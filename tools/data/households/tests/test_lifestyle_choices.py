"""Preference reversals, research safety, group isolation and saved labels."""
import json
from pathlib import Path
import tempfile
import unittest

import numpy as np

from tools.data.households.generate_lifestyle_choices import (
    DEFAULT_BASE, DEFAULT_LUXURY, DIMENSIONS, encode, generate, load_catalog,
    safe_cost, score, audit_saved, FEATURE_NAMES, comparison_mask,
)
from tools.data.vehicles.lifestyle_traits import build_traits, read_reviews
from vehicle_matching.finance import Profile
from vehicle_matching.catalog import ROOT


class LifestyleChoiceTests(unittest.TestCase):
    def test_design_preference_reverses_order_without_price_or_brand_shortcut(self):
        a = {'values': dict.fromkeys(DIMENSIONS, .1), 'body_type': 'SEDAN'}
        b = {'values': dict.fromkeys(DIMENSIONS, .9), 'body_type': 'SEDAN'}
        car = {'brand': 'same'}
        weights = [1] * len(DIMENSIONS) + [0] * (len(FEATURE_NAMES) - len(DIMENSIONS))
        for target, expected in ((0, True), (1, False)):
            taste = {'targets': dict.fromkeys(DIMENSIONS, target), 'purpose': 'commute', 'brand': None, 'body_type': 'SEDAN'}
            self.assertEqual(score(encode(taste, a, car, 0), weights) > score(encode(taste, b, car, 0), weights), expected)

    def test_missing_traits_are_not_guessed_or_used_against_other_car(self):
        cars = load_catalog(DEFAULT_BASE, DEFAULT_LUXURY)
        traits = build_traits(cars, read_reviews())
        self.assertTrue(all(row['values']['ride_comfort'] is None for row in traits.values()))
        self.assertTrue(all(row['values']['interior_minimalism'] is None for row in traits.values()))
        research = next(c for c in cars if c['brand'] == 'Lamborghini' and c['model'] == 'Revuelto')
        self.assertAlmostEqual(traits[research['id']]['values']['acceleration_performance'], .95)
        existing = next(c for c in cars if c['brand'] == '기아' and c['model'] == '레이')
        self.assertEqual(traits[existing['id']]['values']['exterior_angularity'], 1)
        mask = comparison_mask({'purpose': 'weekend-drive', 'brand': None, 'targets': dict.fromkeys(DIMENSIONS, .5)}, traits[research['id']], traits[existing['id']], False)
        self.assertEqual(mask[DIMENSIONS.index('acceleration_performance')], 0)
        self.assertEqual(mask[len(DIMENSIONS)], 0)
        self.assertEqual(mask[-1], 0)
        # Neither unsupported claims nor unverified seating should become a trait.
        modified = dict(existing, seats_status='user-provided', length_mm=None)
        values = build_traits([modified], {'reviews': []})[modified['id']]['values']
        self.assertIsNone(values['seat_capacity'])
        self.assertIsNone(values['compactness'])

    def test_bad_visual_evidence_and_comfort_inference_are_rejected(self):
        cars = load_catalog(DEFAULT_BASE, DEFAULT_LUXURY)
        reviews = read_reviews()
        reviews['reviews'][0]['traits']['exterior_sportiness']['image_sha256'] = 'invalid'
        with self.assertRaisesRegex(ValueError, 'hash'):
            build_traits(cars, reviews)
        reviews = read_reviews()
        review = reviews['reviews'][0]
        review['traits']['ride_comfort'] = review['traits'].pop('exterior_sportiness')
        with self.assertRaisesRegex(ValueError, 'comfort'):
            build_traits(cars, reviews)

    def test_luxury_unknowns_are_preserved_and_never_financially_approved(self):
        cars = load_catalog(DEFAULT_BASE, DEFAULT_LUXURY)
        research = [c for c in cars if c['provenance']['kind'] != 'existing-snapshot']
        self.assertEqual(len(research), 19)
        self.assertTrue(any(c['price'] is None for c in research))
        profile = Profile(100000000, 0, 0, 10000000000, 0, 0, 0, 15000, 0, financing_mode='recommendation')
        self.assertTrue(all(safe_cost(profile, car) is None for car in research))

    def test_saved_choices_are_reproducible_isolated_and_include_every_car(self):
        cars = load_catalog(DEFAULT_BASE, DEFAULT_LUXURY)
        (ROOT / 'tmp').mkdir(exist_ok=True)
        with tempfile.TemporaryDirectory(dir=ROOT / 'tmp') as folder:
            paths = [Path(folder) / 'a', Path(folder) / 'b']
            reports = [generate(path, values, groups=len(cars), seed=17)
                       for path, values in zip(paths, (cars, list(reversed(cars))))]
            self.assertEqual(reports[0]['unexposed_ids'], [])
            groups = {}
            for role in ('train', 'validation', 'test'):
                self.assertEqual((paths[0] / f'{role}.jsonl').read_bytes(), (paths[1] / f'{role}.jsonl').read_bytes())
                rows = [json.loads(line) for line in (paths[0] / f'{role}.jsonl').read_text(encoding='utf-8').splitlines()]
                with np.load(paths[0] / f'{role}_choices.npz') as arrays:
                    self.assertEqual(len(rows), len(arrays['labels']))
                    for i, row in enumerate(rows):
                        self.assertEqual(groups.setdefault(row['group'], role), role)
                        self.assertEqual(row['label'], int(row['draw'] < row['probability_a']))
                        self.assertEqual(row['label'], arrays['labels'][i])
                        self.assertAlmostEqual(row['utility_a'], score(row['features_a'], row['weights']))
                        if row['task'] == 'taste-only':
                            self.assertFalse(row['financial_eligible'])
                            self.assertEqual(row['weights'][-1], 0)
            with self.assertRaises(FileExistsError):
                generate(paths[0], cars, groups=1)
            path = paths[0] / 'train.jsonl'
            lines = path.read_text(encoding='utf-8').splitlines()
            row = json.loads(lines[0])
            row['label'] = 1 - row['label']
            lines[0] = json.dumps(row)
            path.write_text('\n'.join(lines) + '\n', encoding='utf-8')
            with self.assertRaisesRegex(ValueError, 'label'):
                audit_saved(paths[0])


if __name__ == '__main__':
    unittest.main()
