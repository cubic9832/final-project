import json
import tempfile
import unittest
from pathlib import Path

from vehicle_matching.api import load_service
from vehicle_matching.catalog import ROOT
from vehicle_matching.preferences import assumes_standard_seating, exclusions
from vehicle_matching.seating import apply_seating_registry
from test_vehicle_matching import person, vehicle


class SeatingRegistrationTests(unittest.TestCase):
    def test_all_registered_candidates_use_seating_data_instead_of_generic_assumption(self):
        service = load_service(ROOT / 'ml/experiments/candidate-v2')
        registry = json.loads((ROOT / 'data/vehicles/candidate-seating-registry.json').read_text(encoding='utf-8'))
        registered_ids = {r['id'] for r in registry['vehicles']}
        self.assertTrue(registered_ids.issubset({v.id for v in service.vehicles}))
        # Supplemental official candidates need not be entries in the legacy registry.
        for car in (v for v in service.vehicles if v.id in registered_ids):
            self.assertFalse(assumes_standard_seating(car), car.id)
            self.assertTrue(car.seats_status)
            self.assertTrue(car.seats or car.seat_options)
        morning = next(v for v in service.vehicles if v.model == '모닝')
        self.assertEqual(exclusions(person(minimum_seats=5), morning), [])
        self.assertEqual(exclusions(person(minimum_seats=6), morning), ['insufficient-seats'])

    def test_document_conflicts_do_not_create_nonexistent_seating_capacity(self):
        service = load_service(ROOT / 'ml/experiments/candidate-v2')
        gt = next(v for v in service.vehicles if v.model == 'EV9 GT')
        self.assertEqual(gt.seats, 6)
        self.assertEqual(exclusions(person(minimum_seats=7), gt), ['insufficient-seats'])
        seven = next(v for v in service.vehicles if v.id == 'legacy-C0030')
        nine = next(v for v in service.vehicles if v.id == 'legacy-C0028')
        self.assertEqual(exclusions(person(minimum_seats=8), seven), ['insufficient-seats'])
        self.assertEqual(exclusions(person(minimum_seats=9), nine), [])

    def test_registry_rejects_wrong_candidate_identity(self):
        row = {'id': 'example', 'brand': 'wrong', 'model': 'wrong', 'trim': 'wrong', 'price': 1}
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / 'registry.json'
            path.write_text(json.dumps({'vehicles': [row]}), encoding='utf-8')
            with self.assertRaisesRegex(ValueError, 'identity mismatch'):
                apply_seating_registry([vehicle()], path)
