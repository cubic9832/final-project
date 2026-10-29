"""Shared-score pair model: unknown dimensions are masked on both candidates."""
import hashlib
import json
from pathlib import Path

import numpy as np
import torch
from torch import nn

from vehicle_matching.finance import Assumptions
from vehicle_matching.lifestyle_features import FEATURE_NAMES

SCHEMA = 'lifestyle-pair-v1'
INPUT_NAMES = tuple(f'{kind}_{name}' for kind in ('weighted', 'weight', 'known') for name in FEATURE_NAMES)


def network():
    return nn.Sequential(nn.Linear(len(INPUT_NAMES), 64), nn.ReLU(), nn.Linear(64, 32), nn.ReLU(), nn.Linear(32, 1))


def model_inputs(features, weights, masks):
    features, weights, masks = (np.asarray(value, dtype=np.float32) for value in (features, weights, masks))
    if features.ndim != 2 or features.shape[1] != len(FEATURE_NAMES) or weights.shape != features.shape or masks.shape != features.shape:
        raise ValueError('Lifestyle feature shape mismatch')
    if any(not np.isfinite(value).all() for value in (features, weights, masks)) or np.any(weights < 0) or not np.isin(masks, (0, 1)).all():
        raise ValueError('Invalid lifestyle values')
    normalized = weights / np.maximum(weights.sum(axis=1, keepdims=True), 1e-12)
    return np.concatenate((features * masks * normalized, normalized * masks, masks), axis=1)


class LifestyleRanker:
    schema = SCHEMA

    def __init__(self, net):
        self.net = net.eval()
        self.assumptions = Assumptions()
        self.mean = np.zeros(len(INPUT_NAMES), dtype=np.float32)

    def pair_logits(self, a, b, weights, masks):
        first, second = (model_inputs(value, weights, masks) for value in (a, b))
        with torch.inference_mode():
            return np.concatenate([(self.net(torch.from_numpy(first[i:i + 16384])) - self.net(torch.from_numpy(second[i:i + 16384]))).flatten().numpy()
                                   for i in range(0, len(first), 16384)]) if len(first) else np.empty(0, dtype=np.float32)

    def save(self, output, provenance):
        torch.save(self.net.state_dict(), output / 'model.pt')
        metadata = {'schema': SCHEMA, 'features': list(INPUT_NAMES), 'pair_features': list(FEATURE_NAMES),
                    'training': provenance, 'weights_sha256': digest(output / 'model.pt')}
        (output / 'metadata.json').write_text(json.dumps(metadata, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')

    @classmethod
    def load(cls, output):
        torch.set_num_threads(2)
        output = Path(output)
        metadata = json.loads((output / 'metadata.json').read_text(encoding='utf-8'))
        if metadata['schema'] != SCHEMA or metadata['features'] != list(INPUT_NAMES) or metadata['pair_features'] != list(FEATURE_NAMES):
            raise ValueError('Lifestyle schema mismatch')
        if digest(output / 'model.pt') != metadata['weights_sha256']:
            raise ValueError('Lifestyle model checksum mismatch')
        net = network()
        net.load_state_dict(torch.load(output / 'model.pt', map_location='cpu', weights_only=True))
        return cls(net)


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()
