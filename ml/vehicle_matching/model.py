"""Pairwise MLP with shared features and versioned, portable CPU artifacts."""
import hashlib
import json
from pathlib import Path

import numpy as np
import torch
from torch import nn

from vehicle_matching.features import FEATURE_NAMES, encode
from vehicle_matching.finance import Assumptions


def network():
    return nn.Sequential(nn.Linear(len(FEATURE_NAMES), 64), nn.ReLU(),
                         nn.Linear(64, 32), nn.ReLU(), nn.Linear(32, 1))


class PairRanker:
    def __init__(self, net, mean, scale, minimum, maximum, assumptions=Assumptions()):
        self.net = net.eval()
        self.mean, self.scale = np.asarray(mean), np.asarray(scale)
        self.minimum, self.maximum = np.asarray(minimum), np.asarray(maximum)
        self.assumptions = assumptions

    def predict(self, profile, vehicles):
        if not vehicles:
            return [], []
        features = np.stack([encode(profile, v, self.assumptions) for v in vehicles])
        values = ((features - self.mean) / self.scale).astype(np.float32)
        with torch.no_grad():
            scores = torch.sigmoid(self.net(torch.from_numpy(values)).flatten()).numpy().tolist()
        outside = np.any((features < self.minimum - 1e-5) | (features > self.maximum + 1e-5), axis=1)
        return scores, outside.tolist()

    def save(self, directory, provenance):
        directory = Path(directory)
        directory.mkdir(parents=True, exist_ok=True)
        weights = directory / 'model.pt'
        torch.save(self.net.state_dict(), weights)
        meta = {'schema': 'candidate-v2', 'features': list(FEATURE_NAMES), 'mean': self.mean.tolist(),
                'scale': self.scale.tolist(), 'minimum': self.minimum.tolist(), 'maximum': self.maximum.tolist(),
                'assumptions': self.assumptions.to_dict(), 'training': provenance,
                'weights_sha256': hashlib.sha256(weights.read_bytes()).hexdigest()}
        (directory / 'metadata.json').write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding='utf-8')

    @classmethod
    def load(cls, directory):
        directory = Path(directory)
        meta = json.loads((directory / 'metadata.json').read_text(encoding='utf-8'))
        if meta['schema'] != 'candidate-v2' or meta['features'] != list(FEATURE_NAMES):
            raise ValueError('Model/feature schema mismatch')
        if hashlib.sha256((directory / 'model.pt').read_bytes()).hexdigest() != meta['weights_sha256']:
            raise ValueError('Model checksum mismatch')
        net = network()
        net.load_state_dict(torch.load(directory / 'model.pt', map_location='cpu', weights_only=True))
        mean, scale = np.asarray(meta['mean']), np.asarray(meta['scale'])
        if mean.shape != (len(FEATURE_NAMES),) or scale.shape != mean.shape or not np.all(np.isfinite(scale)) or np.any(scale <= 0):
            raise ValueError('Invalid feature scaler')
        return cls(net, mean, scale, meta['minimum'], meta['maximum'], Assumptions(**meta['assumptions']))


def fit_pairs(features, targets, pairs, *, seed=42, epochs=60):
    if not pairs:
        raise ValueError('No training preferences')
    torch.manual_seed(seed)
    torch.set_num_threads(2)
    x = np.asarray(features, dtype=np.float32)
    mean, scale = x.mean(axis=0), x.std(axis=0)
    scale[scale < 1e-6] = 1
    tensor = torch.from_numpy(((x - mean) / scale).astype(np.float32))
    target = torch.tensor(targets, dtype=torch.float32)
    pair_tensor = torch.tensor(pairs, dtype=torch.long)
    net = network()
    optimizer = torch.optim.Adam(net.parameters(), lr=0.002)
    generator = torch.Generator().manual_seed(seed)
    history = []
    for epoch in range(epochs):
        net.train()
        losses = []
        for batch in torch.randperm(len(pairs), generator=generator).split(256):
            positive, negative = pair_tensor[batch].T
            pos, neg = net(tensor[positive]).flatten(), net(tensor[negative]).flatten()
            # Pairwise ordering plus a bounded teacher-scale anchor; no probability claim.
            loss = nn.functional.softplus(-(pos - neg)).mean()
            loss += 0.5 * ((torch.sigmoid(pos) - target[positive]).square().mean()
                           + (torch.sigmoid(neg) - target[negative]).square().mean())
            optimizer.zero_grad()
            loss.backward()
            optimizer.step()
            losses.append(loss.item())
        history.append({'epoch': epoch + 1, 'loss': float(np.mean(losses))})
    return PairRanker(net, mean, scale, x.min(axis=0), x.max(axis=0)), history
