"""Saved-model inference, hard constraints, request isolation and unknown evidence."""
from pathlib import Path
import tempfile
import unittest

from fastapi.testclient import TestClient
import numpy as np
import torch

from vehicle_matching.api import create_app
from vehicle_matching.catalog import ROOT
from vehicle_matching.lifestyle_features import FEATURE_NAMES
from vehicle_matching.lifestyle_model import LifestyleRanker, network
from vehicle_matching.lifestyle_service import LifestyleService
from vehicle_matching.train_lifestyle_choices import train
from tools.data.households.generate_lifestyle_choices import generate, load_catalog, DEFAULT_BASE, DEFAULT_LUXURY


class LifestyleModelTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        (ROOT / 'tmp').mkdir(exist_ok=True)
        cls.folder = tempfile.TemporaryDirectory(dir=ROOT / 'tmp')
        cls.data, cls.output = [Path(cls.folder.name) / name for name in ('data', 'model')]
        generate(cls.data, load_catalog(DEFAULT_BASE, DEFAULT_LUXURY), groups=323, seed=31)
        train(cls.data, cls.output, epochs=2, batch_size=128)

    @classmethod
    def tearDownClass(cls):
        cls.folder.cleanup()

    def test_unknown_features_cannot_change_pair_scores_and_pairs_are_antisymmetric(self):
        torch.manual_seed(4)
        ranker = LifestyleRanker(network())
        a = np.full((2, len(FEATURE_NAMES)), .2, dtype=np.float32)
        b = np.full_like(a, .8)
        weights, masks = np.ones_like(a), np.ones_like(a)
        masks[:, 0] = 0
        weights[:, 0] = 0
        expected = ranker.pair_logits(a, b, weights, masks)
        a[:, 0] = 10000
        b[:, 0] = -10000
        np.testing.assert_array_equal(expected, ranker.pair_logits(a, b, weights, masks))
        np.testing.assert_allclose(expected, -ranker.pair_logits(b, a, weights, masks))

    def test_saved_model_api_rejects_invalid_preferences_and_never_recommends_research(self):
        service = LifestyleService.load(self.output)
        request = {'profile': {'monthly_income': 10000000., 'monthly_expenses': 2000000.,
            'existing_monthly_payment': 0., 'liquid_assets': 1000000000., 'emergency_reserve': 0.,
            'monthly_savings': 0., 'annual_distance': 15000., 'minimum_seats': 4},
            'lifestyle': {'sportiness': 1., 'angularity': 1., 'design_importance': 5}, 'k': 3}
        with TestClient(create_app(service)) as client:
            options = client.get('/api/v2/recommendation-options')
            self.assertEqual(options.status_code, 200, options.text)
            self.assertTrue(options.json()['data']['lifestyleSupported'])
            response = client.post('/api/v2/recommendations', json=request)
            self.assertEqual(response.status_code, 200, response.text)
            original = response.json()['data']
            self.assertTrue(original['recommendations'])
            self.assertEqual(original['trainingCatalogCount'], 323)
            for row in original['recommendations']:
                self.assertFalse(row['vehicle']['id'].startswith('research-'))
                self.assertGreaterEqual(row['vehicle']['seats'], 4)
                self.assertTrue(row['cost']['eligible'])
                self.assertIn('ride_comfort', row['lifestyleEvidence']['unknownDimensions'])
            changed = dict(request, lifestyle={'sportiness': 0., 'angularity': 0.})
            self.assertEqual(client.post('/api/v2/recommendations', json=changed).status_code, 200)
            repeated = client.post('/api/v2/recommendations', json=request).json()['data']
            self.assertEqual(original['recommendations'], repeated['recommendations'])
            for invalid in ({'sportiness': 2.}, {'brand': 'nonexistent'}, {'design_importance': 0}, {'interior_guess': 1.}):
                response = client.post('/api/v2/recommendations', json=dict(request, lifestyle=invalid))
                self.assertEqual(response.status_code, 400, response.text)
                self.assertIn('application/problem+json', response.headers['content-type'])

    def test_changed_arrays_cannot_be_used_for_retraining(self):
        path = self.data / 'train_choices.npz'
        original = path.read_bytes()
        try:
            path.write_bytes(original + b'changed')
            with self.assertRaisesRegex(ValueError, 'checksum'):
                train(self.data, Path(self.folder.name) / 'bad-model', epochs=1)
        finally:
            path.write_bytes(original)
