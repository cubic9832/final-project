"""Train and evaluate evidence-backed choices; select checkpoints on validation only."""
import argparse
import copy
import json
from pathlib import Path
import time

import numpy as np
import torch
from torch import nn

from vehicle_matching.lifestyle_features import DATASET_SCHEMA, FEATURE_NAMES
from vehicle_matching.lifestyle_model import LifestyleRanker, digest, model_inputs, network


def read_split(data, role):
    with np.load(data / f'{role}_choices.npz', allow_pickle=False) as archive:
        arrays = {key: archive[key] for key in archive.files}
    if not len(arrays['labels']) or not np.isin(arrays['labels'], (0, 1)).all():
        raise ValueError('Empty or invalid labels')
    for key in ('a', 'b', 'weights', 'masks'):
        if arrays[key].shape != (len(arrays['labels']), len(FEATURE_NAMES)):
            raise ValueError('Invalid saved feature dimensions')
    return arrays


def evaluate(net, arrays):
    net.eval()
    probabilities = []
    with torch.inference_mode():
        for offset in range(0, len(arrays['labels']), 16384):
            batch = slice(offset, offset + 16384)
            a, b = [torch.from_numpy(model_inputs(arrays[key][batch], arrays['weights'][batch], arrays['masks'][batch])) for key in ('a', 'b')]
            probabilities.extend((net(a) - net(b)).sigmoid().flatten().tolist())
    p = np.clip(np.asarray(probabilities), 1e-7, 1 - 1e-7)
    y = arrays['labels']
    metrics = lambda selected: {'comparisons': int(selected.sum()),
        'accuracy': float(np.mean((p[selected] >= .5) == y[selected])),
        'log_loss': float(np.mean(-y[selected] * np.log(p[selected]) - (1 - y[selected]) * np.log1p(-p[selected]))),
        'brier_score': float(np.mean((p[selected] - y[selected])**2))} if selected.any() else {'comparisons': 0}
    return {'all': metrics(np.ones(len(y), dtype=bool)),
            'eligible_preference': metrics(arrays['financial_eligible'].astype(bool)),
            'taste_only': metrics(~arrays['financial_eligible'].astype(bool)),
            'photo_evidence': metrics(arrays['masks'][:, :2].any(axis=1)),
            'majority_baseline_accuracy': float(max(y.mean(), 1 - y.mean()))}


def train(data, output, *, epochs=12, batch_size=8192, seed=20261028):
    if output.exists():
        raise FileExistsError(output)
    if epochs < 1 or batch_size < 1:
        raise ValueError('Positive training settings required')
    report = json.loads((data / 'generation_report.json').read_text(encoding='utf-8'))
    audit = json.loads((data / 'saved_data_audit.json').read_text(encoding='utf-8'))
    if report['schema'] != DATASET_SCHEMA or report['feature_names'] != list(FEATURE_NAMES) or audit['status'] != 'passed' or audit['comparisons_checked'] != report['profiles']:
        raise ValueError('Unsupported or unaudited dataset')
    for name, expected in audit['sha256'].items():
        if digest(data / name) != expected:
            raise ValueError(f'Dataset checksum mismatch: {name}')
    if digest(data / 'vehicle_traits.json') != report['traits_sha256']:
        raise ValueError('Vehicle evidence checksum mismatch')
    torch.set_num_threads(2)
    torch.manual_seed(seed)
    rng = torch.Generator().manual_seed(seed)
    training, validation = read_split(data, 'train'), read_split(data, 'validation')
    first, second = [torch.from_numpy(model_inputs(training[key], training['weights'], training['masks'])) for key in ('a', 'b')]
    labels = torch.from_numpy(training['labels'].astype(np.float32))
    net = network()
    optimizer = torch.optim.Adam(net.parameters(), lr=.001)
    history, best, selected, state = [], float('inf'), 0, None
    for epoch in range(epochs):
        started = time.monotonic()
        net.train()
        total = 0.
        for batch in torch.randperm(len(labels), generator=rng).split(batch_size):
            logits = (net(first[batch]) - net(second[batch])).flatten()
            loss = nn.functional.binary_cross_entropy_with_logits(logits, labels[batch])
            optimizer.zero_grad()
            loss.backward()
            optimizer.step()
            total += loss.item() * len(batch)
        metrics = evaluate(net, validation)
        row = {'epoch': epoch + 1, 'training_log_loss': total / len(labels),
               'validation': metrics, 'seconds': round(time.monotonic() - started, 2)}
        history.append(row)
        print(json.dumps(row), flush=True)
        if metrics['all']['log_loss'] < best:
            best, selected, state = metrics['all']['log_loss'], epoch + 1, copy.deepcopy(net.state_dict())
    net.load_state_dict(state)
    output.mkdir(parents=True)
    for name in ('catalog.json', 'vehicle_traits.json'):
        (output / name).write_bytes((data / name).read_bytes())
    provenance = {'data_dir': str(data.resolve()), 'profiles': report['profiles'], 'selected_epoch': selected,
        'seed': seed, 'epochs': epochs, 'batch_size': batch_size, 'objective': 'BCE(score(A)-score(B), sampled_choice_A)',
        'catalog_sha256': digest(output / 'catalog.json'), 'traits_sha256': digest(output / 'vehicle_traits.json'),
        'generation_report_sha256': digest(data / 'generation_report.json'),
        'audit_sha256': digest(data / 'saved_data_audit.json'), 'trainer_sha256': digest(Path(__file__)),
        'torch_version': torch.__version__, 'evaluation_scope': 'Synthetic choices, unseen financial groups; not real customer preference accuracy'}
    ranker = LifestyleRanker(net)
    ranker.save(output, provenance)
    # Held-out data is opened only after validation checkpoint selection and reload.
    saved = LifestyleRanker.load(output)
    test = read_split(data, 'test')
    results = {'selected_epoch': selected, 'history': history, 'test': evaluate(saved.net, test),
               'catalog_count': report['catalog_count'], 'trait_coverage': report['trait_coverage'],
               'limitations': report['limitations']}
    (output / 'training_report.json').write_text(json.dumps(results, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'stage': 'saved-model-test', 'output': str(output), 'test': results['test']}), flush=True)
    return results


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--data', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--epochs', type=int, default=12)
    args = parser.parse_args()
    train(args.data, args.output, epochs=args.epochs)


if __name__ == '__main__':
    main()
