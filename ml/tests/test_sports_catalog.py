import tempfile
import unittest
from pathlib import Path

import numpy as np

from test_vehicle_matching import person, vehicle
from vehicle_matching.catalog import ROOT, read_catalog
from vehicle_matching.finance import Assumptions
from vehicle_matching.preference_model import PreferenceRanker, encode_preference
from vehicle_matching.train_sports_population import acceptable


class SportsCatalogTests(unittest.TestCase):
    def test_unknown_seats_cannot_satisfy_required_passengers(self):
        cars = read_catalog(ROOT / 'data/vehicles/sports-catalog-20261028/catalog.json')
        for car in cars:
            profile = person(liquid_assets=1000000000, minimum_seats=2, months=0,
                             financing_mode='recommendation')
            if car.seats is None:
                self.assertIsNone(acceptable(profile, car, Assumptions()))
            else:
                self.assertIsNotNone(acceptable(profile, car, Assumptions()))

    def test_previous_checkpoint_roundtrip_preserves_scores_with_new_bodies(self):
        model = PreferenceRanker.load(ROOT / 'ml/outputs/models/candidate-preferences/20261027-seating-verified-v1')
        cars = [vehicle(body_type=body) for body in ('SEDAN', 'COUPE', 'CONVERTIBLE', 'ROADSTER')]
        profile = person(preferred_body_type='OTHER')
        before, outside = model.score_candidates(profile, cars)
        with tempfile.TemporaryDirectory(dir=ROOT / 'tmp') as directory:
            model.save(Path(directory), {'test': 'backward compatibility'})
            restored = PreferenceRanker.load(directory)
            after, after_outside = restored.score_candidates(profile, cars)
        np.testing.assert_array_equal(before, after)
        self.assertEqual(outside, after_outside)
        vectors = [encode_preference(profile, car, model.assumptions) for car in cars[1:]]
        self.assertTrue(all(not np.array_equal(a, b) for a, b in zip(vectors, vectors[1:])))


if __name__ == '__main__':
    unittest.main()
