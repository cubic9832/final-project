"""Add independent sports-model comparison exposure to the frozen population."""
import argparse
import csv
import hashlib
import json
import random
from collections import Counter, defaultdict
from dataclasses import asdict
from pathlib import Path

import numpy as np
import torch

from vehicle_matching.body_types import BODY_TYPES
from vehicle_matching.catalog import ROOT, read_catalog, save_catalog, catalog_fingerprint
from vehicle_matching.finance import Profile, assess
from vehicle_matching.partition_preference_population import digest
from vehicle_matching.preference_model import FEATURE_NAMES, PreferenceRanker, encode_preference
from vehicle_matching.recommendation_policy import POLICY, seating_status
from vehicle_matching.retrain_verified_catalog import teacher_keys
from vehicle_matching.train_preference_population import financial_group, independent_eligible, fit_population

ROLES = ('train', 'validation', 'test')


def financial_key(profile):
    names = ('monthly_income', 'monthly_expenses', 'existing_monthly_payment', 'liquid_assets', 'purchase_price_ceiling')
    return tuple(int(getattr(profile, name)) for name in names)


def split_for(key, seed):
    number = int(hashlib.sha256(json.dumps([seed, key]).encode()).hexdigest()[:12], 16) % 100
    return 0 if number < 70 else 1 if number < 85 else 2


def acceptable(profile, car, assumptions):
    if seating_status(profile, car) != 'match':
        return None
    cost = assess(profile, car, assumptions)
    if not cost['eligible']:
        return None
    if not independent_eligible(profile, car, cost):
        raise ValueError('Decimal financial audit disagrees')
    return cost


def generate(directory, source, supplement, per_model, seed, assumptions):
    if directory.exists():
        raise ValueError('Use a new generation directory')
    directory.mkdir(parents=True)
    old_cars = read_catalog(source / 'catalog.json')
    new_cars = read_catalog(supplement)
    cars = old_cars + new_cars
    if len({c.id for c in cars}) != len(cars):
        raise ValueError('Duplicate vehicle IDs')
    save_catalog(directory / 'catalog.json', cars)
    by_family = defaultdict(list)
    for index in range(len(old_cars), len(cars)):
        by_family[cars[index].brand, cars[index].model].append(index)
    held_out = {tuple(v) for v in json.loads((ROOT / 'data/households/synthetic/curated-current-v2-20261026/refinement_report.json').read_text(encoding='utf-8'))['held_out_models']}
    signatures, group_roles = set(), {}
    max_id = 0
    for code, role in enumerate(ROLES):
        with (source / f'{role}_profiles.jsonl').open(encoding='utf-8') as stream:
            for line in stream:
                record = json.loads(line); profile = Profile(**record['profile'])
                key = financial_key(profile)
                if group_roles.setdefault(key, code) != code:
                    raise ValueError('Existing financial groups cross splits')
                max_id = max(max_id, record['id'])
                signatures.add(json.dumps(asdict(profile), sort_keys=True))
    buckets = {role: {'features': [], 'targets': [], 'pairs': [], 'profile_ids': [], 'vehicle_indices': []} for role in ROLES}
    rng = random.Random(seed)
    counts, rejected = Counter(), Counter()
    next_id, group = max_id + 1, 0
    handles = {role: (directory / f'{role}_profiles.jsonl').open('w', encoding='utf-8') for role in ROLES}
    with (directory / 'sports_cases.csv').open('w', encoding='utf-8-sig', newline='') as output:
        names = ['profile_id', 'financial_group', 'split', 'anchor_brand', 'anchor_model', 'anchor_id', 'comparison_id', 'preferred_body_type', 'minimum_seats', 'monthly_income', 'monthly_expenses', 'existing_monthly_payment', 'liquid_assets', 'higher_id', 'lower_id']
        writer = csv.DictWriter(output, fieldnames=names); writer.writeheader()
        for family, indices in sorted(by_family.items()):
            accepted = 0
            attempts = 0
            while accepted < per_model:
                group += 1
                financial = financial_group(rng, group)
                # Generate all preferences before selecting a vehicle configuration.
                profiles = [Profile(**financial, preferred_body_type=rng.choice(('any', *BODY_TYPES, 'OTHER')),
                    body_importance=rng.choice((1, 3, 5)), preferred_fuel=rng.choice((None, 'GASOLINE', 'HYBRID', 'DIESEL', 'ELECTRIC', 'LPG')),
                    preferred_size=rng.choice(('any', 'small', 'medium', 'large')), minimum_seats=rng.choice((0, 2, 4, 5, 6, 7, 9)),
                    cost_importance=rng.choice((1, 3, 5)), space_importance=rng.choice((1, 3, 5)), fuel_importance=rng.choice((1, 3, 5)), seating_importance=rng.choice((1, 3, 5))) for _ in range(4)]
                for profile in profiles:
                    if accepted == per_model:
                        break
                    attempts += 1
                    if attempts > per_model * 1000:
                        raise ValueError(f'Insufficient independent eligible cases for {family}')
                    key = financial_key(profile)
                    code = group_roles.setdefault(key, split_for(key, seed)); role = ROLES[code]
                    signature = json.dumps(asdict(profile), sort_keys=True)
                    if signature in signatures:
                        rejected['duplicate-profile'] += 1; continue
                    anchor_index = rng.choice(indices); anchor = cars[anchor_index]
                    cost = acceptable(profile, anchor, assumptions)
                    if cost is None:
                        rejected['anchor-ineligible-or-seats-unverified'] += 1; continue
                    pair = None
                    for other_index in rng.sample(range(len(cars)), min(32, len(cars))):
                        other = cars[other_index]
                        if (other.brand, other.model) == family or (code != 2 and (other.brand, other.model) in held_out):
                            continue
                        other_cost = acceptable(profile, other, assumptions)
                        if other_cost is None:
                            continue
                        keys = teacher_keys(profile, [anchor, other], [cost, other_cost])
                        if keys[0] == keys[1]:
                            continue
                        pair = other_index, keys; break
                    if pair is None:
                        rejected['no-distinct-comparison'] += 1; continue
                    other_index, keys = pair
                    bucket = buckets[role]; start = len(bucket['features'])
                    better = 0 if keys[0] < keys[1] else 1
                    for local, index in enumerate((anchor_index, other_index)):
                        bucket['features'].append(encode_preference(profile, cars[index], assumptions))
                        bucket['targets'].append(.95 if local == better else .05)
                        bucket['profile_ids'].append(next_id); bucket['vehicle_indices'].append(index)
                    bucket['pairs'].append((start + better, start + 1 - better))
                    record = {'id': next_id, 'group': f'SPORT-G-{group}', 'split': role, 'profile': asdict(profile)}
                    handles[role].write(json.dumps(record, ensure_ascii=False) + '\n')
                    writer.writerow(dict(zip(names, [next_id, record['group'], role, *family, anchor.id, cars[other_index].id,
                        profile.preferred_body_type, profile.minimum_seats, profile.monthly_income, profile.monthly_expenses,
                        profile.existing_monthly_payment, profile.liquid_assets,
                        (anchor if better == 0 else cars[other_index]).id, (anchor if better == 1 else cars[other_index]).id], strict=True)))
                    signatures.add(signature); next_id += 1; accepted += 1
                    counts[f'{family[0]}|{family[1]}|{role}'] += 1
            print(json.dumps({'stage': 'sports-generated', 'model': family, 'cases': accepted, 'attempts': attempts}, ensure_ascii=False), flush=True)
    for handle in handles.values():
        handle.close()
    source_hashes, sizes = {}, {}
    for code, role in enumerate(ROLES):
        bucket = buckets[role]
        arrays = {key: np.asarray(value, dtype=np.float32 if key in ('features', 'targets') else np.int64) for key, value in bucket.items()}
        arrays['features'] = arrays['features'].reshape(-1, len(FEATURE_NAMES))
        arrays['pairs'] = arrays['pairs'].reshape(-1, 2)
        arrays['splits'] = np.full(len(arrays['features']), code, dtype=np.int8)
        np.savez_compressed(directory / f'sports_{role}_pairs.npz', **arrays)
        with np.load(source / f'{role}_pairs.npz') as saved:
            baseline = {key: saved[key].copy() for key in ('features', 'targets', 'pairs', 'profile_ids', 'vehicle_indices', 'splits')}
        # Existing body bits retain exact positions. New sports bits are zero for the old catalog.
        baseline['features'] = np.pad(baseline['features'], ((0, 0), (0, len(FEATURE_NAMES) - baseline['features'].shape[1])))
        offset = len(baseline['features'])
        joined = {key: np.concatenate([baseline[key], arrays[key] + offset if key == 'pairs' else arrays[key]]) for key in baseline}
        assert np.all(joined['profile_ids'][joined['pairs'][:, 0]] == joined['profile_ids'][joined['pairs'][:, 1]])
        np.savez_compressed(directory / f'{role}_pairs.npz', **joined)
        sizes[role] = {'new_cases': len(arrays['pairs']), 'new_feature_rows': len(arrays['features']), 'total_pairs': len(joined['pairs']), 'total_feature_rows': len(joined['features'])}
        for suffix in ('pairs.npz', 'profiles.jsonl'):
            path = source / f'{role}_{suffix}'; source_hashes[path.name] = digest(path)
    for family in by_family:
        assert sum(counts[f'{family[0]}|{family[1]}|{role}'] for role in ROLES) == per_model
    report = {'seed': seed, 'policy': POLICY, 'rows_per_model': per_model, 'model_families': len(by_family),
        'sports_cases': len(by_family) * per_model, 'counts': dict(counts), 'partitions': sizes,
        'source': str(source.resolve()), 'source_hashes': source_hashes, 'supplement_sha256': digest(supplement),
        'financial_group_leakage': 0, 'duplicate_profiles': 0, 'independent_decimal_violations': 0,
        'held_out_models_preserved_for_new_training_comparisons': sorted(held_out),
        'quantity_override': 'User explicitly requested 10000 independent accepted comparison exposures per new model; not forced wins or purchase labels.',
        'eligibility': 'Current cash and 12-month running deficit rules; required seats must be verified. Missing efficiency uses existing documented assumptions.',
        'evaluation_scope': 'Synthetic policy agreement. New models occur in training; this is unseen-financial-group evaluation, not unseen-new-model accuracy.'}
    (directory / 'generation_report.json').write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
    return report


def pair_accuracy(model, path):
    with np.load(path) as saved:
        x = saved['features']; pairs = saved['pairs']
    scores = []
    with torch.no_grad():
        for start in range(0, len(x), 32768):
            values = x[start:start + 32768, :len(model.mean)]
            scores.extend(model.net(torch.from_numpy(((values - model.mean) / model.scale).astype(np.float32))).flatten().numpy())
    values = np.asarray(scores)
    return {'pairs': len(pairs), 'accuracy': float(np.mean(values[pairs[:, 0]] > values[pairs[:, 1]]))}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--source', type=Path, required=True)
    parser.add_argument('--supplement', type=Path, required=True)
    parser.add_argument('--data', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--old-model', type=Path, required=True)
    parser.add_argument('--per-model', type=int, default=10000)
    parser.add_argument('--epochs', type=int, default=12)
    args = parser.parse_args()
    if args.output.exists() or args.per_model < 1:
        raise ValueError('Use a new checkpoint and positive row count')
    old = PreferenceRanker.load(args.old_model)
    report = generate(args.data, args.source, args.supplement, args.per_model, 20261028, old.assumptions)
    from vehicle_matching.train_curated_population import load_partitions
    x, y, pairs, splits = load_partitions(args.data)
    provenance = {'seed': 20261028, 'catalog_mode': 'verified-runtime-snapshot', 'catalog_sha256': catalog_fingerprint(args.data / 'catalog.json'),
        'policy': POLICY, 'data_dir': str(args.data.resolve()), 'source_model': str(args.old_model.resolve()),
        'generation_report_sha256': digest(args.data / 'generation_report.json'), 'sports_cases': report['sports_cases'], 'features': len(FEATURE_NAMES)}
    model, history = fit_population(x, y, pairs, splits, 20261028, args.epochs, args.output, provenance)
    save_catalog(args.output / 'catalog.json', read_catalog(args.data / 'catalog.json'))
    results = {}
    for name, path in [('sports', args.data / 'sports_test_pairs.npz'), ('baseline', args.source / 'test_pairs.npz')]:
        if name == 'baseline':
            with np.load(path) as source:
                adapted = {k: source[k] for k in ('features', 'pairs')}
            adapted['features'] = np.pad(adapted['features'], ((0, 0), (0, len(FEATURE_NAMES) - adapted['features'].shape[1])))
            path = args.data / 'baseline_test_pairs.npz'; np.savez_compressed(path, **adapted)
        results[name] = {'old': pair_accuracy(old, path), 'new': pair_accuracy(model, path)}
    result = {'history': history, 'generation': report, 'holdout': results,
        'serving': 'Trained candidate only; not activated and no database writes.'}
    (args.output / 'training_report.json').write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps({'stage': 'training-complete', 'holdout': results}), flush=True)


if __name__ == '__main__':
    main()
