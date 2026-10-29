"""Evidence-backed vehicle traits with synthetic user preferences and choices."""
import argparse
from collections import Counter
from contextlib import ExitStack
from dataclasses import asdict, fields
import hashlib
import json
from pathlib import Path
import random

import numpy as np

from vehicle_matching.catalog import ROOT, Vehicle
from vehicle_matching.finance import Assumptions, Profile
from vehicle_matching.train_preference_population import financial_group
from tools.data.vehicles.lifestyle_traits import (
    DIMENSIONS, DEFAULT_REVIEWS, build_traits, read_reviews, pair_masks,
)
from tools.data.households.generate_behavioral_choices import (
    canonical, choice_probability, derived_seed, eligible_cost, financial_key,
    sha256, split_for, write_json,
)

VERSION = 'lifestyle-choice-v2-evidence'
PURPOSES = ('commute', 'family', 'camping', 'weekend-drive', 'business')
# Capacity is NOT sufficient evidence of camping suitability; cargo is unknown.
PURPOSE_DIMENSIONS = ('compactness', 'seat_capacity', None, 'acceleration_performance', 'ride_comfort')
FEATURE_NAMES = tuple(f'{name}_match' for name in DIMENSIONS) + ('purpose_match', 'body_match', 'brand_match', 'asset_retention')
DEFAULT_BASE = ROOT / 'data/households/synthetic/sports-official-v1-20261028/catalog.json'
DEFAULT_LUXURY = ROOT / 'data/vehicles/luxury-sports-review-20261028/reviewed.json'
ROLES = ('train', 'validation', 'test')


def load_catalog(base, luxury):
    cars = json.loads(base.read_text(encoding='utf-8'))
    for car in cars:
        car['provenance'] = {'kind': 'existing-snapshot', 'path': str(base.relative_to(ROOT)) if base.is_relative_to(ROOT) else str(base)}
    review = json.loads(luxury.read_text(encoding='utf-8'))
    porsche = review['porsche']
    for values in porsche['configurations']:
        row = dict(zip(porsche['columns'], values))
        row.update(brand='Porsche', fuel='GASOLINE', efficiency=None, seats=None,
                   source_url=porsche['price_source'], checked_on=review['checked_on'],
                   provenance={'kind': 'official-price-incomplete-specifications',
                               'review': str(luxury), 'price_basis': porsche['price_basis'],
                               'fuel_basis': porsche['fuel_basis'], 'production_ready': False})
        cars.append(row)
    for key, brand in (('ferrari', 'Ferrari'), ('lamborghini', 'Lamborghini')):
        for candidate in review[key]['candidates']:
            row = dict(candidate, brand=brand, trim='research-candidate', year=None,
                       price=candidate['reported_price'], efficiency=None, seats=None,
                       source_url=candidate.get('price_source') or candidate.get('domestic_evidence'),
                       checked_on=review['checked_on'],
                       provenance={'kind': 'unverified-research-candidate', 'review': str(luxury),
                                   'price_status': candidate['price_status'], 'production_ready': False})
            cars.append(row)
    for car in cars:
        if not car.get('id'):
            identity = [car['brand'], car['model'], car['trim'], car.get('year')]
            car['id'] = 'research-' + hashlib.sha256(canonical(identity).encode()).hexdigest()[:16]
    if len({car['id'] for car in cars}) != len(cars):
        raise ValueError('Duplicate vehicle IDs')
    return sorted(cars, key=lambda car: car['id'])


def safe_cost(profile, car):
    if car['provenance']['kind'] != 'existing-snapshot':
        return None  # Research candidates cannot become financial recommendations.
    names = {field.name for field in fields(Vehicle)}
    return eligible_cost(profile, Vehicle(**{k: v for k, v in car.items() if k in names}), Assumptions())


def encode(taste, attributes, car, retention):
    values = attributes['values']
    matches = [0 if values[name] is None else 1 - abs(taste['targets'][name] - values[name]) for name in DIMENSIONS]
    purpose_dimension = PURPOSE_DIMENSIONS[PURPOSES.index(taste['purpose'])]
    purpose = values.get(purpose_dimension) or 0
    body = float(attributes['body_type'] == taste['body_type'])
    brand = .5 if taste['brand'] is None else float(taste['brand'] == car['brand'])
    return matches + [purpose, body, brand, retention]


def comparison_mask(taste, a, b, eligible):
    masks = pair_masks(a, b)
    dimension = PURPOSE_DIMENSIONS[PURPOSES.index(taste['purpose'])]
    purpose_known = dimension is not None and a['values'][dimension] is not None and b['values'][dimension] is not None
    return masks + [int(purpose_known), int(a['body_type'] is not None and b['body_type'] is not None),
                    int(taste['brand'] is not None), int(eligible)]


def informative(a, b):
    return bool(comparison_channels(a, b))


def comparison_channels(a, b):
    channels = [name for name in DIMENSIONS if a['values'][name] is not None
                and b['values'][name] is not None and a['values'][name] != b['values'][name]]
    if a['body_type'] is not None and b['body_type'] is not None and a['body_type'] != b['body_type']:
        channels.append('body_type')
    return channels


def score(features, weights):
    return sum(a * b for a, b in zip(features, weights)) / sum(weights)


def generate(output, cars, *, groups=20000, seed=20261028, sources=(), reviews=None):
    if groups < 1 or len({(c['brand'], c['model']) for c in cars}) < 2:
        raise ValueError('Positive groups and at least two vehicle families required')
    if len({c['id'] for c in cars}) != len(cars):
        raise ValueError('Duplicate vehicle IDs')
    cars = sorted(cars, key=lambda car: car['id'])
    attrs = build_traits(cars, read_reviews() if reviews is None else reviews)
    alternatives = {car['id']: [other for other in cars if (car['brand'], car['model']) != (other['brand'], other['model'])
                                and informative(attrs[car['id']], attrs[other['id']])] for car in cars}
    if any(not pool for pool in alternatives.values()):
        raise ValueError('Some vehicles have no evidence-supported comparison; collect evidence first')
    channel_pools = {car['id']: {
        channel: [other for other in alternatives[car['id']] if channel in comparison_channels(attrs[car['id']], attrs[other['id']])]
        for channel in sorted({channel for other in alternatives[car['id']] for channel in comparison_channels(attrs[car['id']], attrs[other['id']])})
    } for car in cars}
    rng = random.Random(seed)
    output.mkdir(parents=True, exist_ok=False)
    write_json(output / 'catalog.json', cars)
    write_json(output / 'vehicle_traits.json', {
        'status': 'evidence-backed-with-explicit-unknowns', 'dimensions': DIMENSIONS, 'vehicles': attrs})
    buckets = {role: {'a': [], 'b': [], 'weights': [], 'masks': [], 'labels': [], 'financial_eligible': []} for role in ROLES}
    exposure, tasks, counts, channel_counts = Counter(), Counter(), Counter(), Counter()
    keys = set()
    with ExitStack() as stack:
        streams = {role: stack.enter_context((output / f'{role}.jsonl').open('w', encoding='utf-8')) for role in ROLES}
        for group in range(groups):
            financial = financial_group(rng, group)
            financial['minimum_seats'] = rng.choice((0, 2, 4, 5, 7))
            profile = Profile(**financial)
            key = financial_key(profile)
            if key in keys:
                raise ValueError('Duplicate financial group')
            keys.add(key)
            role = split_for(key, derived_seed(seed, 'split'))
            # Round-robin anchors guarantee candidate exposure without forcing wins.
            a = cars[group % len(cars)]
            channels = sorted(channel_pools[a['id']])
            channel = channels[(group // len(cars)) % len(channels)]
            b = rng.choice(channel_pools[a['id']][channel])
            costs = [safe_cost(profile, car) for car in (a, b)]
            eligible = all(cost is not None for cost in costs)
            task = 'eligible-preference' if eligible else 'taste-only'
            retention = [(max(0, min(1, (profile.liquid_assets - cost['total_purchase_cost']) / max(profile.liquid_assets, 1))) if eligible else 0) for cost in costs]
            importance = [rng.uniform(.3, 1.5) for _ in range(len(FEATURE_NAMES) - 1)] + [rng.uniform(0, .5) if eligible else 0]
            tau = rng.uniform(.05, .15)
            purpose = rng.choice(PURPOSES)
            brand = rng.choice((None, *sorted({car['brand'] for car in cars})))
            body = rng.choice(sorted({entry['body_type'] for entry in attrs.values() if entry['body_type'] is not None}))
            targets = {name: rng.random() for name in DIMENSIONS}
            for variant in range(2):
                taste = {'targets': targets if variant == 0 else {name: 1 - value for name, value in targets.items()},
                         'purpose': purpose, 'brand': brand, 'body_type': body}
                masks = comparison_mask(taste, attrs[a['id']], attrs[b['id']], eligible)
                weights = [weight * mask for weight, mask in zip(importance, masks)]
                weights[-1] = min(weights[-1], .2 * sum(weights[:-1]))
                fa, fb = [encode(taste, attrs[car['id']], car, r) for car, r in zip((a, b), retention)]
                fa, fb = [[value * mask for value, mask in zip(features, masks)] for features in (fa, fb)]
                ua, ub = score(fa, weights), score(fb, weights)
                probability = choice_probability(ua, ub, tau)
                draw = rng.random()
                label = int(draw < probability)
                record = {'id': group * 2 + variant, 'group': hashlib.sha256(key.encode()).hexdigest(),
                          'split': role, 'task': task, 'financial': asdict(profile), 'taste': taste,
                          'sampling_channel': channel,
                          'a': a['id'], 'b': b['id'], 'features_a': fa, 'features_b': fb,
                          'importance': importance, 'masks': masks, 'weights': weights, 'tau': tau, 'utility_a': ua, 'utility_b': ub,
                          'probability_a': probability, 'draw': draw, 'label': label,
                          'financial_eligible': eligible}
                streams[role].write(canonical(record) + '\n')
                bucket = buckets[role]
                for name, value in (('a', fa), ('b', fb), ('weights', weights), ('masks', masks), ('labels', label), ('financial_eligible', eligible)):
                    bucket[name].append(value)
                exposure.update((a['id'], b['id']))
                tasks[task] += 1
                counts[role] += 1
                channel_counts[channel] += 1
    for role, bucket in buckets.items():
        arrays = {name: np.asarray(value, dtype=np.float32).reshape(-1, len(FEATURE_NAMES)) if name in ('a', 'b', 'weights', 'masks')
                  else np.asarray(value, dtype=np.int8) for name, value in bucket.items()}
        np.savez_compressed(output / f'{role}_choices.npz', **arrays)
    report = {'schema': VERSION, 'seed': seed, 'groups': groups, 'profiles': groups * 2,
              'catalog_count': len(cars), 'model_families': len({(c['brand'], c['model']) for c in cars}),
              'feature_names': FEATURE_NAMES, 'partitions': dict(counts), 'tasks': dict(tasks),
              'sampling_channels': dict(channel_counts),
              'exposure': dict(exposure), 'unexposed_ids': [c['id'] for c in cars if not exposure[c['id']]],
              'sources': {str(path): sha256(path) for path in sources},
              'trait_coverage': {name: sum(entry['values'][name] is not None for entry in attrs.values()) for name in DIMENSIONS},
              'traits_sha256': sha256(output / 'vehicle_traits.json'),
              'policy': {'finance_weight_max_ratio_to_nonfinancial': .2,
                         'purpose_proxies': dict(zip(PURPOSES, PURPOSE_DIMENSIONS)),
                         'acceleration_normalization': 'clip((12 - seconds_0_100) / 10, 0, 1)',
                         'capacity_normalization': 'clip((seats - 2) / 7, 0, 1)',
                         'compactness_normalization': 'clip((6000 - length_mm) / 3500, 0, 1)'},
              'limitations': ['Photo assessments are ordinal, subjective and representative-family-level, not exact-trim measurements.',
                             'Unknown dimensions are masked for BOTH candidates; zero placeholders are not negative ratings.',
                             'Capacity and compactness are declared proxies, not overall practicality; acceleration is not driving enjoyment.',
                             'Research prices remain unverified; missing fields remain null.',
                             'Taste-only choices do not assert financial or seat eligibility.',
                             'Synthetic policy agreement is not actual user preference accuracy.',
                             'New feature schema requires a separate trainer; existing models cannot load it.']}
    write_json(output / 'generation_report.json', report)
    write_json(output / 'saved_data_audit.json', audit_saved(output))
    return report


def audit_saved(output):
    cars = {c['id']: c for c in json.loads((output / 'catalog.json').read_text(encoding='utf-8'))}
    attrs = json.loads((output / 'vehicle_traits.json').read_text(encoding='utf-8'))['vehicles']
    report = json.loads((output / 'generation_report.json').read_text(encoding='utf-8'))
    if report['schema'] != VERSION or sha256(output / 'vehicle_traits.json') != report['traits_sha256']:
        raise ValueError('Unsupported schema or changed trait evidence')
    groups, ids, exposure = {}, set(), Counter()
    checked = 0
    for role in ROLES:
        with np.load(output / f'{role}_choices.npz') as archive:
            arrays = {name: archive[name] for name in archive.files}
            offset = 0
            with (output / f'{role}.jsonl').open(encoding='utf-8') as stream:
                for offset, line in enumerate(stream, 1):
                    row = json.loads(line)
                    profile = Profile(**row['financial'])
                    key = financial_key(profile)
                    group = hashlib.sha256(key.encode()).hexdigest()
                    if (row['id'] in ids or row['group'] != group or row['split'] != role
                            or groups.setdefault(group, role) != role
                            or split_for(key, derived_seed(report['seed'], 'split')) != role):
                        raise ValueError('Duplicate identity or split leakage')
                    ids.add(row['id'])
                    pair = [cars[row[name]] for name in ('a', 'b')]
                    if not informative(attrs[pair[0]['id']], attrs[pair[1]['id']]):
                        raise ValueError('No shared evidence for comparison')
                    if row['sampling_channel'] not in comparison_channels(attrs[pair[0]['id']], attrs[pair[1]['id']]):
                        raise ValueError('Invalid evidence sampling channel')
                    costs = [safe_cost(profile, car) for car in pair]
                    eligible = all(cost is not None for cost in costs)
                    if row['financial_eligible'] != eligible or row['task'] != ('eligible-preference' if eligible else 'taste-only'):
                        raise ValueError('Financial eligibility mismatch')
                    masks = comparison_mask(row['taste'], attrs[pair[0]['id']], attrs[pair[1]['id']], eligible)
                    expected_weights = [w * m for w, m in zip(row['importance'], masks)]
                    expected_weights[-1] = min(expected_weights[-1], .2 * sum(expected_weights[:-1]))
                    if row['masks'] != masks or row['weights'] != expected_weights or not np.array_equal(masks, arrays['masks'][offset - 1]):
                        raise ValueError('Unknown-evidence mask mismatch')
                    for name, car, cost in zip(('a', 'b'), pair, costs):
                        retention = max(0, min(1, (profile.liquid_assets - cost['total_purchase_cost']) / max(profile.liquid_assets, 1))) if eligible else 0
                        features = encode(row['taste'], attrs[car['id']], car, retention)
                        features = [value * mask for value, mask in zip(features, masks)]
                        if features != row[f'features_{name}'] or not np.allclose(features, arrays[name][offset - 1], atol=1e-7):
                            raise ValueError('Stored feature mismatch')
                        if abs(score(features, row['weights']) - row[f'utility_{name}']) > 1e-12:
                            raise ValueError('Stored utility mismatch')
                    probability = choice_probability(row['utility_a'], row['utility_b'], row['tau'])
                    if (abs(probability - row['probability_a']) > 1e-12 or row['label'] != int(row['draw'] < probability)
                            or row['label'] != int(arrays['labels'][offset - 1])
                            or bool(arrays['financial_eligible'][offset - 1]) != eligible
                            or not np.allclose(row['weights'], arrays['weights'][offset - 1], atol=1e-7)
                            or (not eligible and row['weights'][-1] != 0)):
                        raise ValueError('Stored label or weights mismatch')
                    exposure.update(car['id'] for car in pair)
                    checked += 1
            if offset != len(arrays['labels']):
                raise ValueError('Array/record count mismatch')
    if checked != report['profiles'] or dict(exposure) != report['exposure']:
        raise ValueError('Report count mismatch')
    return {'status': 'passed', 'comparisons_checked': checked, 'financial_groups': len(groups),
            'split_leakage': 0, 'feature_label_mismatches': 0,
            'auditor_sha256': sha256(Path(__file__)),
            'sha256': {path.name: sha256(path) for path in sorted(output.iterdir()) if path.suffix in ('.jsonl', '.npz')}}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--base', type=Path, default=DEFAULT_BASE)
    parser.add_argument('--luxury', type=Path, default=DEFAULT_LUXURY)
    parser.add_argument('--reviews', type=Path, default=DEFAULT_REVIEWS)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--groups', type=int, default=20000)
    parser.add_argument('--seed', type=int, default=20261028)
    args = parser.parse_args()
    report = generate(args.output, load_catalog(args.base, args.luxury), groups=args.groups,
                      seed=args.seed, sources=(args.base, args.luxury, args.reviews, Path(__file__), ROOT / 'tools/data/vehicles/lifestyle_traits.py'),
                      reviews=read_reviews(args.reviews))
    print(canonical({key: report[key] for key in ('catalog_count', 'profiles', 'partitions', 'tasks', 'unexposed_ids')}))


if __name__ == '__main__':
    main()
