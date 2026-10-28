"""Learning choice direction and retaining exact accepted profile counts."""
import contextlib
import io
import json
from pathlib import Path
import tempfile
import unittest

import numpy as np
import torch
from torch import nn

from vehicle_matching.catalog import ROOT, Vehicle
from vehicle_matching.preference_model import FEATURE_NAMES
from vehicle_matching.train_behavioral_choices import evaluate, fit, normalization
from tools.data.households.generate_behavioral_choices import generate, sha256
from tools.data.households.generate_behavioral_population import audit_population


class BehavioralTrainingTests(unittest.TestCase):
    def test_pair_training_learns_direction_on_unseen_examples(self):
        (ROOT / 'tmp').mkdir(exist_ok=True)
        with tempfile.TemporaryDirectory(dir=ROOT / 'tmp') as folder:
            data = Path(folder)
            shard = data / 'shard-0000'
            shard.mkdir()
            rng = np.random.default_rng(19)
            for role, count in (('train', 4000), ('validation', 1000), ('test', 1000)):
                x = np.zeros((count * 2, len(FEATURE_NAMES)), dtype=np.float32)
                x[:, 0] = rng.normal(size=len(x))
                pairs = np.arange(count * 2).reshape(-1, 2)
                probability = 1 / (1 + np.exp(-3 * (x[pairs[:, 0], 0] - x[pairs[:, 1], 0])))
                labels = (rng.random(count) < probability).astype(np.int8)
                np.savez(shard / f'{role}_choices.npz', features=x, comparisons=pairs, labels=labels)
            manifest = {'shards': [{'directory': shard.name}]}
            torch.set_num_threads(1)
            net = nn.Linear(len(FEATURE_NAMES), 1)
            nn.init.zeros_(net.weight)
            nn.init.zeros_(net.bias)
            stats = normalization(data, manifest)
            with contextlib.redirect_stdout(io.StringIO()):
                fit(data, manifest, net, stats, epochs=8, batch_size=128, seed=19, learning_rate=.02)
            result = evaluate(net, data, manifest, 'test', *stats[:2])
            self.assertLess(result['log_loss'], .4)
            self.assertGreater(result['accuracy'], .8)

    def test_target_count_and_cross_shard_group_isolation(self):
        cars = [Vehicle(str(index), 'Brand', f'Model {index}', 'Base', '2026',
                        10000000 + index * 1000000, 'GASOLINE', 12, 'https://example.com',
                        '2026-10-28', seats=5, length_mm=4500, body_type='SUV') for index in range(4)]
        (ROOT / 'tmp').mkdir(exist_ok=True)
        with tempfile.TemporaryDirectory(dir=ROOT / 'tmp') as folder:
            data = Path(folder)
            shards = []
            for index in range(2):
                output = data / f'shard-{index:04d}'
                generate(output, cars, groups=100, target_profiles=9,
                         seed=19 + index, shard_index=index, split_seed=17)
                report = json.loads((output / 'generation_report.json').read_text(encoding='utf-8'))
                self.assertEqual(sum(p['profiles'] for p in report['partitions'].values()), 9)
                shards.append({'directory': output.name, 'report_sha256': sha256(output / 'generation_report.json')})
            result = audit_population(data, {'shards': shards, 'profiles_requested': 18})
            self.assertEqual(result['profiles'], 18)
            self.assertEqual(result['split_leakage'], 0)


if __name__ == '__main__':
    unittest.main()
