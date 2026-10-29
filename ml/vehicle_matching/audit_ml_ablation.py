"""Paired offline rule-only versus current serving-ML audit; no policy changes."""
import argparse
from collections import Counter, defaultdict
from dataclasses import asdict
import hashlib
import json
import math
from pathlib import Path
import random

import numpy as np
import torch

from vehicle_matching.api import load_service
from vehicle_matching.finance import Profile
from vehicle_matching.service import CandidateService


class AuditedRanker:
    def __init__(self, ranker, neutral=False):
        self.ranker = ranker
        self.assumptions = ranker.assumptions
        self.neutral = neutral
        self.saturated = self.scored = 0

    def predict(self, profile, vehicles):
        scores, outside = self.ranker.predict(profile, vehicles)
        self.scored += len(scores)
        self.saturated += sum(value == 1.0 or value == 0.0 for value in scores)
        return ([.5] * len(scores) if self.neutral else scores), outside


def rule_score(row):
    parts = [x for x in row['integratedScore']['components'] if x['key'] != 'model']
    return sum(x['score'] * x['weight'] for x in parts) / sum(x['weight'] for x in parts)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--model', type=Path, required=True)
    parser.add_argument('--data', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--per-origin', type=int, default=300)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=False)
    torch.set_num_threads(2)
    service = load_service(args.model)
    actual = AuditedRanker(service.ranker)
    neutral = AuditedRanker(service.ranker, neutral=True)
    services = [CandidateService(r, service.vehicles) for r in (neutral, actual)]
    origins = defaultdict(list)
    source = args.data / 'test_profiles.jsonl'
    for line in source.read_text(encoding='utf-8').splitlines():
        record = json.loads(line)
        origins[record['origin']].append(record)
    rng = random.Random(20261027)
    selected, groups = [], set()
    for origin, records in sorted(origins.items()):
        rng.shuffle(records)
        count = 0
        for record in records:
            if record['group'] in groups:
                continue
            selected.append(record)
            groups.add(record['group'])
            count += 1
            if count == args.per_origin:
                break
    cases, examples = [], []
    for index, record in enumerate(selected):
        profile = Profile(**record['profile'])
        before, after = [s.recommend(profile, k=3)['recommendations'] for s in services]
        assert len(before) == len(after)
        keys = lambda rows: [(r['vehicle']['brand'], r['vehicle']['model']) for r in rows]
        ids = lambda rows: [r['vehicle']['id'] for r in rows]
        losses, high_losses = [], []
        dominated = 0
        for rank, (a, b) in enumerate(zip(before, after), 1):
            ap = {p['key']: p for p in a['integratedScore']['components'] if p['key'] != 'model'}
            bp = {p['key']: p for p in b['integratedScore']['components'] if p['key'] != 'model'}
            assert ap.keys() == bp.keys()
            deltas = [bp[k]['score'] - ap[k]['score'] for k in ap]
            dominated += int(all(d <= 1e-8 for d in deltas) and any(d < -1e-8 for d in deltas))
            for key in ap.keys() - {'cost'}:
                if bp[key]['score'] < ap[key]['score'] - 1e-8:
                    losses.append({'rank': rank, 'condition': key, 'before': ap[key]['score'], 'after': bp[key]['score']})
                    if ap[key]['weight'] >= 4 and ap[key]['score'] >= 100 - 1e-8:
                        high_losses.append(losses[-1])
        dcg = lambda rows: sum(rule_score(r) / math.log2(i + 2) for i, r in enumerate(rows))
        gap = dcg(after) - dcg(before)
        # Rule-only ordering maximizes this same-rule discounted gain, with one trim/model.
        assert gap <= 1e-7
        case = {'id': record['id'], 'group': record['group'], 'origin': record['origin'],
                'recommendations': len(before), 'vehicle_order_changed': ids(before) != ids(after),
                'model_order_changed': keys(before) != keys(after),
                'model_set_changed': set(keys(before)) != set(keys(after)),
                'rule_dcg_delta': gap,
                'top1_rule_delta': rule_score(after[0]) - rule_score(before[0]) if before else 0,
                'preference_losses': losses, 'high_importance_full_losses': high_losses,
                'dominated_rank_slots': dominated,
                'outside_training_top3': sum(r['outsideTrainingRange'] for r in after),
                'before': [{'id': r['vehicle']['id'], 'model': r['vehicle']['model'], 'rule_score': rule_score(r)} for r in before],
                'after': [{'id': r['vehicle']['id'], 'model': r['vehicle']['model'], 'rule_score': rule_score(r)} for r in after]}
        cases.append(case)
        if case['vehicle_order_changed']:
            examples.append({'case': case, 'profile': asdict(profile), 'rule_only': before, 'with_ml': after})
        if (index + 1) % 100 == 0:
            print(json.dumps({'completed': index + 1, 'total': len(selected)}), flush=True)
    def summarize(rows):
        nonempty = [r for r in rows if r['recommendations']]
        return {'profiles': len(rows), 'with_candidates': len(nonempty),
                **{k: sum(r[k] for r in rows) for k in ('vehicle_order_changed', 'model_order_changed', 'model_set_changed', 'dominated_rank_slots', 'outside_training_top3')},
                'profiles_with_preference_loss': sum(bool(r['preference_losses']) for r in rows),
                'profiles_with_high_importance_full_loss': sum(bool(r['high_importance_full_losses']) for r in rows),
                'top1_rule_worse': sum(r['top1_rule_delta'] < -1e-8 for r in rows),
                'top1_rule_better': sum(r['top1_rule_delta'] > 1e-8 for r in rows),
                'rule_dcg_worse': sum(r['rule_dcg_delta'] < -1e-8 for r in rows),
                'mean_top1_rule_delta': float(np.mean([r['top1_rule_delta'] for r in nonempty])) if nonempty else None,
                'worst_top1_rule_delta': min((r['top1_rule_delta'] for r in rows), default=0)}
    fingerprint = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
    report = {'model': str(args.model.resolve()), 'seed': 20261027,
              'model_hashes': {name: fingerprint(args.model / name) for name in ('model.pt', 'metadata.json', 'catalog.json')},
              'test_profiles_sha256': fingerprint(source), 'catalog_count': len(service.vehicles),
              'loaded_catalog_sha256': hashlib.sha256(json.dumps([asdict(v) for v in service.vehicles], sort_keys=True).encode()).hexdigest(),
              'catalog_source': 'local load_service snapshot plus local specification updates; not live managed database',
              'baseline': 'same service with constant ML=0.5; equivalent rule-only order because denominator is constant per profile',
              'summary': summarize(cases), 'by_origin': {o: summarize([r for r in cases if r['origin'] == o]) for o in origins},
              'candidate_scores': actual.scored, 'exact_sigmoid_endpoint_scores': actual.saturated,
              'interpretation': 'Rule agreement only. Rule-only wins this metric by construction; no real-user satisfaction inference.',
              'policy_changed': False}
    for name, value in (('report.json', report), ('cases.json', cases), ('changed_examples.json', examples)):
        (args.output / name).write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps(report, ensure_ascii=False, indent=2), flush=True)


if __name__ == '__main__':
    main()
