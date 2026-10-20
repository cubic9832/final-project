"""Shared train/serve features. Vehicle identity is deliberately excluded."""
import numpy as np

from vehicle_matching.catalog import FUELS
from vehicle_matching.finance import PURPOSES, Assumptions, assess

FEATURE_NAMES = ('log_income', 'expenses_share', 'existing_payment_share', 'savings_share',
                 'cash_income_months', 'down_payment_share', 'log_price', 'price_income_years',
                 'monthly_cost_share', 'stress_cost_share', 'buffer_share', 'running_cost_share',
                 'annual_distance_30000', 'months_72', 'rate', 'unknown_efficiency', 'fuel_match',
                 *('purpose_' + p for p in PURPOSES), *('fuel_' + f for f in FUELS))


def encode(profile, vehicle, assumptions=Assumptions()):
    cost = assess(profile, vehicle, assumptions)
    if not cost['eligible']:
        raise ValueError('Only eligible pairs may be scored')
    income = max(1, profile.monthly_income)
    match = float(vehicle.fuel == profile.preferred_fuel) if profile.preferred_fuel else 0.5
    return np.asarray([np.log1p(income), profile.monthly_expenses / income,
                       profile.existing_monthly_payment / income, profile.monthly_savings / income,
                       profile.liquid_assets / income, profile.down_payment / vehicle.price,
                       np.log1p(vehicle.price), vehicle.price / (income * 12),
                       cost['monthly_total'] / income, cost['stress_monthly_total'] / income,
                       cost['stress_remaining_monthly'] / income, cost['monthly_running_cost'] / income,
                       profile.annual_distance / 30000, profile.months / 72, profile.annual_rate,
                       float(cost['efficiency_estimated']), match,
                       *(float(profile.purpose == p) for p in PURPOSES),
                       *(float(vehicle.fuel == f) for f in FUELS)], dtype=np.float32)


def utility(profile, vehicle, assumptions=Assumptions(), preference_weight=0.25):
    """Explicit synthetic teacher, NOT an observed satisfaction/purchase probability.

    Positive labels mean better stress buffer, lower running cost and matching fuel.
    Purpose changes the cost tradeoff only; no unsupported safety/space claims.
    """
    cost = assess(profile, vehicle, assumptions)
    if not cost['eligible']:
        return 0.0
    income = max(1, profile.monthly_income)
    buffer = np.clip(cost['stress_remaining_monthly'] / income, 0, 1)
    economy = np.clip(1 - cost['monthly_running_cost'] / income, 0, 1)
    match = float(vehicle.fuel == profile.preferred_fuel) if profile.preferred_fuel else 0.5
    running_weight = 0.4 if profile.purpose in ('commute', 'business') else 0.2
    return float((1 - preference_weight) * ((1 - running_weight) * buffer + running_weight * economy)
                 + preference_weight * match)
