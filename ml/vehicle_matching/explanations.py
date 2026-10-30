"""Read-only decision evidence. Never changes candidate eligibility or ranking."""
from vehicle_matching.body_types import matches_body_preference
import math

from vehicle_matching.preferences import SIZE_BANDS
from vehicle_matching.recommendation_policy import POLICY

NEAR_TIE_POINTS = 1.0  # Display rule, not a statistical confidence interval.


def preference_evidence(profile, vehicle, components):
    by_key = {item['key']: item for item in components}
    evidence = []

    def add(key, status, **values):
        component = by_key.get(key, {})
        evidence.append({'key': key, 'status': status,
                         'weight': component.get('weight'),
                         'score': component.get('score'),
                         'contribution': component.get('contribution'), **values})

    if profile.preferred_fuel:
        evaluated = 'HYBRID' if vehicle.original_fuel == 'PHEV' else vehicle.fuel
        add('fuel', 'match' if evaluated == profile.preferred_fuel else 'mismatch',
            requested=profile.preferred_fuel, actual=vehicle.original_fuel or vehicle.fuel,
            evaluatedFuel=evaluated)
    if profile.preferred_body_type != 'any':
        add('body', 'unknown' if vehicle.body_type is None else 'match' if matches_body_preference(profile.preferred_body_type, vehicle.body_type) else 'mismatch',
            requested=profile.preferred_body_type, actual=vehicle.body_type, sourceUrls=list(vehicle.body_source_urls))
    if profile.preferred_size != 'any':
        lower, upper = SIZE_BANDS[profile.preferred_size]
        length = vehicle.length_mm
        delta = max(lower - length, length - upper, 0) if length is not None else None
        add('space', 'unknown' if length is None else 'match' if delta == 0 else 'mismatch',
            requested=profile.preferred_size, lowerMm=lower, upperMm=upper,
            actualMm=length, differenceMm=delta,
            direction=None if length is None else 'shorter' if length < lower else 'longer' if length > upper else 'within')
    if profile.minimum_seats:
        capacity = vehicle.seats if vehicle.seats is not None else min(vehicle.seat_options) if vehicle.seat_options else None
        add('seating', 'unknown' if vehicle.seats is None or vehicle.seats_status == 'official-reference-conflict' else 'match' if capacity >= profile.minimum_seats else 'mismatch',
            requested=profile.minimum_seats, actual=capacity,
            difference=None if capacity is None else max(0, profile.minimum_seats - capacity),
            dataStatus=vehicle.seats_status, seatOptions=list(vehicle.seat_options))
    return evidence


def candidate_evidence(profile, vehicle, cost, score):
    available = profile.monthly_income - profile.monthly_expenses - profile.existing_monthly_payment - profile.monthly_savings
    funds = profile.liquid_assets - profile.emergency_reserve
    return {
        'vehicleId': vehicle.id,
        'preferences': preference_evidence(profile, vehicle, score['components']),
        'financial': {
            'eligible': cost['eligible'], 'purchaseFunds': funds,
            'purchaseCost': cost['total_purchase_cost'],
            'cashAfterPurchase': round(funds - cost['total_purchase_cost'], 2),
            'monthlyAvailable': available, 'monthlyRunningCost': cost['monthly_running_cost'],
            'remainingMonthly': cost['remaining_monthly'],
            'fundingSource': cost.get('funding_source', 'income'),
            'monthlyAssetDrawdown': cost.get('monthly_asset_drawdown', 0),
            'assetRunwayMonths': cost.get('asset_runway_months'),
            'requiredAssetCoverageMonths': cost.get('required_asset_coverage_months'),
            'minimumMonthlyBuffer': profile.minimum_buffer,
            'financing': 'cash-only', 'includesAcquisitionFees': False,
        },
    }


def evaluation_summary(profile, catalog, eligible, costs, combined):
    matches = unknown = 0
    keys = []
    if profile.preferred_body_type != 'any':
        keys.append('body')
    if profile.preferred_fuel:
        keys.append('fuel')
    if profile.preferred_size != 'any':
        keys.append('space')
    if profile.minimum_seats:
        keys.append('seating')
    for vehicle in eligible:
        score = combined.get(vehicle.id)
        # This explicitly prevents a partial ranking evaluation from being
        # presented as an exhaustive catalog assessment.
        if score is None:
            continue
        items = [item for item in preference_evidence(profile, vehicle, score['components']) if item['key'] in keys]
        if any(item['status'] == 'mismatch' for item in items):
            continue
        if any(item['status'] == 'unknown' for item in items):
            unknown += 1
        elif keys:
            matches += 1
    return {
        'scope': 'loaded-catalog-financially-eligible-configurations',
        'catalogFinanciallyChecked': len(catalog),
        'financiallyEligibleConfigurations': len(eligible),
        'preferenceEvaluatedConfigurations': len(combined),
        'complete': len(combined) == len(eligible),
        'specifiedPreferenceKeys': keys,
        'confirmedMatchingConfigurations': matches,
        'unresolvedConfigurations': unknown,
        'purposeAssessment': 'not-evaluated',
    }


def ranking_comparison(higher, lower):
    if higher.get('rankingPolicy') == POLICY:
        return {'status':'preference-priority','higherVehicleId':higher['vehicle']['id'], 'lowerVehicleId':lower['vehicle']['id'], 'scoreDifference':higher['rankingScore']-lower['rankingScore'], 'featureAttributionAvailable':False}
    if higher.get('rankingScoreType') == lower.get('rankingScoreType') == 'ml-raw':
        gap = higher['rankingScore'] - lower['rankingScore']
        return {'higherVehicleId': higher['vehicle']['id'], 'lowerVehicleId': lower['vehicle']['id'],
                'status': 'ml-ranked' if math.isfinite(gap) and gap >= 0 else 'unavailable',
                'scoreType': 'ml-raw', 'scoreDifference': gap,
                'featureAttributionAvailable': False}
    result = {'higherVehicleId': higher['vehicle']['id'], 'lowerVehicleId': lower['vehicle']['id'],
              'nearTieThreshold': NEAR_TIE_POINTS, 'status': 'unavailable'}
    try:
        high, low = higher['integratedScore'], lower['integratedScore']
        a = {item['key']: item for item in high['components']}
        b = {item['key']: item for item in low['components']}
        if set(a) != set(b) or any(a[key]['weight'] != b[key]['weight'] for key in a):
            return result
        for score in (high, low):
            contributions = [item['contribution'] for item in score['components']]
            if not all(math.isfinite(value) for value in contributions):
                return result
            if not math.isclose(sum(contributions), score['total'], abs_tol=1e-6):
                return result
        gap = high['total'] - low['total']
        result.update(scoreDifference=gap, status='near-tie' if abs(gap) < NEAR_TIE_POINTS else 'explained')
        if gap < -1e-6:
            return {**result, 'status': 'unavailable'}
        deltas = [{'key': key, 'weight': a[key]['weight'],
                   'difference': a[key]['contribution'] - b[key]['contribution']} for key in a]
        result['contributionDifferences'] = sorted(deltas, key=lambda item: -item['difference'])
        return result
    except (KeyError, TypeError, ValueError):
        return result
