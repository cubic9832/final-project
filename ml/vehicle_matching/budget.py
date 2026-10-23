"""Prioritize the upper 80-100% of currently spendable cash, without borrowing."""
import math

def recommendation_budget(profile, vehicles, costs):
    funds=max(0,profile.liquid_assets-profile.emergency_reserve)
    monthly=max(0,profile.monthly_income-profile.monthly_expenses-profile.existing_monthly_payment
                -profile.monthly_savings-profile.minimum_buffer)
    financial_upper=math.floor(funds)
    if profile.purchase_price_ceiling:
        financial_upper=min(financial_upper,math.floor(profile.purchase_price_ceiling))
    catalog_upper=max((v.price for v in vehicles),default=financial_upper)
    upper=min(financial_upper,catalog_upper)
    return {'policy':'cash-weighted-budget-v3','lower':math.ceil(upper*.8),'upper':math.floor(upper),
            'financialUpper':financial_upper,'availablePurchaseFunds':round(funds),'monthlyVehicleBudget':round(monthly),
            'referenceMonthlyRunningCost':None,'lowerRatio':.8,'catalogCapped':catalog_upper<financial_upper}


def apply_budget_preference(score, vehicle, band):
    """Treat the preferred price band as a weight, never a priority gate."""
    fit = min(1, vehicle.price / max(1, band['lower'])) * 100
    components = [dict(item) for item in score['components']]
    components.append({'key': 'budget', 'score': fit, 'weight': 2})
    total_weight = sum(item['weight'] for item in components)
    for item in components:
        item['contribution'] = item['score'] * item['weight'] / total_weight
    return {**score, 'components': components,
            'total': sum(item['contribution'] for item in components),
            'policy': 'cash-weighted-budget-v6'}


def budget_order(vehicle, score, band):
    return (-score, not band['lower'] <= vehicle.price <= band['upper'], -vehicle.price, vehicle.id)
