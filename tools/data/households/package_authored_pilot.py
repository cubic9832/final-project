"""Package individually authored personas and decisions; never generate choice labels."""
import csv
from dataclasses import asdict
import hashlib
import json
from pathlib import Path

import numpy as np

from vehicle_matching.catalog import read_catalog
from vehicle_matching.finance import Profile, assess
from vehicle_matching.preference_model import FEATURE_NAMES, encode_preference
from vehicle_matching.recommendation_policy import seating_status

ROOT = Path(__file__).resolve().parents[3]
OUTPUT = ROOT / 'data/households/synthetic/authored-pilot-v1-20261029'
SOURCE = ROOT / 'data/households/synthetic/behavioral-million-20261028/catalog.json'
PRIORITIES = ('cost', 'space', 'performance', 'ride_comfort', 'quietness', 'design', 'brand', 'technology')


def write_json(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + '\n', encoding='utf-8')


def write_csv(path, rows):
    with path.open('w', encoding='utf-8-sig', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def main():
    catalog = read_catalog(SOURCE)
    users, choices, assessments, selected = [], [], [], {}
    arrays = {role: {'features': [], 'comparisons': [], 'labels': [], 'profile_ids': [], 'vehicle_indices': []}
              for role in ('train', 'validation', 'test')}
    review = ['# 개별 작성 사용자 30명 · 비교 선택 150건', '',
              '금액은 원입니다. 모든 선택과 이유는 personas.txt에 개별 작성되어 있으며 포장 코드는 선택을 계산하지 않습니다.', '']
    lines = [line for line in (OUTPUT / 'personas.txt').read_text(encoding='utf-8').splitlines()
             if line and not line.startswith('#')]
    for number, line in enumerate(lines):
        name, story, money, context, tastes, weights, models, reasons = line.split('|')
        income, expenses, debt, savings, assets, reserve, ceiling = [int(x) * 10000 for x in money.split(',')]
        distance, seats, charging = map(int, context.split(','))
        body, size, fuel = tastes.split(',')
        priorities = dict(zip(PRIORITIES, map(int, weights.split(',')), strict=True))
        assert all(1 <= value <= 5 for value in priorities.values())
        profile = Profile(monthly_income=income, monthly_expenses=expenses, existing_monthly_payment=debt,
                          monthly_savings=savings, liquid_assets=assets, emergency_reserve=reserve,
                          purchase_price_ceiling=ceiling, annual_distance=distance, minimum_seats=seats,
                          charging_available=bool(charging), preferred_body_type=body, preferred_size=size,
                          preferred_fuel=fuel, cost_importance=priorities['cost'], space_importance=priorities['space'],
                          body_importance=5 if number in (1, 6, 9, 10, 18, 19) else 3,
                          fuel_importance=4, seating_importance=5, purpose_importance=3,
                          purpose='family' if seats >= 6 or number in (4, 7) else 'business' if number in (15, 16, 18) else 'leisure' if number in (8, 9, 10, 28) else 'commute',
                          down_payment=0, months=0, annual_rate=0, financing_mode='recommendation', minimum_buffer=200000)
        role = 'train' if number < 20 else 'validation' if number < 25 else 'test'
        user_id = f'AP{number+1:03}'
        user = {'id': user_id, 'group': user_id, 'split': role, 'name': name, 'scenario': story,
                'profile': asdict(profile), 'experience_priorities': priorities,
                'charging_access': 'home_or_work' if charging else 'no_reliable_access'}
        users.append(user)
        candidates = []
        for model in models.split(';'):
            matches = [v for v in catalog if v.model == model and assess(profile, v)['eligible']
                       and seating_status(profile, v) == 'match']
            if not matches:
                raise ValueError(f'{user_id}: no eligible exact model {model}')
            vehicle = min(matches, key=lambda v: (v.price, v.id))
            selected[vehicle.id] = vehicle
            candidates.append(vehicle)
        reason_list = reasons.split(';')
        assert len(candidates) == 6 and len(reason_list) == 5 and len({v.model for v in candidates}) == 6
        review += [f'## {user_id} {name} ({role})', '', story, '',
                   f'- 월 소득 {income:,} / 생활비 {expenses:,} / 상환 {debt:,} / 저축 {savings:,}',
                   f'- 자산 {assets:,} / 비상금 {reserve:,} / 구매상한 {ceiling:,}',
                   f'- 연 {distance:,}km / 필수 {seats}석 / 충전 {bool(charging)} / 선호 {body}, {size}, {fuel}',
                   '- 중요도: ' + ', '.join(f'{key}={value}' for key, value in priorities.items()), '',
                   '| 차량 A | 차량 B | 선택 | 이유 |', '| --- | --- | --- | --- |']
        bucket = arrays[role]
        for offset, (other, reason) in enumerate(zip(candidates[1:], reason_list)):
            winner = candidates[0]
            a, b = (winner, other) if (number + offset) % 2 == 0 else (other, winner)
            label = int(a.id == winner.id)
            choice = {'id': f'{user_id}-C{offset+1}', 'profile_id': user_id, 'split': role,
                      'a': a.id, 'b': b.id, 'label': label, 'reason': reason,
                      'reason_scope': 'authored preference; not measured vehicle performance'}
            choices.append(choice)
            positions = []
            for v in (a, b):
                cost = assess(profile, v)
                positions.append(len(bucket['features']))
                bucket['features'].append(encode_preference(profile, v, cost=cost))
                bucket['profile_ids'].append(user_id)
                bucket['vehicle_indices'].append(next(i for i, c in enumerate(catalog) if c.id == v.id))
                assessments.append({'choice_id': choice['id'], 'vehicle_id': v.id,
                                    'eligible': cost['eligible'], 'seating_status': seating_status(profile, v),
                                    'monthly_running_cost': cost['monthly_running_cost'], 'funding_source': cost['funding_source']})
            bucket['comparisons'].append(positions)
            bucket['labels'].append(label)
            display = lambda v: f'{v.brand} {v.model} {v.trim} ({v.price:,}원)'
            review.append(f'| {display(a)} | {display(b)} | {"A" if label else "B"} | {reason} |')
        review.append('')
    assert len(users) == 30 and len(choices) == 150
    assert len({json.dumps(u['profile'], sort_keys=True) for u in users}) == 30
    assert sum(c['label'] for c in choices) == 75
    for role, bucket in arrays.items():
        features = np.asarray(bucket['features'], dtype=np.float32)
        assert features.shape[1] == len(FEATURE_NAMES) and np.isfinite(features).all()
        np.savez_compressed(OUTPUT / f'{role}_choices.npz', features=features,
                            comparisons=np.asarray(bucket['comparisons'], dtype=np.int64),
                            labels=np.asarray(bucket['labels'], dtype=np.float32),
                            profile_ids=np.asarray(bucket['profile_ids']),
                            vehicle_indices=np.asarray(bucket['vehicle_indices'], dtype=np.int64))
    for filename, records in [('profiles.jsonl', users), ('choices.jsonl', choices)]:
        (OUTPUT / filename).write_text(''.join(json.dumps(row, ensure_ascii=False, allow_nan=False)+'\n' for row in records), encoding='utf-8')
    write_json(OUTPUT / 'catalog.json', [asdict(v) for v in catalog])
    write_csv(OUTPUT / 'profiles.csv', [{'id': u['id'], 'split': u['split'], 'name': u['name'], 'scenario': u['scenario'],
                                       **u['profile'], **{k+'_priority': v for k,v in u['experience_priorities'].items()}} for u in users])
    lookup = {v.id: v for v in catalog}
    write_csv(OUTPUT / 'choices.csv', [{**c, 'a_model': lookup[c['a']].model, 'a_trim': lookup[c['a']].trim,
                                      'b_model': lookup[c['b']].model, 'b_trim': lookup[c['b']].trim} for c in choices])
    write_json(OUTPUT / 'validation_report.json', {'status': 'passed', 'profiles': len(users), 'choices': len(choices),
               'selected_vehicle_specs': len(selected), 'financial_checks': len(assessments),
               'financial_violations': sum(not a['eligible'] for a in assessments),
               'seating_violations': sum(a['seating_status'] != 'match' for a in assessments),
               'labels': {'A': 75, 'B': 75}, 'partitions': {r: {'profiles':sum(u['split']==r for u in users),
                       'choices':sum(c['split']==r for c in choices)} for r in arrays}, 'candidate_assessments': assessments})
    (OUTPUT / 'REVIEW.md').write_text('\n'.join(review), encoding='utf-8')
    files = [p for p in OUTPUT.iterdir() if p.is_file() and p.name != 'manifest.json']
    write_json(OUTPUT / 'manifest.json', {'version':'authored-pilot-v1', 'branch_base':'a31fe22',
               'catalog_source':str(SOURCE.relative_to(ROOT)), 'catalog_source_sha256':hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
               'authoring':'30 individually authored scenarios and 150 explicit choices; no utility formula or sampled labels',
               'legacy_feature_names':list(FEATURE_NAMES),
               'files_sha256':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(files)}})
    print(json.dumps({'profiles':len(users),'choices':len(choices),'selected_specs':len(selected),'output':str(OUTPUT)}, ensure_ascii=False))


if __name__ == '__main__':
    main()
