"""Controlled synthetic cohorts: identical finances/pools, one preference changed.

Run from the repository root with PYTHONPATH=ml. Scores are declared policy
labels, never real satisfaction observations or outputs of the trained model.
"""
import argparse
from collections import Counter
import copy
import csv
import hashlib
import json
import math
from pathlib import Path
import random
import re

from vehicle_matching.catalog import ROOT
from vehicle_matching.finance import Profile
from vehicle_matching.train_preference_population import financial_group
from tools.data.households.generate_behavioral_choices import (
    canonical, derived_seed, financial_key, sha256, split_for, write_json,
)
from tools.data.households.generate_lifestyle_choices import (
    DEFAULT_BASE, DEFAULT_LUXURY, load_catalog, safe_cost,
)
from tools.data.vehicles.lifestyle_traits import DEFAULT_REVIEWS, build_traits, read_reviews

SCHEMA = 'controlled-preference-cohorts-v1'
DEFAULT_DETAILS = ROOT / 'data/vehicles/new-model-details-20261028/vehicle-details.json'
AXES = {
    'body_type': {'label': '차체 형태', 'targets': ['SEDAN', 'SUV', 'COUPE'], 'meaning': '세단 / SUV / 쿠페 선호'},
    'exterior_sportiness': {'label': '사진 평가 기반 외관 비례', 'targets': [0, .5, 1], 'meaning': '높고 직립한 / 혼합 / 낮고 스포티한 비례'},
    'exterior_angularity': {'label': '사진 평가 기반 직선·곡선 성향', 'targets': [0, .5, 1], 'meaning': '곡면 / 혼합 / 각진 윤곽'},
    'acceleration_performance': {'label': '공개 조건의 가속 성능', 'targets': [0, .5, 1], 'meaning': '낮은 / 중간 / 높은 가속 성능을 선호하는 실험 대조군'},
    'compactness': {'label': '도심 목적의 전장 대리 지표', 'targets': [0, .5, 1], 'meaning': '긴 / 중간 / 짧은 전장 선호'},
    'seat_capacity': {'label': '가족 목적의 정원 대리 지표', 'targets': [0, .5, 1], 'meaning': '적은 / 중간 / 많은 정원 선호; 최소 필요 인원은 고정'},
}
ACCELERATION_LABELS = {'0–100 km/h', 'Acceleration 0 - 100 km/h',
    'Acceleration 0 - 100 km/h with Sport Chrono Package', '가속',
    'Performance · 0-100 km/h'}
CSV_FIELDS = ['comparison_id', 'group_id', 'split', 'task', 'axis', 'target',
    'monthly_income', 'monthly_expenses', 'existing_monthly_payment', 'liquid_assets', 'minimum_seats',
    'vehicle_id', 'brand', 'model', 'trim', 'year', 'rank', 'policy_score', 'trait_value',
    'financial_eligible', 'monthly_running_cost', 'evidence_source', 'label_origin']


def identity(car):
    return tuple(str(car.get(key) or '') for key in ('brand', 'model', 'trim', 'year'))


def add_acceleration_evidence(cars, traits, details):
    """Read only exact-ID/trim/year, unambiguous numeric acceleration fields.

    Display-only details become a separate experimental feature snapshot. Their
    use here does not promote prices, seats or existing ML/model snapshots.
    """
    result = copy.deepcopy(traits)
    lookup = {car['id']: car for car in cars}
    seen = set()
    for row in details['vehicles']:
        if row['id'] in seen:
            raise ValueError('Duplicate detail identity')
        seen.add(row['id'])
        car = lookup.get(row['id'])
        if car is None:
            continue
        if identity(car) != identity(row):
            raise ValueError('Detail identity mismatch: ' + row['id'])
        candidates = [field for field in row['fields'] if field['label'] in ACCELERATION_LABELS
                      and field.get('status') != 'source-conflict']
        seconds = []
        for field in candidates:
            match = re.fullmatch(r'\s*(\d+(?:\.\d+)?)\s*(?:s|sec)\s*', field['value'], re.I)
            if match:
                seconds.append((float(match[1]), field['label']))
        if not seconds or len({value for value, _ in seconds}) != 1:
            continue
        value, condition = seconds[0]
        if not 1 <= value <= 30 or not row.get('source_url'):
            raise ValueError('Invalid acceleration evidence')
        previous = result[row['id']]['evidence'].get('acceleration_performance')
        if previous and previous.get('seconds_0_100') != value:
            raise ValueError('Conflicting acceleration evidence: ' + row['id'])
        result[row['id']]['values']['acceleration_performance'] = min(1, max(0, (12 - value) / 10))
        result[row['id']]['evidence']['acceleration_performance'] = {
            'kind': 'official-acceleration-detail', 'seconds_0_100': value,
            'condition': condition, 'source_url': row['source_url'], 'checked_on': row['checked_on'],
            'notes': row.get('notes', []), 'detail_source_files': row.get('source_files', []),
            'limitation': 'Published conditions can differ; not measured driving sensation or ride comfort.',
        }
    return result


def trait_value(attributes, axis):
    return attributes['body_type'] if axis == 'body_type' else attributes['values'][axis]


def cohort_pool(cars, traits, axis):
    return [car for car in cars if trait_value(traits[car['id']], axis) is not None]


def rank_candidates(cars, traits, axis, target):
    if axis not in AXES or target not in AXES[axis]['targets']:
        raise ValueError('Unsupported axis/target')
    scores = []
    for car in cars:
        value = trait_value(traits[car['id']], axis)
        if value is None:
            raise ValueError('Unknown trait cannot be ranked')
        if axis != 'body_type' and (not isinstance(value, (int, float)) or not math.isfinite(value) or not 0 <= value <= 1):
            raise ValueError('Invalid normalized trait')
        score = float(value == target) if axis == 'body_type' else 1 - abs(target - value)
        scores.append({'vehicle_id': car['id'], 'trait_value': value, 'policy_score': round(score, 12)})
    scores.sort(key=lambda row: (-row['policy_score'], row['vehicle_id']))
    previous, rank = None, 0
    for position, row in enumerate(scores, 1):
        if row['policy_score'] != previous:
            previous, rank = row['policy_score'], position
        row['rank'] = rank  # Equal scores share rank; ID order is only serialization.
    return scores


def record_for(group_id, split, task, financial, cars, traits, axis, costs):
    if task not in ('financial-eligible', 'taste-only'):
        raise ValueError('Unsupported cohort task')
    pool = cohort_pool(cars, traits, axis)
    if len({(car['brand'], car['model']) for car in pool}) < 2:
        return None
    if len({trait_value(traits[car['id']], axis) for car in pool}) < 2:
        return None
    profiles = []
    for target in AXES[axis]['targets']:
        profiles.append({'target': target, 'ranking': rank_candidates(pool, traits, axis, target)})
    # Reversals are an outcome of the declared policy, never forced random labels.
    tops = [{row['vehicle_id'] for row in profile['ranking'] if row['rank'] == 1} for profile in profiles]
    return {'comparison_id': f'{group_id}:{task}:{axis}', 'group_id': group_id, 'split': split,
            'task': task, 'financial': financial, 'axis': axis,
            'candidate_ids': [car['id'] for car in pool],
            'excluded_unknown_count': len(cars) - len(pool),
            'financial_eligible': True if task == 'financial-eligible' else None,
            'costs': {car['id']: costs[car['id']] for car in pool} if task == 'financial-eligible' else {},
            'label_origin': 'deterministic-synthetic-policy', 'profiles': profiles,
            'top_set_changed': any(top != tops[0] for top in tops[1:])}


def generate(output, cars, traits, *, groups=100, seed=20261028, sources=()):
    if type(groups) is not int or groups < 1:
        raise ValueError('groups must be a positive integer')
    cars = sorted(cars, key=lambda car: car['id'])
    if len(cars) < 2 or len({car['id'] for car in cars}) != len(cars):
        raise ValueError('At least two unique vehicles required')
    if set(traits) != {car['id'] for car in cars}:
        raise ValueError('Trait/catalog mismatch')
    output.mkdir(parents=True, exist_ok=False)
    write_json(output / 'catalog.json', cars)
    write_json(output / 'vehicle_traits.json', traits)
    counts, skipped, exposure = Counter(), Counter(), Counter()
    splits, changed, csv_count = Counter(), 0, 0
    rng, keys = random.Random(seed), set()
    lookup = {car['id']:car for car in cars}
    with (output/'comparisons.jsonl').open('w',encoding='utf-8') as stream, (output/'rankings.csv').open('w',encoding='utf-8-sig',newline='') as csv_stream:
        writer = csv.DictWriter(csv_stream,fieldnames=CSV_FIELDS)
        writer.writeheader()
        for index in range(groups):
            financial = financial_group(rng,index)
            financial['minimum_seats'] = rng.choice((0,2,4,5,7))
            profile = Profile(**financial)
            key = financial_key(profile)
            if key in keys:
                raise ValueError('Duplicate financial group')
            keys.add(key)
            group_id = hashlib.sha256(key.encode()).hexdigest()[:24]
            split = split_for(key,derived_seed(seed,'cohort-split'))
            costs = {car['id']: safe_cost(profile,car) for car in cars}
            eligible = [car for car in cars if costs[car['id']] is not None]
            for task,pool in [('financial-eligible',eligible),('taste-only',cars)]:
                for axis in AXES:
                    record = record_for(group_id,split,task,financial,pool,traits,axis,costs)
                    if record is None:
                        skipped[f'{task}:{axis}'] += 1
                        continue
                    stream.write(canonical(record)+'\n')
                    counts[f'{task}:{axis}'] += 1
                    splits[split] += 1
                    changed += record['top_set_changed']
                    exposure.update(record['candidate_ids'])
                    for persona in record['profiles']:
                        for ranked in persona['ranking']:
                            car = lookup[ranked['vehicle_id']]
                            evidence = traits[car['id']]
                            source = evidence['body_sources'] if axis=='body_type' else evidence['evidence'][axis]['source_url']
                            cost = record['costs'].get(car['id'])
                            writer.writerow({**{name:record[name] for name in ('comparison_id','group_id','split','task','axis','financial_eligible','label_origin')},
                                'target':persona['target'], **{name:financial[name] for name in ('monthly_income','monthly_expenses','existing_monthly_payment','liquid_assets','minimum_seats')},
                                **{name:car.get(name) for name in ('brand','model','trim','year')}, **ranked,
                                'monthly_running_cost':cost['monthly_running_cost'] if cost else None,
                                'evidence_source':canonical(source) if isinstance(source,list) else source})
                            csv_count += 1
    report = {'schema':SCHEMA,'seed':seed,'financial_groups':groups,'catalog_count':len(cars),
        'model_families':len({(car['brand'],car['model']) for car in cars}), 'axes':AXES,
        'comparisons':sum(counts.values()),'persona_profiles':3*sum(counts.values()),'ranking_csv_rows':csv_count,
        'counts':dict(counts),'skipped_insufficient_evidence':dict(skipped),'splits':dict(splits),
        'top_set_changed_comparisons':changed,'exposed_vehicle_count':len(exposure),
        'unexposed_vehicle_ids':sorted(set(lookup)-set(exposure)),
        'coverage':{axis:len(cohort_pool(cars,traits,axis)) for axis in AXES},
        'sources':{str(path):sha256(path) for path in sources},
        'snapshot_hashes':{name:sha256(output/name) for name in ('catalog.json','vehicle_traits.json','comparisons.jsonl','rankings.csv')},
        'policy':{'score':'body: exact category match; numeric: 1 - abs(target - observed_trait)',
            'numeric_targets':{'0':'특성값 하단 선호 대조군','0.5':'중간 특성 선호','1':'특성값 상단 선호 대조군'},
            'acceleration':'clip((12 - seconds_0_100) / 10, 0, 1); inspect evidence.kind: official or explicitly synthetic estimated-acceleration',
            'ties':'competition ranks; top-1 is a set; IDs only break serialization order',
            'missing':'axis-specific shared evidence pool, identical for all three targets',
            'split':'all tasks/axes/targets sharing financial inputs stay in one split'},
        'limitations':['Synthetic policy labels are not actual user choices or model accuracy.',
            'Taste-only includes research vehicles and never asserts purchase/seat eligibility.',
            'Acceleration is published-condition performance, not driving sensation.',
            'Explicit estimated-acceleration evidence, when supplied, is an unvalidated synthetic prior, not published or measured performance.',
            'Visual assessments are ordinal and subjective, not objective design quality.',
            'Length and seat count are purpose proxies, not overall practicality or comfort.',
            'Missing ride comfort, cargo volume and interior evidence is not invented.',
            'Each comparison isolates one axis; cross-axis pools must not be compared as a controlled experiment.',
            'This is a new cohort schema; existing pairwise trainers cannot consume it directly.']}
    write_json(output/'generation_report.json',report)
    write_json(output/'saved_data_audit.json',audit_saved(output))
    return report


def audit_saved(output):
    """Replay saved ranking, pool eligibility, group partition and CSV links."""
    report = json.loads((output/'generation_report.json').read_text(encoding='utf-8'))
    if report['schema'] != SCHEMA:
        raise ValueError('Unsupported cohort schema')
    for name,digest in report['snapshot_hashes'].items():
        if sha256(output/name) != digest:
            raise ValueError('Snapshot hash mismatch: '+name)
    cars = json.loads((output/'catalog.json').read_text(encoding='utf-8'))
    traits = json.loads((output/'vehicle_traits.json').read_text(encoding='utf-8'))
    seen,groups,cache = set(),{},{}
    count = csv_count = 0
    with (output/'comparisons.jsonl').open(encoding='utf-8') as stream, (output/'rankings.csv').open(encoding='utf-8-sig',newline='') as csv_stream:
        reader = csv.DictReader(csv_stream)
        for line in stream:
            row = json.loads(line)
            profile = Profile(**row['financial'])
            key = financial_key(profile)
            group_id = hashlib.sha256(key.encode()).hexdigest()[:24]
            split = split_for(key,derived_seed(report['seed'],'cohort-split'))
            if row['comparison_id'] in seen or row['group_id'] != group_id or row['split'] != split:
                raise ValueError('Duplicate comparison or split leakage')
            seen.add(row['comparison_id'])
            if groups.setdefault(group_id,canonical(row['financial'])) != canonical(row['financial']):
                raise ValueError('Financial group changed')
            if group_id not in cache:
                cache[group_id] = {car['id']:safe_cost(profile,car) for car in cars}
            costs = cache[group_id]
            pool = cars if row['task']=='taste-only' else [car for car in cars if costs[car['id']] is not None]
            expected = record_for(group_id,split,row['task'],row['financial'],pool,traits,row['axis'],costs)
            if row != expected:
                raise ValueError('Saved cohort ranking or candidate pool mismatch')
            for persona in row['profiles']:
                for ranked in persona['ranking']:
                    flat = next(reader,None)
                    if flat is None or flat['comparison_id'] != row['comparison_id'] or flat['vehicle_id'] != ranked['vehicle_id'] or flat['target'] != str(persona['target']) or int(flat['rank']) != ranked['rank'] or float(flat['policy_score']) != ranked['policy_score']:
                        raise ValueError('CSV/JSONL ranking mismatch')
                    csv_count += 1
            count += 1
        if next(reader,None) is not None or count != report['comparisons'] or csv_count != report['ranking_csv_rows']:
            raise ValueError('Saved row count mismatch')
    return {'status':'passed','comparisons_checked':count,'ranking_rows_checked':csv_count,'financial_groups_checked':len(groups)}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--base',type=Path,default=DEFAULT_BASE)
    parser.add_argument('--luxury',type=Path,default=DEFAULT_LUXURY)
    parser.add_argument('--reviews',type=Path,default=DEFAULT_REVIEWS)
    parser.add_argument('--details',type=Path,default=DEFAULT_DETAILS)
    parser.add_argument('--traits',type=Path,help='Explicit full-trait snapshot, including separately labelled synthetic estimates')
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--groups',type=int,default=100)
    parser.add_argument('--seed',type=int,default=20261028)
    args = parser.parse_args()
    cars = load_catalog(args.base,args.luxury)
    traits = (json.loads(args.traits.read_text(encoding='utf-8'))['vehicles'] if args.traits else
        add_acceleration_evidence(cars,build_traits(cars,read_reviews(args.reviews)),
            json.loads(args.details.read_text(encoding='utf-8'))))
    if set(traits) != {car['id'] for car in cars}:
        raise ValueError('Trait snapshot/catalog identity mismatch')
    report = generate(args.output,cars,traits,groups=args.groups,seed=args.seed,
        sources=(args.base,args.luxury,args.reviews,args.details,Path(__file__),
                 ROOT/'tools/data/vehicles/lifestyle_traits.py', ROOT/'ml/vehicle_matching/finance.py',
                 ROOT/'tools/data/households/generate_lifestyle_choices.py') + ((args.traits,) if args.traits else ()))
    print(canonical({key:report[key] for key in ('catalog_count','model_families','comparisons','persona_profiles','ranking_csv_rows','coverage')}))


if __name__ == '__main__':
    main()
