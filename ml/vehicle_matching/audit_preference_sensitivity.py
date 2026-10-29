"""Hold finances/candidates fixed and intervene on one preference at a time."""
import argparse
from collections import defaultdict
from dataclasses import asdict, replace
import hashlib
import json
from pathlib import Path
import random

import numpy as np
import torch

from vehicle_matching.api import load_service
from vehicle_matching.body_types import BODY_TYPES
from vehicle_matching.catalog import FUELS
from vehicle_matching.finance import Profile, assess
from vehicle_matching.preferences import integrated_score


AXES = {
    'fuel': ('preferred_fuel', 'fuel_importance', FUELS),
    'body': ('preferred_body_type', 'body_importance', BODY_TYPES),
    'space': ('preferred_size', 'space_importance', ('small', 'medium', 'large')),
    'seating': ('minimum_seats', 'seating_importance', (2, 5, 7, 9)),
}


def order(cars, scores):
    chosen, seen = [], set()
    for i in sorted(range(len(cars)), key=lambda i: (-float(scores[i]), cars[i].id)):
        key = (cars[i].brand, cars[i].model)
        if key not in seen:
            seen.add(key)
            chosen.append(i)
        if len(chosen) == 3:
            break
    return chosen


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--model', type=Path, required=True)
    parser.add_argument('--data', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--per-origin', type=int, default=100)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=False)
    torch.set_num_threads(2)
    service = load_service(args.model)
    source = args.data / 'test_profiles.jsonl'
    origins = defaultdict(list)
    for line in source.read_text(encoding='utf-8').splitlines():
        row = json.loads(line)
        origins[row['origin']].append(row)
    rng, used, selected = random.Random(20261028), set(), []
    for origin, records in sorted(origins.items()):
        rng.shuffle(records)
        count = 0
        for row in records:
            if row['group'] in used:
                continue
            selected.append(row)
            used.add(row['group'])
            count += 1
            if count == args.per_origin:
                break
    results, manifests = [], []
    for number, record in enumerate(selected, 1):
        base = replace(Profile(**record['profile']), preferred_fuel=None, preferred_body_type='any',
                       preferred_size='any', minimum_seats=0, cost_importance=3,
                       fuel_importance=3, body_importance=3, space_importance=3, seating_importance=3,
                       purpose='commute', financing_mode='recommendation', down_payment=0, months=0, annual_rate=0)
        eligible = [(v, assess(base, v, service.ranker.assumptions)) for v in service.vehicles]
        eligible = [(v, c) for v, c in eligible if c['eligible']]
        cars, costs = [v for v, _ in eligible], [c for _, c in eligible]
        manifests.append({'id': record['id'], 'group': record['group'], 'origin': record['origin'],
                          'neutral_profile': asdict(base), 'candidate_ids': [v.id for v in cars]})
        if not cars:
            continue
        raw_base = service.ranker.ranking_scores(base, cars)
        bounded_base, _ = service.ranker.predict(base, cars)
        baselines = {'raw': order(cars, raw_base), 'sigmoid': order(cars, bounded_base)}
        for axis, (field, weight, values) in AXES.items():
            for value in values:
                high = replace(base, **{field: value, weight: 5})
                low = replace(high, **{weight: 1})
                # Preferences must not alter the financial candidate set or costs.
                assert all(assess(high, v, service.ranker.assumptions) == c for v, c in eligible)
                raw = service.ranker.ranking_scores(high, cars)
                bounded, outside = service.ranker.predict(high, cars)
                raw_low = service.ranker.ranking_scores(low, cars)
                components = [next(p['score'] for p in integrated_score(high, v, c, .5)['components'] if p['key'] == axis)
                              for v, c in eligible]
                varying = max(components) - min(components) > 1e-8
                models = lambda indices: [(cars[i].brand, cars[i].model) for i in indices]
                mean = lambda indices: float(np.mean([components[i] for i in indices]))
                raw_order = order(cars, raw)
                low_order = order(cars, raw_low)
                for method, scores in (('raw', raw), ('sigmoid', bounded)):
                    after = order(cars, scores)
                    before = baselines[method]
                    results.append({'id': record['id'], 'group': record['group'], 'axis': axis, 'value': value,
                                    'method': method, 'discriminating_candidates': varying,
                                    'full_match_available': max(components) >= 100 - 1e-8,
                                    'model_order_changed': models(before) != models(after),
                                    'model_set_changed': set(models(before)) != set(models(after)),
                                    'target_score_before': mean(before), 'target_score_after': mean(after),
                                    'target_score_delta': mean(after) - mean(before),
                                    'full_match_fraction_after': float(np.mean([components[i] >= 100 - 1e-8 for i in after])),
                                    'weight_1_to_5_delta': mean(raw_order) - mean(low_order) if method == 'raw' else None,
                                    'raw_vs_sigmoid_order_differs': models(raw_order) != models(order(cars, bounded)),
                                    'exact_endpoint_fraction': sum(s in (0., 1.) for s in bounded) / len(bounded),
                                    'outside_top3': sum(outside[i] for i in after),
                                    'before': [{'model': cars[i].model, 'id': cars[i].id, 'target_score': components[i]} for i in before],
                                    'after': [{'model': cars[i].model, 'id': cars[i].id, 'target_score': components[i], 'raw': raw[i], 'sigmoid': bounded[i]} for i in after]})
        if number % 25 == 0:
            print(json.dumps({'completed_profiles': number, 'total': len(selected)}), flush=True)
    def summary(rows):
        valid = [r for r in rows if r['discriminating_candidates']]
        return {'comparisons': len(rows), 'discriminating_comparisons': len(valid),
                'model_order_changed': sum(r['model_order_changed'] for r in rows),
                'model_set_changed': sum(r['model_set_changed'] for r in rows),
                'target_improved': sum(r['target_score_delta'] > 1e-8 for r in valid),
                'target_unchanged': sum(abs(r['target_score_delta']) <= 1e-8 for r in valid),
                'target_worsened': sum(r['target_score_delta'] < -1e-8 for r in valid),
                'mean_target_delta_discriminating': float(np.mean([r['target_score_delta'] for r in valid])) if valid else None,
                'weight_increase_worsened': sum(r['weight_1_to_5_delta'] is not None and r['weight_1_to_5_delta'] < -1e-8 for r in valid),
                'weight_increase_improved': sum(r['weight_1_to_5_delta'] is not None and r['weight_1_to_5_delta'] > 1e-8 for r in valid),
                'raw_vs_sigmoid_order_differs': sum(r['raw_vs_sigmoid_order_differs'] for r in rows)}
    digest = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
    report = {'profiles': len(selected), 'profiles_with_candidates': sum(bool(r['candidate_ids']) for r in manifests),
              'seed': 20261028, 'model': str(args.model.resolve()), 'test_profiles_sha256': digest(source),
              'model_hashes': {n: digest(args.model / n) for n in ('model.pt', 'metadata.json', 'catalog.json')},
              'catalog_sha256': hashlib.sha256(json.dumps([asdict(v) for v in service.vehicles], sort_keys=True).encode()).hexdigest(),
              'catalog_source': 'local snapshot plus specification updates; current working tree; no live DB',
              'design': 'Neutral other preferences; cost importance 3; change one preference to weight 5. Compare standalone ML top3, same finances/candidate IDs; distinct models.',
              'metric': 'Mean target preference component at top3, 0-100. Diagnostic rules never enter ML-only ranking. Repeated interventions are not independent users.',
              'summary': {m: summary([r for r in results if r['method'] == m]) for m in ('raw', 'sigmoid')},
              'by_axis': {a: {m: summary([r for r in results if r['axis'] == a and r['method'] == m]) for m in ('raw', 'sigmoid')} for a in AXES},
              'by_value_raw': {a: {str(v): summary([r for r in results if r['axis'] == a and r['value'] == v and r['method'] == 'raw']) for v in config[2]} for a, config in AXES.items()},
              'production_changed': False}
    for name, data in (('report.json', report), ('comparisons.json', results), ('sample_manifest.json', manifests)):
        (args.output / name).write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps(report['summary'], indent=2), flush=True)
    print(json.dumps(report['by_axis'], indent=2), flush=True)


if __name__ == '__main__':
    main()
