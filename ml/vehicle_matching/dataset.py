"""Reproducible independent financial profiles; no assigned vehicle label.

These are experimental distributions, not population/market estimates. Profile IDs
and vehicle-model partitions are disjoint across development and evaluation.
"""
import random

from vehicle_matching.catalog import FUELS
from vehicle_matching.features import encode, utility
from vehicle_matching.finance import PURPOSES, Profile, assess


def profiles(count, seed):
    rng = random.Random(seed)
    result = []
    for _ in range(count):
        income = rng.uniform(1500000, 12000000)
        cash = rng.uniform(0, income * 30)
        reserve = cash * rng.uniform(0.05, 0.5)
        result.append(Profile(monthly_income=income, monthly_expenses=income * rng.uniform(0.2, 0.8),
                              existing_monthly_payment=income * rng.uniform(0, 0.25), liquid_assets=cash,
                              down_payment=0, emergency_reserve=reserve,
                              monthly_savings=income * rng.uniform(0, 0.25), annual_distance=rng.uniform(3000, 40000),
                              months=0, annual_rate=0, financing_mode='recommendation',
                              minimum_buffer=income * rng.uniform(0, 0.1), purpose=rng.choice(PURPOSES),
                              preferred_fuel=rng.choice((*FUELS, None)), charging_available=rng.choice((True, False))))
    return result


def pair_data(people, vehicles, seed=42):
    rng = random.Random(seed)
    features, targets, pairs = [], [], []
    for person in people:
        eligible = [v for v in vehicles if assess(person, v)['eligible']]
        chosen = rng.sample(eligible, min(24, len(eligible)))
        start = len(features)
        for vehicle in chosen:
            features.append(encode(person, vehicle))
            targets.append(utility(person, vehicle))
        for _ in range(min(32, len(chosen) * 2)):
            if len(chosen) < 2:
                break
            a, b = rng.sample(range(start, len(features)), 2)
            if abs(targets[a] - targets[b]) < 0.01:
                continue
            pairs.append((a, b) if targets[a] > targets[b] else (b, a))
    return features, targets, pairs
