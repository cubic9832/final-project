"""Cash ceiling metadata. A higher price is never a ranking advantage."""
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
    return {'policy':'cash-ceiling-only-v8','lower':0,'upper':math.floor(upper),
            'financialUpper':financial_upper,'availablePurchaseFunds':round(funds),'monthlyVehicleBudget':round(monthly),
            'referenceMonthlyRunningCost':None,'lowerRatio':0,'catalogCapped':catalog_upper<financial_upper}


def apply_budget_preference(score, vehicle, band):
    """Compatibility entry point: no separate price-band contribution."""
    return {**score, 'policy': 'cash-preference-weighted-v8'}


def budget_order(vehicle, score, band):
    return (-score, vehicle.id)
