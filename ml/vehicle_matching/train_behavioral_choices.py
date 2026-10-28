"""Train on stochastic pair choices; frozen serving checkpoints are never overwritten."""
import argparse
import copy
import json
import math
from pathlib import Path
import random
import sys
import time

import numpy as np
import torch
from torch import nn

from vehicle_matching.catalog import read_catalog, save_catalog, catalog_fingerprint
from vehicle_matching.finance import Assumptions, Profile, assess
from vehicle_matching.preference_model import FEATURE_NAMES, PreferenceRanker, preference_network
from vehicle_matching.preferences import preference_assessment
from vehicle_matching.recommendation_policy import ranking_key
from tools.data.households.generate_behavioral_choices import sha256, write_json


def load_shard(data, shard, role):
    with np.load(data / shard['directory'] / f'{role}_choices.npz', allow_pickle=False) as arrays:
        return arrays['features'], arrays['comparisons'], arrays['labels'].astype(np.float32)


def normalization(data, manifest):
    total = 0
    sums = np.zeros(len(FEATURE_NAMES), dtype=np.float64)
    squares = np.zeros_like(sums)
    minimum = np.full_like(sums, np.inf)
    maximum = np.full_like(sums, -np.inf)
    for shard in manifest['shards']:
        x, _, _ = load_shard(data, shard, 'train')
        if not len(x):
            continue
        values = x.astype(np.float64)
        total += len(x)
        sums += values.sum(axis=0)
        squares += np.square(values).sum(axis=0)
        minimum = np.minimum(minimum, x.min(axis=0))
        maximum = np.maximum(maximum, x.max(axis=0))
    if not total:
        raise ValueError('No training features')
    mean = sums / total
    scale = np.sqrt(np.maximum(0, squares / total - mean**2))
    scale[scale < 1e-6] = 1
    return tuple(value.astype(np.float32) for value in (mean, scale, minimum, maximum))


def evaluate(net, data, manifest, role, mean, scale, batch_size=16384):
    net.eval()
    count, loss, brier, correct = 0, 0., 0., 0
    with torch.no_grad():
        for shard in manifest['shards']:
            x, pairs, labels = load_shard(data, shard, role)
            if not len(pairs):
                continue
            values = torch.from_numpy(((x[:, :len(mean)] - mean) / scale).astype(np.float32))
            scores = torch.cat([net(batch).flatten() for batch in values.split(batch_size)])
            for start in range(0, len(pairs), batch_size):
                selected = pairs[start:start + batch_size]
                target = torch.from_numpy(labels[start:start + batch_size])
                difference = scores[selected[:, 0]] - scores[selected[:, 1]]
                probabilities = difference.sigmoid()
                loss += nn.functional.binary_cross_entropy_with_logits(difference, target, reduction='sum').item()
                brier += (probabilities - target).square().sum().item()
                correct += int(((difference >= 0) == (target >= .5)).sum())
                count += len(target)
    if not count:
        raise ValueError(f'Empty {role} comparisons')
    return {'comparisons': count, 'log_loss': loss / count, 'brier_score': brier / count, 'accuracy': correct / count}


def fit(data, manifest, net, stats, *, epochs, batch_size, seed, learning_rate=.001):
    mean, scale, _, _ = stats
    optimizer = torch.optim.Adam(net.parameters(), lr=learning_rate)
    generator = torch.Generator().manual_seed(seed)
    rng = random.Random(seed)
    history, best, best_state, selected_epoch = [], math.inf, None, 0
    for epoch in range(epochs):
        started = time.monotonic()
        net.train()
        order = list(manifest['shards'])
        rng.shuffle(order)
        loss_sum, count = 0., 0
        for shard in order:
            x, pairs, labels = load_shard(data, shard, 'train')
            if not len(pairs):
                continue
            values = torch.from_numpy(((x - mean) / scale).astype(np.float32))
            pair_tensor = torch.from_numpy(pairs)
            target_tensor = torch.from_numpy(labels)
            for selected in torch.randperm(len(pairs), generator=generator).split(batch_size):
                first, second = pair_tensor[selected].T
                difference = net(values[first]).flatten() - net(values[second]).flatten()
                loss = nn.functional.binary_cross_entropy_with_logits(difference, target_tensor[selected])
                optimizer.zero_grad()
                loss.backward()
                optimizer.step()
                loss_sum += loss.item() * len(selected)
                count += len(selected)
        validation = evaluate(net, data, manifest, 'validation', mean, scale, batch_size)
        row = {'epoch': epoch + 1, 'training_log_loss': loss_sum / count,
               'validation': validation, 'seconds': round(time.monotonic() - started, 2)}
        history.append(row)
        print(json.dumps(row), flush=True)
        if validation['log_loss'] < best:
            best = validation['log_loss']
            selected_epoch = epoch + 1
            best_state = copy.deepcopy(net.state_dict())
    net.load_state_dict(best_state)
    return history, selected_epoch


def evaluate_rules(data, manifest):
    """Deterministic rules have accuracy only; their outputs are not probabilities."""
    vehicles = read_catalog(data / 'catalog.json')
    policy_correct, economy_correct, count = 0., 0., 0
    for shard in manifest['shards']:
        directory = data / shard['directory']
        with (directory / 'test_profiles.jsonl').open(encoding='utf-8') as stream:
            records = [json.loads(line) for line in stream]
        profiles = {row['id']: Profile(**row['profile']) for row in records}
        with np.load(directory / 'test_choices.npz', allow_pickle=False) as arrays:
            profile_ids, vehicle_indices = arrays['profile_ids'], arrays['vehicle_indices']
            pairs, labels = arrays['comparisons'], arrays['labels']
        keys, economy = [], []
        for profile_id, vehicle_index in zip(profile_ids, vehicle_indices):
            profile, vehicle = profiles[int(profile_id)], vehicles[int(vehicle_index)]
            cost = assess(profile, vehicle)
            score = preference_assessment(profile, vehicle, cost)['components'][0]['score']
            economy.append(score)
            keys.append(ranking_key(profile, vehicle, 0)[:-2] + (-score,))
        for (first, second), label in zip(pairs, labels):
            policy_prediction = .5 if keys[first] == keys[second] else float(keys[first] < keys[second])
            cost_prediction = .5 if economy[first] == economy[second] else float(economy[first] > economy[second])
            policy_correct += .5 if policy_prediction == .5 else float(policy_prediction == label)
            economy_correct += .5 if cost_prediction == .5 else float(cost_prediction == label)
            count += 1
    return {'preference_priority_cost_tiebreak': {'comparisons': count, 'accuracy': policy_correct / count},
            'cost_only': {'comparisons': count, 'accuracy': economy_correct / count}}


def train(data, output, *, epochs=12, batch_size=16384, seed=20261028, threads=4, old_model=None):
    if epochs <= 0 or batch_size <= 0 or threads <= 0:
        raise ValueError('Positive epochs, batch size and threads required')
    if output.exists():
        raise FileExistsError(output)
    manifest = json.loads((data / 'manifest.json').read_text(encoding='utf-8'))
    audit = json.loads((data / 'population_audit.json').read_text(encoding='utf-8'))
    if audit['status'] != 'passed' or audit['profiles'] != manifest['profiles_requested']:
        raise ValueError('Population audit is incomplete')
    if sha256(data / 'catalog.json') != manifest['catalog_sha256']:
        raise ValueError('Catalog checksum mismatch')
    for shard in manifest['shards']:
        if sha256(data / shard['directory'] / 'generation_report.json') != shard['report_sha256']:
            raise ValueError('Shard report checksum mismatch')
        report = json.loads((data / shard['directory'] / 'generation_report.json').read_text(encoding='utf-8'))
        for role in ('train', 'validation', 'test'):
            name = f'{role}_choices.npz'
            if sha256(data / shard['directory'] / name) != report['files_sha256'][name]:
                raise ValueError('Training data checksum mismatch')
    output.mkdir(parents=True)
    torch.set_num_threads(threads)
    torch.manual_seed(seed)
    stats = normalization(data, manifest)
    mean, scale, minimum, maximum = stats
    net = preference_network(len(mean))
    history, epoch = fit(data, manifest, net, stats, epochs=epochs, batch_size=batch_size, seed=seed)
    provenance = {'objective': 'BCEWithLogits(score_A-score_B, sampled_choice_A)', 'seed': seed,
                  'selected_epoch': epoch, 'data_dir': str(data.resolve()),
                  'dataset_manifest_sha256': sha256(data / 'manifest.json'),
                  'population_audit_sha256': sha256(data / 'population_audit.json'),
                  'catalog_mode': 'verified-runtime-snapshot', 'catalog_sha256': catalog_fingerprint(data / 'catalog.json'),
                  'ranking_policy': 'required-eligibility-then-ml-only-experimental',
                  'evaluation_scope': 'synthetic pair choices on unseen financial groups; not actual purchase probabilities',
                  'trainer_sha256': sha256(__file__), 'epochs': epochs, 'batch_size': batch_size}
    provenance['runtime'] = {'python': sys.version, 'torch': torch.__version__, 'numpy': np.__version__,
                             'device': 'cpu', 'torch_threads': threads, 'learning_rate': .001}
    ranker = PreferenceRanker(net, mean, scale, minimum, maximum, Assumptions())
    ranker.save(output, provenance)
    save_catalog(output / 'catalog.json', read_catalog(data / 'catalog.json'))
    # Reload the saved checkpoint before the held-out evaluation.
    saved = PreferenceRanker.load(output)
    results = {'mlp': evaluate(saved.net, data, manifest, 'test', saved.mean, saved.scale, batch_size)}
    print(json.dumps({'stage': 'mlp-test', **results['mlp']}), flush=True)
    torch.manual_seed(seed)
    linear = nn.Linear(len(mean), 1)
    linear_history, linear_epoch = fit(data, manifest, linear, stats, epochs=min(epochs, 8), batch_size=batch_size, seed=seed)
    results['linear'] = evaluate(linear, data, manifest, 'test', mean, scale, batch_size)
    torch.save({'state_dict': linear.state_dict(), 'mean': mean.tolist(), 'scale': scale.tolist(),
                'selected_epoch': linear_epoch}, output / 'linear_baseline.pt')
    if old_model:
        old = PreferenceRanker.load(old_model)
        results['previous_checkpoint_uncalibrated'] = evaluate(old.net, data, manifest, 'test', old.mean, old.scale, batch_size)
    results.update(evaluate_rules(data, manifest))
    comparisons = manifest['partitions']['test']['comparisons']
    results['coin_flip'] = {'comparisons': comparisons, 'log_loss': math.log(2), 'brier_score': .25, 'expected_accuracy': .5}
    report = {'training': provenance, 'partitions': manifest['partitions'], 'history': history,
              'linear_history': linear_history, 'test': results,
              'limitations': ['Synthetic behavioral assumptions only.', 'Hidden behavioral coefficients are not model inputs.',
                              'Current hhc service and checkpoint are unchanged.', 'No live serving activation.']}
    write_json(output / 'training_report.json', report)
    print(json.dumps({'stage': 'training-complete', 'output': str(output.resolve()), 'test': results}), flush=True)
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--data', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--epochs', type=int, default=12)
    parser.add_argument('--batch-size', type=int, default=16384)
    parser.add_argument('--threads', type=int, default=4)
    parser.add_argument('--seed', type=int, default=20261028)
    parser.add_argument('--old-model', type=Path)
    args = parser.parse_args()
    train(args.data, args.output, epochs=args.epochs, batch_size=args.batch_size,
          seed=args.seed, threads=args.threads, old_model=args.old_model)


if __name__ == '__main__':
    main()
