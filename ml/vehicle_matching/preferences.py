"""Financial eligibility with transparent weighted soft preferences.

Financial eligibility remains mandatory. User weights affect only feasible cars.
Length bands describe exterior length, not legal classes or interior capacity.
"""
HORIZON = 60
SIZE_BANDS = {'small': (2500, 4200), 'medium': (4200, 4800), 'large': (4800, 6000)}
VARIABLE_SEATING_MODELS = ('스타리아', '카니발', 'GV80', '렉스턴', 'EV9', '팰리세이드', '싼타페', '쏘렌토')


def assumes_standard_seating(vehicle):
    """User-approved catalog assumption; never overwrite verified capacities."""
    return (vehicle.seats is None and not vehicle.seat_options
            and not any(name in vehicle.model for name in VARIABLE_SEATING_MODELS))


def exclusions(profile, vehicle):
    result = []
    if profile.minimum_seats:
        options = tuple(sorted(set(tuple(vehicle.seat_options) + ((vehicle.seats,) if vehicle.seats is not None else ()))))
        if vehicle.seats is not None and vehicle.seats >= profile.minimum_seats:
            pass
        elif not options and assumes_standard_seating(vehicle) and profile.minimum_seats <= 4:
            pass
        elif not options or (vehicle.seats is not None and profile.minimum_seats <= max(options)) or min(options) < profile.minimum_seats <= max(options):
            result.append('seats-unverified')
        elif max(options) < profile.minimum_seats:
            result.append('insufficient-seats')
    if profile.preferred_size != 'any' and vehicle.length_mm is None:
        result.append('length-unverified')
    return result


def integrated_score(profile, vehicle, cost, ml_score):
    # Purchase price already includes principal: add only interest, not installments again.
    balance, interest = cost['principal'], 0.0
    for _ in range(min(cost.get('financing_months', profile.months), HORIZON)):
        charge = balance * cost.get('financing_annual_rate', profile.annual_rate) / 12
        interest += charge
        balance = max(0, balance - (cost['monthly_payment'] - charge))
    total = cost['total_purchase_cost'] + cost['monthly_running_cost'] * HORIZON + interest
    available = profile.monthly_income - profile.monthly_expenses - profile.existing_monthly_payment - profile.monthly_savings
    budget = max(1, available * HORIZON + profile.liquid_assets - profile.emergency_reserve)
    economy = max(0.0, min(1.0, 1 - total / budget))
    monthly_capacity=max(0,available-profile.minimum_buffer)
    burden=cost['monthly_running_cost']/max(1,monthly_capacity)
    # A continuous scoring penalty, not another eligibility threshold.
    monthly_score=100*(1-min(1,burden)**2)
    purchase_score=100*max(0,min(1,1-cost['total_purchase_cost']/max(1,profile.liquid_assets-profile.emergency_reserve)))
    if profile.financing_mode=='recommendation':
        # Cost importance is shared equally by purchase economy and recurring
        # affordability. Future salary never increases the purchase cash limit.
        economy=(purchase_score+monthly_score)/200
    components = [{'key': 'cost', 'score': economy * 100, 'weight': profile.cost_importance},
                  {'key': 'model', 'score': ml_score * 100, 'weight': 1}]
    if profile.preferred_size != 'any':
        lower, upper = SIZE_BANDS[profile.preferred_size]
        distance = max(lower - vehicle.length_mm, vehicle.length_mm - upper, 0) if vehicle.length_mm is not None else None
        size = max(0, 1 - distance / 1000) if distance is not None else .5
        components.append({'key': 'space', 'score': size * 100, 'weight': profile.space_importance,
                           'verified': vehicle.length_mm is not None})
    if profile.preferred_fuel:
        fuel = 'HYBRID' if vehicle.original_fuel == 'PHEV' else vehicle.fuel
        components.append({'key':'fuel','score':100 * (fuel == profile.preferred_fuel), 'weight':profile.fuel_importance})
    if profile.minimum_seats:
        capacity = vehicle.seats if vehicle.seats is not None else min(vehicle.seat_options) if vehicle.seat_options else None
        seats = min(1,capacity/profile.minimum_seats) if capacity is not None else .5
        components.append({'key':'seating','score':100*seats,'weight':profile.seating_importance,'verified':capacity is not None})
    target = {'commute':4100,'family':4750,'leisure':4900,'business':4600}[profile.purpose]
    purpose = max(0,1-abs(vehicle.length_mm-target)/1500) if vehicle.length_mm is not None else .5
    components.append({'key':'purpose','score':100*purpose,'weight':profile.purpose_importance})
    weight_sum = sum(item['weight'] for item in components)
    for item in components:
        item['contribution'] = item['score'] * item['weight'] / weight_sum
    return {'total': sum(item['contribution'] for item in components), 'components': components,
            'ownershipMonths': HORIZON, 'estimatedOwnershipCost': round(total, 2),
            'monthlyAffordability':{'availableMonthly':round(available,2),'protectedMonthlyBuffer':profile.minimum_buffer,
                                    'spendableMonthly':round(monthly_capacity,2),'runningCostRatio':round(burden,6),
                                    'score':round(monthly_score,6),'purchaseEconomyScore':round(purchase_score,6),
                                    'costMix':{'purchase':.5,'monthly':.5}},
            'policy': 'cash-monthly-affordability-v5', 'spaceEvaluated': profile.preferred_size != 'any' and vehicle.length_mm is not None}
