"""Generate versioned synthetic pair choices from the registered vehicle catalog."""
import argparse
from collections import Counter, defaultdict
from contextlib import ExitStack
from dataclasses import asdict, fields
from decimal import Decimal
import hashlib
from itertools import combinations
import json
import math
from pathlib import Path
import random
import subprocess
from urllib.request import urlopen

import numpy as np

from vehicle_matching.body_types import BODY_TYPES, matches_body_preference
from vehicle_matching.catalog import ROOT, FUELS, Vehicle, read_catalog, save_catalog
from vehicle_matching.finance import Assumptions, Profile, assess
from vehicle_matching.preference_model import FEATURE_NAMES, encode_preference
from vehicle_matching.preferences import SIZE_BANDS
from vehicle_matching.recommendation_policy import seating_status
from vehicle_matching.train_preference_population import financial_group

VERSION = 'behavioral-choice-v1'
ROLES = ('train', 'validation', 'test')
TYPE_COEFFICIENTS = {
    'balanced': (1, 1, 1, 1, 1),
    'running-cost': (1, 2, .8, 1, .8),
    'asset-preservation': (2, 1, .8, .8, .8),
    'taste': (.7, .7, 1.8, 1.4, 1.4),
}
OLD_RULES = ROOT / 'data/households/synthetic/sports-official-v1-20261028/rules.txt'
NEW_RULES = ROOT / 'data/households/synthetic/behavioral-choice-v1/rules.txt'
DEFAULT_URL = 'http://127.0.0.1:8080/api/v1/vehicles/recommendation-catalog'


def canonical(value):
    return json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(',', ':'), allow_nan=False)


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def derived_seed(seed, name):
    return int(hashlib.sha256(f'{seed}:{name}'.encode()).hexdigest()[:16], 16)


def financial_key(profile):
    names = ('monthly_income', 'monthly_expenses', 'existing_monthly_payment', 'liquid_assets',
             'down_payment', 'emergency_reserve', 'monthly_savings', 'minimum_buffer',
             'purchase_price_ceiling', 'months', 'annual_rate', 'financing_mode', 'annual_distance')
    return canonical({name: getattr(profile, name) for name in names})


def split_for(key, seed):
    number = derived_seed(seed, key) / 2**64
    return 'train' if number < .7 else 'validation' if number < .85 else 'test'


def read_registered_catalog(url):
    with urlopen(url, timeout=20) as response:
        payload = json.load(response)
    if payload.get('success') is not True or not isinstance(payload.get('data'), list):
        raise ValueError('Invalid registered catalog response')
    allowed = {field.name for field in fields(Vehicle)}
    vehicles = [Vehicle(**{k: v for k, v in row.items() if k in allowed}) for row in payload['data']]
    validate_catalog(vehicles)
    return vehicles


def validate_catalog(vehicles):
    if not vehicles or len({v.id for v in vehicles}) != len(vehicles):
        raise ValueError('Catalog must be nonempty with unique vehicle IDs')


def eligible_cost(profile, vehicle, assumptions):
    cost = assess(profile, vehicle, assumptions)
    d = lambda value: Decimal(str(value))
    remaining = d(profile.liquid_assets) - d(profile.emergency_reserve) - d(vehicle.price)
    available = d(profile.monthly_income) - d(profile.monthly_expenses) - d(profile.existing_monthly_payment) - d(profile.monthly_savings)
    deficit = max(Decimal(0), d(cost['monthly_running_cost']) + d(profile.minimum_buffer) - available)
    independent = remaining >= 0 and remaining >= deficit * 12 and (
        not profile.purchase_price_ceiling or vehicle.price <= profile.purchase_price_ceiling)
    if independent != cost['eligible']:
        raise ValueError('Independent Decimal financial audit disagrees')
    if cost['eligible'] and seating_status(profile, vehicle) == 'match':
        return cost
    return None


def utility(profile, vehicle, cost, coefficients):
    funds = profile.liquid_assets - profile.emergency_reserve
    assets = max(0, min(1, (funds - cost['total_purchase_cost']) / max(funds, 1)))
    available = profile.monthly_income - profile.monthly_expenses - profile.existing_monthly_payment - profile.monthly_savings
    running = cost['monthly_running_cost']
    burden = running / max(available - profile.minimum_buffer, running, 1)
    body = .5 if vehicle.body_type is None else float(matches_body_preference(profile.preferred_body_type, vehicle.body_type))
    fuel = 'HYBRID' if vehicle.original_fuel == 'PHEV' else vehicle.fuel
    fuel_match = float(fuel == profile.preferred_fuel)
    size = .5
    if profile.preferred_size != 'any' and vehicle.length_mm is not None:
        lower, upper = SIZE_BANDS[profile.preferred_size]
        size = max(0, 1 - max(lower - vehicle.length_mm, vehicle.length_mm - upper, 0) / 1000)
    wc = profile.cost_importance / 5
    wh = profile.body_importance / 5 if profile.preferred_body_type != 'any' else 0
    wf = profile.fuel_importance / 5 if profile.preferred_fuel else 0
    ws = profile.space_importance / 5 if profile.preferred_size != 'any' else 0
    a, b, h, f, s = coefficients
    denominator = wc * (a + b) + wh * h + wf * f + ws * s
    return (wc * (a * assets - b * burden**2) + wh * h * body + wf * f * fuel_match + ws * s * size) / denominator


def choice_probability(first, second, tau):
    if not math.isfinite(tau) or tau <= 0:
        raise ValueError('Positive finite temperature required')
    difference = (first - second) / tau
    return 1 / (1 + math.exp(-difference)) if difference >= 0 else math.exp(difference) / (1 + math.exp(difference))


def write_json(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + '\n', encoding='utf-8')


def generate(output, vehicles, *, groups=25000, seed=20261028, source='explicit catalog'):
    if groups <= 0:
        raise ValueError('groups must be positive')
    validate_catalog(vehicles)
    vehicles = sorted(vehicles, key=lambda vehicle: vehicle.id)
    rule_texts = [path.read_text(encoding='utf-8') for path in (OLD_RULES, NEW_RULES)]
    seeds = {name: derived_seed(seed, name) for name in ('split', 'financial', 'preferences', 'behavior', 'candidates', 'choice')}
    rngs = {name: random.Random(value) for name, value in seeds.items()}
    output.mkdir(parents=True, exist_ok=False)
    save_catalog(output / 'catalog.json', vehicles)
    for name, text in zip(('legacy_rules.txt', 'behavioral_rules.txt'), rule_texts):
        (output / name).write_text(text, encoding='utf-8')
    (output / 'rules.txt').write_text(
        'Applied rules: legacy_rules.txt and behavioral_rules.txt.\n'
        'Conflicts: behavioral rules override deterministic teacher labels, preference-priority ranking,\n'
        'sports-only per-model quotas, historical input reuse and historical held-out model lists.\n'
        'Fresh input population; no historical training rows are merged.\n'
        'Financial/seating constraints, preference-first inputs, catalog provenance and group isolation remain.\n'
        'No model training or service activation is performed.\n', encoding='utf-8')
    buckets = {role: {'features': [], 'comparisons': [], 'labels': [], 'profile_ids': [], 'vehicle_indices': []} for role in ROLES}
    rejected, counts, types, exposure, wins = (Counter() for _ in range(5))
    group_keys, signatures = set(), set()
    with ExitStack() as stack:
        profiles = {role: stack.enter_context((output / f'{role}_profiles.jsonl').open('w', encoding='utf-8')) for role in ROLES}
        audits = {role: stack.enter_context((output / f'{role}_audit.jsonl').open('w', encoding='utf-8')) for role in ROLES}
        exclusions = stack.enter_context((output / 'excluded_profiles.jsonl').open('w', encoding='utf-8'))
        for group in range(groups):
            financial = financial_group(rngs['financial'], group)
            key = financial_key(Profile(**financial))
            if key in group_keys:
                raise ValueError('Duplicate financial group')
            group_keys.add(key)
            role = split_for(key, seeds['split'])
            group_id = hashlib.sha256(key.encode()).hexdigest()
            for variant in range(4):
                rng = rngs['preferences']
                profile = Profile(**financial, preferred_body_type=rng.choice(('any', *BODY_TYPES, 'OTHER')),
                    preferred_fuel=rng.choice((None, *FUELS)), preferred_size=rng.choice(('any', 'small', 'medium', 'large')),
                    minimum_seats=rng.choice((0, 2, 4, 5, 6, 7, 9)), **{
                        name: rng.choice((1, 3, 5)) for name in ('body_importance', 'cost_importance', 'space_importance', 'fuel_importance', 'seating_importance')})
                signature = canonical(asdict(profile))
                if signature in signatures:
                    rejected['duplicate-profile'] += 1
                    continue
                signatures.add(signature)
                profile_id = group * 4 + variant
                behavior_rng = rngs['behavior']
                kind = behavior_rng.choice(tuple(TYPE_COEFFICIENTS))
                coefficients = [base * behavior_rng.uniform(.8, 1.2) for base in TYPE_COEFFICIENTS[kind]]
                tau = behavior_rng.uniform(.05, .15)
                pool = defaultdict(list)
                for index, vehicle in enumerate(vehicles):
                    cost = eligible_cost(profile, vehicle, Assumptions())
                    if cost is not None:
                        pool[vehicle.brand, vehicle.model].append((index, cost))
                if len(pool) < 2:
                    reason = 'fewer-than-two-eligible-models'
                    rejected[reason] += 1
                    exclusions.write(canonical({'id': profile_id, 'group': group_id, 'split': role, 'profile': asdict(profile), 'reason': reason, 'eligible_models': len(pool)}) + '\n')
                    continue
                candidate_rng = rngs['candidates']
                families = candidate_rng.sample(sorted(pool), min(16, len(pool)))
                candidates = [candidate_rng.choice(pool[family]) for family in families]
                pairs = candidate_rng.sample(list(combinations(range(len(candidates)), 2)), min(8, math.comb(len(candidates), 2)))
                used = sorted({index for pair in pairs for index in pair})
                bucket = buckets[role]
                positions = {}
                for index in used:
                    car_index, cost = candidates[index]
                    positions[index] = len(bucket['features'])
                    bucket['features'].append(encode_preference(profile, vehicles[car_index], cost=cost))
                    bucket['profile_ids'].append(profile_id)
                    bucket['vehicle_indices'].append(car_index)
                profiles[role].write(canonical({'id': profile_id, 'group': group_id, 'split': role, 'profile': asdict(profile)}) + '\n')
                for first, second in pairs:
                    if candidate_rng.random() < .5:
                        first, second = second, first
                    i, cost_a = candidates[first]
                    j, cost_b = candidates[second]
                    ua = utility(profile, vehicles[i], cost_a, coefficients)
                    ub = utility(profile, vehicles[j], cost_b, coefficients)
                    probability = choice_probability(ua, ub, tau)
                    draw = rngs['choice'].random()
                    label = int(draw < probability)
                    bucket['comparisons'].append((positions[first], positions[second]))
                    bucket['labels'].append(label)
                    audits[role].write(canonical({'profile_id': profile_id, 'a': vehicles[i].id, 'b': vehicles[j].id,
                        'type': kind, 'coefficients': coefficients, 'tau': tau, 'utility_a': ua, 'utility_b': ub,
                        'probability_a': probability, 'draw': draw, 'label': label}) + '\n')
                    exposure[vehicles[i].id] += 1
                    exposure[vehicles[j].id] += 1
                    wins[vehicles[i if label else j].id] += 1
                counts[role] += 1
                types[kind] += 1
    partitions = {}
    for role, bucket in buckets.items():
        arrays = {'features': np.asarray(bucket['features'], dtype=np.float32).reshape(-1, len(FEATURE_NAMES)),
                  'comparisons': np.asarray(bucket['comparisons'], dtype=np.int64).reshape(-1, 2),
                  'labels': np.asarray(bucket['labels'], dtype=np.int8),
                  'profile_ids': np.asarray(bucket['profile_ids'], dtype=np.int64),
                  'vehicle_indices': np.asarray(bucket['vehicle_indices'], dtype=np.int64)}
        np.savez_compressed(output / f'{role}_choices.npz', **arrays)
        partitions[role] = {'profiles': counts[role], 'comparisons': len(arrays['labels']), 'features': len(arrays['features'])}
    try:
        revision = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip()
        dirty = bool(subprocess.check_output(['git', 'status', '--porcelain'], cwd=ROOT, text=True).strip())
    except (OSError, subprocess.CalledProcessError):
        revision, dirty = None, None
    report = {'version': VERSION, 'source': source, 'seed': seed, 'derived_seeds': seeds,
              'configuration': {'type_coefficients': TYPE_COEFFICIENTS, 'type_probabilities': [.25] * 4,
                                'coefficient_multiplier_range': [.8, 1.2], 'tau_range': [.05, .15],
                                'profiles_per_group': 4, 'candidate_models_max': 16, 'comparisons_max': 8,
                                'importance_values': [1, 3, 5], 'split_probabilities': [.7, .15, .15]},
              'groups_requested': groups, 'profiles_attempted': groups * 4, 'partitions': partitions,
              'rejected': dict(rejected), 'accepted_behavior_types': dict(types), 'vehicle_exposure': dict(exposure),
              'vehicle_wins': dict(wins), 'catalog_count': len(vehicles), 'assumptions': Assumptions().to_dict(),
              'feature_names': list(FEATURE_NAMES), 'git_revision': revision, 'git_dirty': dirty,
              'generator_sha256': sha256(__file__), 'financial_generator_sha256': sha256(ROOT / 'ml/vehicle_matching/train_preference_population.py'),
              'dependency_sha256': {name: sha256(ROOT / 'ml/vehicle_matching' / name) for name in
                                    ('finance.py', 'catalog.py', 'body_types.py', 'preference_model.py', 'preferences.py', 'recommendation_policy.py')},
              'evaluation_scope': 'synthetic conditional pair choice; unseen financial groups, not unseen vehicles or actual purchases',
              'schema': 'choices-v1: comparisons index feature rows; labels=1 means A selected. No teacher-score targets; incompatible with legacy trainers.',
              'files_sha256': {path.name: sha256(path) for path in sorted(output.iterdir()) if path.is_file()}}
    write_json(output / 'generation_report.json', report)
    audit = audit_saved(output)
    write_json(output / 'saved_data_audit.json', audit)
    return report


def audit_saved(directory):
    """Re-read stored artifacts and reject leakage, infeasible pairs or corrupt choices."""
    report = json.loads((directory / 'generation_report.json').read_text(encoding='utf-8'))
    for name, expected in report['files_sha256'].items():
        if sha256(directory / name) != expected:
            raise ValueError(f'Artifact checksum mismatch: {name}')
    vehicles = read_catalog(directory / 'catalog.json')
    groups, signatures, ids = {}, set(), set()
    checked = 0
    for role in ROLES:
        records = {}
        for line in (directory / f'{role}_profiles.jsonl').read_text(encoding='utf-8').splitlines():
            record = json.loads(line)
            profile = Profile(**record['profile'])
            key, signature = financial_key(profile), canonical(record['profile'])
            if groups.setdefault(key, role) != role or signature in signatures or record['id'] in ids or record['split'] != role:
                raise ValueError('Profile duplicate or split leakage')
            if split_for(key, report['derived_seeds']['split']) != role or record['group'] != hashlib.sha256(key.encode()).hexdigest():
                raise ValueError('Financial group assignment mismatch')
            signatures.add(signature)
            ids.add(record['id'])
            records[record['id']] = profile
        with np.load(directory / f'{role}_choices.npz', allow_pickle=False) as arrays:
            x, pairs, labels = arrays['features'], arrays['comparisons'], arrays['labels']
            if not np.isfinite(x).all() or x.shape[1:] != (len(FEATURE_NAMES),) or len(pairs) != len(labels):
                raise ValueError('Invalid stored feature/choice arrays')
            used, seen_pairs, audit_count = set(), set(), 0
            behavior_by_profile = {}
            with (directory / f'{role}_audit.jsonl').open(encoding='utf-8') as stream:
                for offset, line in enumerate(stream):
                    if offset >= len(pairs):
                        raise ValueError('Extra audit records')
                    record = json.loads(line)
                    first, second = (int(value) for value in pairs[offset])
                    if not (0 <= first < len(x) and 0 <= second < len(x)):
                        raise ValueError('Comparison index out of bounds')
                    profile_id = record['profile_id']
                    profile = records[profile_id]
                    i, j = int(arrays['vehicle_indices'][first]), int(arrays['vehicle_indices'][second])
                    a, b = vehicles[i], vehicles[j]
                    pair_key = (profile_id, *sorted((a.id, b.id)))
                    if pair_key in seen_pairs or (a.brand, a.model) == (b.brand, b.model):
                        raise ValueError('Duplicate or same-model comparison')
                    seen_pairs.add(pair_key)
                    state = canonical([record['type'], record['coefficients'], record['tau']])
                    bases = TYPE_COEFFICIENTS.get(record['type'])
                    if bases is None or len(record['coefficients']) != 5 or not .05 <= record['tau'] <= .15:
                        raise ValueError('Invalid saved behavior')
                    if any(not .8 * base <= value <= 1.2 * base for base, value in zip(bases, record['coefficients'])):
                        raise ValueError('Behavior coefficient outside configured range')
                    if behavior_by_profile.setdefault(profile_id, state) != state:
                        raise ValueError('User behavior changed across choices')
                    costs = [eligible_cost(profile, car, Assumptions()) for car in (a, b)]
                    if any(cost is None for cost in costs) or [a.id, b.id] != [record['a'], record['b']]:
                        raise ValueError('Ineligible or mismatched saved comparison')
                    for row, car, cost in zip((first, second), (a, b), costs):
                        if arrays['profile_ids'][row] != profile_id or not np.array_equal(x[row], encode_preference(profile, car, cost=cost)):
                            raise ValueError('Feature mismatch or cross-person comparison')
                    ua, ub = [utility(profile, car, cost, record['coefficients']) for car, cost in zip((a, b), costs)]
                    p = choice_probability(ua, ub, record['tau'])
                    if not (0 <= record['draw'] < 1) or not math.isclose(p, record['probability_a'], abs_tol=1e-12):
                        raise ValueError('Invalid choice probability')
                    if not math.isclose(ua, record['utility_a'], abs_tol=1e-12) or not math.isclose(ub, record['utility_b'], abs_tol=1e-12):
                        raise ValueError('Utility mismatch')
                    if int(record['draw'] < p) != record['label'] or record['label'] != int(labels[offset]):
                        raise ValueError('Choice draw and label disagree')
                    used.update((first, second))
                    checked += 1
                    audit_count += 1
            if audit_count != len(pairs) or used != set(range(len(x))):
                raise ValueError('Missing choice audit or orphan feature rows')
    return {'status': 'passed', 'comparisons_checked': checked, 'profiles_checked': len(ids),
            'split_leakage': 0, 'ineligible_comparisons': 0, 'label_mismatches': 0}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True, help='New directory; existing paths are rejected')
    parser.add_argument('--groups', type=int, default=25000, help='Financial groups, four profiles per group')
    parser.add_argument('--seed', type=int, default=20261028)
    source = parser.add_mutually_exclusive_group()
    source.add_argument('--catalog-url', default=DEFAULT_URL)
    source.add_argument('--catalog', type=Path, help='Explicit offline catalog snapshot; never an automatic fallback')
    args = parser.parse_args()
    if args.output.exists():
        parser.error('Output directory already exists')
    if args.groups <= 0:
        parser.error('--groups must be positive')
    vehicles = read_catalog(args.catalog) if args.catalog else read_registered_catalog(args.catalog_url)
    report = generate(args.output, vehicles, groups=args.groups, seed=args.seed,
                      source=str(args.catalog.resolve()) if args.catalog else args.catalog_url)
    print(json.dumps({'output': str(args.output.resolve()), 'partitions': report['partitions'], 'audit': 'passed'}, ensure_ascii=False))


if __name__ == '__main__':
    main()
