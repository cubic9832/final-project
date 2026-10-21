"""Transparent reranking policy. Existing ML features/weights are not retrained.

Financial eligibility remains mandatory. User weights affect only feasible cars.
Length bands describe exterior length, not legal classes or interior capacity.
"""
HORIZON = 60
SIZE_BANDS = {'small': (2500, 4200), 'medium': (4200, 4800), 'large': (4800, 6000)}


def exclusions(profile, vehicle):
    result = []
    if profile.minimum_seats:
        if vehicle.seats is None:
            result.append('seats-unverified')
        elif vehicle.seats < profile.minimum_seats:
            result.append('insufficient-seats')
    if profile.preferred_size != 'any' and vehicle.length_mm is None:
        result.append('length-unverified')
    return result


def integrated_score(profile, vehicle, cost, ml_score):
    # Purchase price already includes principal: add only interest, not installments again.
    balance, interest = cost['principal'], 0.0
    for _ in range(min(profile.months, HORIZON)):
        charge = balance * profile.annual_rate / 12
        interest += charge
        balance = max(0, balance - (cost['monthly_payment'] - charge))
    total = cost['total_purchase_cost'] + cost['monthly_running_cost'] * HORIZON + interest
    available = profile.monthly_income - profile.monthly_expenses - profile.existing_monthly_payment - profile.monthly_savings
    budget = max(1, available * HORIZON + profile.liquid_assets - profile.emergency_reserve)
    economy = max(0.0, min(1.0, 1 - total / budget))
    components = [{'key': 'cost', 'score': economy * 100, 'weight': profile.cost_importance},
                  {'key': 'model', 'score': ml_score * 100, 'weight': 1}]
    if profile.preferred_size != 'any':
        if vehicle.length_mm is None:
            raise ValueError('Cannot score unknown vehicle length')
        lower, upper = SIZE_BANDS[profile.preferred_size]
        distance = max(lower - vehicle.length_mm, vehicle.length_mm - upper, 0)
        size = max(0, 1 - distance / 1000)
        components.append({'key': 'space', 'score': size * 100, 'weight': profile.space_importance})
    weight_sum = sum(item['weight'] for item in components)
    for item in components:
        item['contribution'] = item['score'] * item['weight'] / weight_sum
    return {'total': sum(item['contribution'] for item in components), 'components': components,
            'ownershipMonths': HORIZON, 'estimatedOwnershipCost': round(total, 2),
            'policy': 'weighted-preferences-v1', 'spaceEvaluated': profile.preferred_size != 'any'}
