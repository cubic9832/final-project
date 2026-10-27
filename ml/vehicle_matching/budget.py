"""Importance-specific purchase band; monthly affordability stays mandatory."""
import math


def lower_percent(cost_importance):
    # UI uses 1/3/5; API values 2 and 4 share the adjacent low/high groups.
    return 80 if cost_importance <= 2 else 70 if cost_importance == 3 else 60


def recommendation_budget(profile, vehicles, costs):
    funds = max(0, profile.liquid_assets - profile.emergency_reserve)
    monthly = max(0, profile.monthly_income - profile.monthly_expenses - profile.existing_monthly_payment
                  - profile.monthly_savings - profile.minimum_buffer)
    upper = math.floor(funds)
    if profile.purchase_price_ceiling:
        upper = min(upper, math.floor(profile.purchase_price_ceiling))
    percent = lower_percent(profile.cost_importance)
    # Integer arithmetic rounds up to the first allowed won without float drift.
    lower = (upper * percent + 99) // 100
    return {'policy': 'cash-importance-band-v1', 'lower': lower, 'upper': upper,
            'financialUpper': upper, 'availablePurchaseFunds': round(funds), 'monthlyVehicleBudget': round(monthly),
            'referenceMonthlyRunningCost': None, 'lowerRatio': percent / 100,
            'costImportance': profile.cost_importance, 'catalogCapped': False}


def apply_budget_preference(score, vehicle, band):
    """Compatibility helper; the price band is an eligibility filter, not a bonus."""
    return {**score, 'policy': 'cash-importance-band-v1'}


def budget_order(vehicle, score, band):
    return (-score, vehicle.id)
