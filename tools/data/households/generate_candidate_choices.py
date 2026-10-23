"""Generate preference-first synthetic choices; never observed purchase labels."""
import argparse
import csv
import hashlib
import json
import math
import random
import sys
from collections import Counter
from dataclasses import asdict, fields, replace
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / 'ml'))

from vehicle_matching.catalog import load_csv, save_catalog
from vehicle_matching.catalog_merge import expand_catalog
from vehicle_matching.dataset import profiles
from vehicle_matching.finance import Profile, assess
from vehicle_matching.preferences import exclusions, integrated_score
from vehicle_matching.seating import apply_seating_registry

VERSION = 'preference-first-choice-v3'
TEMPERATURE = 0.055
REPEATS = 4

CSV_FIELDS = {
    'choice_id': '선택사례번호', 'financial_group_id': '재무조건그룹번호',
    'preference_group_id': '재무선호그룹번호', 'split': '데이터구분',
    'monthly_income': '월소득_원', 'monthly_expenses': '월생활지출_원',
    'existing_monthly_payment': '기존대출월상환액_원', 'liquid_assets': '유동자산_원',
    'emergency_reserve': '비상자금_원', 'monthly_savings': '월저축액_원',
    'annual_distance': '연간주행거리_km', 'minimum_buffer': '최소월여유자금_원',
    'purpose': '차량용도', 'preferred_fuel': '선호연료',
    'down_payment': '구매투입가능자금_원', 'months': '가정할부기간_개월',
    'annual_rate': '가정연금리_퍼센트', 'selected_price': '선택차량가격_원',
    'maximum_price': '구매가격상한_원_0이면미지정',
    'monthly_budget': '월차량비용한도_원',
    'selected_upfront': '선택차량초기지급액_원', 'selected_payment': '선택차량월할부금_원',
    'selected_running': '선택차량월유지비_원', 'selected_remaining': '선택후월잔여액_원',
    'no_choice_reason': '선택없음사유',
    'cost_importance': '가성비중요도_1부터5', 'space_importance': '공간중요도_1부터5',
    'minimum_seats': '최소탑승인원_명', 'preferred_size': '선호크기',
    'existing_debt_balance_won': '가상기존부채잔액_원', 'selected_vehicle_id': '선택차량번호',
    'selected_brand': '선택브랜드', 'selected_model': '선택차량모델', 'selected_trim': '선택트림',
    'eligible_model_count': '선택가능모델수', 'choice_probability': '선택확률_만분율',
    'selected_utility': '선택차량점수_100점', 'best_utility': '최고후보점수_100점',
    'label_origin': '생성규칙버전',
}
VALUE_LABELS = {
    'train': '학습', 'validation': '검증', 'test': '새재무상황평가',
    'combination_test': '새선호조합평가', 'commute': '출퇴근', 'family': '가족이동',
    'leisure': '여가', 'business': '업무', 'small': '작음', 'medium': '중간', 'large': '큼',
    'GASOLINE': '가솔린', 'HYBRID': '하이브리드', 'DIESEL': '디젤', 'LPG': 'LPG', 'ELECTRIC': '전기',
}


def korean_row(row):
    result = {}
    for key, label in CSV_FIELDS.items():
        value = row[key]
        if value is None:
            value = '미지정' if key == 'preferred_fuel' else ''
        elif isinstance(value, bool):
            value = '가능' if value else '불가능'
        elif key == 'choice_probability':
            value = round(value * 10000)
        elif key == 'annual_rate':
            value = round(value * 100)
        elif key in ('selected_utility', 'best_utility'):
            value = round(value * 100)
        elif isinstance(value, (int, float)):
            value = round(value)
        else:
            value = VALUE_LABELS.get(value, value)
        result[label] = value
    return result


def consistent_preferences(person, rng):
    purpose = rng.choice(('commute', 'family', 'leisure', 'business'))
    seats = rng.choice((4, 5, 6)) if purpose == 'family' else rng.choice((1, 2, 4))
    size = rng.choice(('medium', 'large')) if seats == 5 else 'large' if seats >= 6 else rng.choice(('small', 'medium', 'large'))
    fuel = rng.choice(('GASOLINE', 'HYBRID', 'DIESEL', 'LPG', 'ELECTRIC', None))
    return replace(person, purpose=purpose, minimum_seats=seats, preferred_size=size,
                   preferred_fuel=fuel, cost_importance=rng.randint(1, 5), space_importance=rng.randint(1, 5))


def purchase_assessment(profile, vehicle):
    # Local synthetic financing scenario. Charging environment is deliberately unused.
    scenario = replace(profile, financing_mode='fixed', charging_available=True,
                       down_payment=min(profile.down_payment, vehicle.price))
    cost = assess(scenario, vehicle)
    # Size is a soft preference; unknown length must not exclude a candidate.
    seat_errors = exclusions(replace(scenario, preferred_size='any'), vehicle)
    return scenario, cost, seat_errors


def load_candidates():
    vehicles, _ = expand_catalog(load_csv()[0])
    for name in ('candidate-space-evidence.json', 'candidate-seating-evidence.json'):
        lookup = {(r['brand'], r['model']): r for r in json.loads(
            (ROOT / 'data/vehicles' / name).read_text(encoding='utf-8'))['vehicles']}
        vehicles = [replace(v, length_mm=v.length_mm or lookup.get((v.brand, v.model), {}).get('length_mm'))
                    for v in vehicles]
    return apply_seating_registry(vehicles)


def preference_key(profile):
    return (profile.cost_importance, profile.preferred_size, profile.purpose)


def is_combination_holdout(profile):
    cost, size, purpose = preference_key(profile)
    return (cost + ('small', 'medium', 'large').index(size)
            + ('commute', 'family', 'leisure', 'business').index(purpose)) % 5 == 0


def choice_distribution(profile, vehicles, maximum_price=0):
    """One option per model prevents models with many trims gaining label mass."""
    best = {}
    for vehicle in vehicles:
        scenario, cost, seat_errors = purchase_assessment(profile, vehicle)
        if not cost['eligible'] or seat_errors or (maximum_price and vehicle.price > maximum_price):
            continue
        # Neutral model component: no learned weights or choice-derived inputs.
        score = integrated_score(scenario, vehicle, cost, 0.5)['total'] / 100
        # Explicit synthetic purpose assumption, using only known exterior length.
        target = {'commute': 4100, 'family': 4750, 'leisure': 4900, 'business': 4600}[profile.purpose]
        purpose_match = max(0, 1 - abs(vehicle.length_mm - target) / 1500) if vehicle.length_mm else 0
        fuel_match = float(vehicle.fuel == profile.preferred_fuel) if profile.preferred_fuel else 0.5
        score = 0.8 * score + 0.12 * purpose_match + 0.08 * fuel_match
        key = (vehicle.brand, vehicle.model)
        if key not in best or score > best[key][1]:
            best[key] = (vehicle, score)
    options = sorted(best.values(), key=lambda item: item[0].id)
    if not options:
        return []
    maximum = max(score for _, score in options)
    weights = [math.exp((score - maximum) / TEMPERATURE) for _, score in options]
    total = sum(weights)
    return [(vehicle, score, weight / total) for (vehicle, score), weight in zip(options, weights)]


def generate(groups, seed, vehicles):
    if groups < 10:
        raise ValueError('At least 10 financial groups required')
    preference_rng, choice_rng = random.Random(seed + 1), random.Random(seed + 2)
    finance_rng = random.Random(seed + 3)
    # Complete all financial and preference inputs before assigning any choice.
    inputs = []
    for index, person in enumerate(profiles(groups, seed)):
        # Round inputs before eligibility and scoring, so exported inputs reproduce decisions.
        person = replace(person, **{field.name: round(getattr(person, field.name))
                                   for field in fields(Profile) if isinstance(getattr(person, field.name), float)})
        person = replace(person, down_payment=round((person.liquid_assets - person.emergency_reserve)
                                                   * finance_rng.uniform(0.3, 1)),
                         months=60, annual_rate=0.06, financing_mode='fixed')
        debt_balance = round(person.existing_monthly_payment * finance_rng.randint(12, 120))
        for variant in range(3):
            person_variant = consistent_preferences(person, preference_rng)
            maximum_price = preference_rng.choice((0, 0, 20000000, 30000000, 50000000, 80000000))
            split = ('train' if index % 10 < 7 else 'validation' if index % 10 == 7 else 'test')
            if is_combination_holdout(person_variant):
                if split != 'test':
                    continue
                split = 'combination_test'
            inputs.append((f'F-{index:06}', variant, split, person_variant, maximum_price, debt_balance))
    rows = []
    for group, variant, split, person, maximum_price, debt_balance in inputs:
        options = choice_distribution(person, vehicles, maximum_price)
        for repetition in range(REPEATS):
            selected = choice_rng.choices(options, weights=[x[2] for x in options])[0] if options else None
            vehicle, score, probability = selected if selected else (None, None, None)
            scenario, cost, _ = purchase_assessment(person, vehicle) if vehicle else (None, None, None)
            rows.append({'choice_id': f'{group}-P{variant}-R{repetition}', 'financial_group_id': group,
                         'preference_group_id': f'{group}-P{variant}', 'split': split,
                         **asdict(person), 'existing_debt_balance_won': debt_balance,
                         'maximum_price': maximum_price,
                         'monthly_budget': person.monthly_income - person.monthly_expenses - person.existing_monthly_payment - person.monthly_savings - person.minimum_buffer,
                         'selected_upfront': round(scenario.down_payment) if scenario else None,
                         'selected_price': round(vehicle.price) if vehicle else None,
                         'selected_payment': math.ceil(cost['monthly_payment']) if cost else None,
                         'selected_running': math.ceil(cost['monthly_running_cost']) if cost else None,
                         'selected_remaining': person.monthly_income - person.monthly_expenses - person.existing_monthly_payment - person.monthly_savings - math.ceil(cost['monthly_payment']) - math.ceil(cost['monthly_running_cost']) if cost else None,
                         'no_choice_reason': '' if options else '월예산부족_또는_정원가격조건충족후보없음',
                         'selected_vehicle_id': vehicle.id if vehicle else '',
                         'selected_brand': vehicle.brand if vehicle else '',
                         'selected_model': vehicle.model if vehicle else '',
                         'selected_trim': vehicle.trim if vehicle else '',
                         'eligible_model_count': len(options), 'choice_probability': probability,
                         'selected_utility': score, 'best_utility': max(x[1] for x in options) if options else None,
                         'label_origin': VERSION})
    return rows


def validate(rows, vehicles):
    lookup = {v.id: v for v in vehicles}
    groups, combinations, choices = {}, {}, {}
    for row in rows:
        if ((row['minimum_seats'] >= 6 and row['preferred_size'] != 'large')
                or (row['minimum_seats'] == 5 and row['preferred_size'] == 'small')):
            raise AssertionError('Conflicting input preferences')
        groups.setdefault(row['financial_group_id'], set()).add(
            'test' if row['split'] == 'combination_test' else row['split'])
        combinations.setdefault(row['split'], set()).add(tuple(row[k] for k in
            ('cost_importance', 'preferred_size', 'purpose')))
        choices.setdefault(row['preference_group_id'], set()).add(row['selected_model'])
        if row['selected_vehicle_id']:
            profile = Profile(**{field.name: row[field.name] for field in fields(Profile)})
            vehicle = lookup[row['selected_vehicle_id']]
            _, cost, seat_errors = purchase_assessment(profile, vehicle)
            if (not cost['eligible'] or seat_errors
                    or (row['maximum_price'] and vehicle.price > row['maximum_price'])
                    or row['selected_remaining'] < profile.minimum_buffer):
                raise AssertionError('Ineligible synthetic choice')
    assert all(len(splits) == 1 for splits in groups.values()), 'Financial group leakage'
    assert not (combinations.get('train', set()) | combinations.get('validation', set())) & combinations.get('combination_test', set()), 'Combination leakage'
    return {'rows': len(rows), 'split_counts': dict(Counter(r['split'] for r in rows)),
            'financial_groups': len(groups), 'same_inputs_multiple_models': sum(len(s - {''}) > 1 for s in choices.values()),
            'no_choice_rows': sum(not r['selected_vehicle_id'] for r in rows),
            'selected_models': dict(Counter(r['selected_model'] for r in rows if r['selected_model'])),
            'eligibility_violations': 0, 'preference_conflicts': 0, 'financial_group_overlap': 0, 'heldout_combination_overlap': 0,
            'mean_synthetic_utility_regret': sum((r['best_utility'] - r['selected_utility'])
                for r in rows if r['selected_vehicle_id']) / max(1, sum(bool(r['selected_vehicle_id']) for r in rows))}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--groups', type=int, default=1000)
    parser.add_argument('--seed', type=int, default=20261021)
    parser.add_argument('--output', type=Path, default=ROOT / 'data/households/synthetic/candidate-choices-v3')
    args = parser.parse_args()
    vehicles = load_candidates()
    rows = generate(args.groups, args.seed, vehicles)
    report = validate(rows, vehicles)
    args.output.mkdir(parents=True, exist_ok=True)
    save_catalog(args.output / 'catalog.json', vehicles)
    with (args.output / 'choices.csv').open('w', encoding='utf-8-sig', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=list(CSV_FIELDS.values()))
        writer.writeheader()
        writer.writerows(korean_row(row) for row in rows)
    example_fields = ['재무조건그룹번호', '재무선호그룹번호', '월소득_원', '월생활지출_원',
                      '유동자산_원', '가성비중요도_1부터5', '선호크기', '선호연료', '차량용도',
                      '최소탑승인원_명', '구매가격상한_원_0이면미지정', '선택차량모델',
                      '선택차량가격_원', '선택차량월할부금_원', '선택차량월유지비_원']
    example_groups = list(dict.fromkeys(row['financial_group_id'] for row in rows
                                       if row['selected_vehicle_id']))[:5]
    with (args.output / 'examples.csv').open('w', encoding='utf-8-sig', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=example_fields)
        writer.writeheader()
        writer.writerows({key: korean_row(row)[key] for key in example_fields}
                         for row in rows if row['financial_group_id'] in example_groups)
    config = {'version': VERSION, 'seed': args.seed, 'financial_groups': args.groups,
              'repeats': REPEATS, 'temperature': TEMPERATURE, 'catalog_candidates': len(vehicles),
              'catalog_models': len({(v.brand, v.model) for v in vehicles}),
              'debt_balance_assumption': 'monthly existing payment times independent 12..120 months; descriptive only',
              'financing_assumptions': {'months': 60, 'annual_rate_percent': 6, 'additional_acquisition_cost': 0},
              'csv_fields': CSV_FIELDS, 'csv_values': VALUE_LABELS,
              'csv_probability_scale': 10000, 'csv_score_scale': 100,
              'choice_rules': 'Hard: seats, explicit price ceiling, monthly payment plus running costs and buffer. Soft: size, fuel, purpose, economy. Charging ignored.',
              'catalog_sha256': hashlib.sha256((args.output / 'catalog.json').read_bytes()).hexdigest()}
    for name, payload in [('generation_config.json', config), ('validation_report.json', report)]:
        (args.output / name).write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps({k: v for k, v in report.items() if k != 'selected_models'}, ensure_ascii=False))


if __name__ == '__main__':
    main()
