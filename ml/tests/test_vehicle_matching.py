import json
import math
import tempfile
import unittest
from dataclasses import replace
from pathlib import Path

import numpy as np
from fastapi.testclient import TestClient

from vehicle_matching.api import create_app, load_service
from vehicle_matching.catalog import ROOT, Vehicle, load_csv
from vehicle_matching.features import encode
from vehicle_matching.finance import Assumptions, Profile, assess, installment


def person(**changes):
    base = Profile(monthly_income=6000000, monthly_expenses=1500000, existing_monthly_payment=200000,
                   liquid_assets=45000000, down_payment=20000000, emergency_reserve=5000000,
                   monthly_savings=1000000, annual_distance=15000, months=48,
                   preferred_fuel='HYBRID', charging_available=True)
    return replace(base, **changes)


def vehicle(**changes):
    base = Vehicle('example', 'Example brand', 'Example model', 'Trim', '2026', 30000000,
                   'GASOLINE', 12, 'https://example.com/price', '2026-10-14')
    return replace(base, **changes)


class FinanceTests(unittest.TestCase):
    def test_payment_zero_interest_and_outright_shortfall(self):
        self.assertEqual(installment(12000000, 0, 24), 500000)
        self.assertEqual(installment(0, 0.06, 0), 0)
        result = assess(person(months=0), vehicle())
        self.assertFalse(result['eligible'])
        self.assertIsNone(result['monthly_total'])
        self.assertIn('insufficient-cash-for-outright-purchase', result['exclusions'])
        paid = assess(person(months=0, liquid_assets=50000000, down_payment=32100000), vehicle())
        self.assertTrue(paid['eligible'])
        self.assertEqual(paid['monthly_payment'], 0)

    def test_savings_existing_debt_and_unknown_efficiency_affect_buffer(self):
        base = assess(person(), vehicle())
        changed = assess(person(existing_monthly_payment=500000, monthly_savings=1100000), vehicle())
        self.assertAlmostEqual(base['remaining_monthly'] - changed['remaining_monthly'], 400000)
        unknown = assess(person(), vehicle(efficiency=None))
        self.assertTrue(unknown['efficiency_estimated'])
        self.assertEqual(unknown['stress_monthly_total'], unknown['monthly_total'])

    def test_invalid_money_and_impossible_cash_are_rejected(self):
        for value in (-1, math.nan, math.inf, True):
            with self.subTest(value=value), self.assertRaises(ValueError):
                person(monthly_income=value)
        with self.assertRaises(ValueError):
            person(down_payment=60000000)
        with self.assertRaises(ValueError):
            person(months=True)

    def test_charging_does_not_exclude_and_monthly_budget_is_mandatory(self):
        electric = vehicle(fuel='ELECTRIC', efficiency=5)
        self.assertNotIn('charging-unavailable', assess(person(charging_available=False), electric)['exclusions'])
        cost = assess(person(), vehicle())
        available = cost['monthly_total'] + 10000
        constrained = person(monthly_expenses=6000000 - 200000 - 1000000 - available)
        result = assess(constrained, vehicle())
        self.assertGreater(result['remaining_monthly'], 0)
        self.assertTrue(result['eligible'])
        tight = replace(constrained, minimum_buffer=20000)
        self.assertIn('insufficient-monthly-buffer', assess(tight, vehicle())['exclusions'])


class TrainedCandidateTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.service = load_service(ROOT / 'ml/experiments/candidate-v2')

    def test_catalog_exceeds_twenty_and_keeps_missing_efficiency_unknown(self):
        vehicles, report = load_csv()
        self.assertGreater(len({(v.brand, v.model) for v in vehicles}), 20)
        self.assertGreater(report['unknown_efficiency'], 0)
        self.assertTrue(all(v.source_url and v.checked_on and v.price > 0 for v in vehicles))

    def test_new_vehicle_identity_needs_no_new_output_node(self):
        original = vehicle()
        new = replace(original, id='never-seen-id', model='Never seen model', brand='New brand')
        np.testing.assert_array_equal(encode(person(), original), encode(person(), new))
        scores, _ = self.service.ranker.predict(person(), [original, new])
        self.assertAlmostEqual(scores[0], scores[1], places=6)
        from vehicle_matching.service import CandidateService
        result = CandidateService(self.service.ranker, [new]).recommend(person())
        self.assertEqual(result['recommendations'][0]['vehicle']['id'], 'never-seen-id')

    def test_no_candidates_does_not_fill_with_infeasible_cars(self):
        poor = person(monthly_income=1500000, monthly_expenses=1500000,
                      existing_monthly_payment=0, monthly_savings=0, liquid_assets=0,
                      down_payment=0, emergency_reserve=0)
        result = self.service.recommend(poor)
        self.assertEqual(result['eligibleCount'], 0)
        self.assertEqual(result['recommendations'], [])

    def test_served_recommendations_are_eligible_and_distinct_under_cost_shift(self):
        for profile in (person(), person(existing_monthly_payment=1500000),
                        person(months=0), person(charging_available=False)):
            result = self.service.recommend(profile, 10)
            keys = []
            for row in result['recommendations']:
                keys.append((row['vehicle']['brand'], row['vehicle']['model']))
                self.assertTrue(row['cost']['eligible'])
                self.assertGreaterEqual(row['cost']['remaining_monthly'], profile.minimum_buffer)
                self.assertTrue(np.isfinite(row['rankingScore']))
                self.assertEqual(row['rankingScoreType'], 'ml-raw')
            self.assertEqual(len(keys), len(set(keys)))

    def test_catalog_tampering_is_detected(self):
        import shutil
        source = ROOT / 'ml/experiments/candidate-v2'
        with tempfile.TemporaryDirectory() as directory:
            for name in ('metadata.json', 'catalog.json'):
                shutil.copyfile(source / name, Path(directory) / name)
            (Path(directory) / 'catalog.json').write_text('[]', encoding='utf-8')
            with self.assertRaisesRegex(ValueError, 'checksum'):
                load_service(directory)

    def test_model_bundle_survives_cross_platform_line_endings(self):
        import shutil
        source = ROOT / 'ml/experiments/candidate-v2'
        with tempfile.TemporaryDirectory() as directory:
            for path in source.iterdir():
                if path.is_file():
                    shutil.copyfile(path, Path(directory) / path.name)
            catalog = Path(directory) / 'catalog.json'
            catalog.write_bytes(catalog.read_bytes().replace(b'\r\n', b'\n'))
            restored = load_service(directory)
            self.assertEqual(len(restored.recommend(person())['recommendations']), 3)


class CandidateApiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.service = load_service(ROOT / 'ml/experiments/candidate-v2')

    def test_request_to_actual_model_and_field_errors(self):
        from dataclasses import asdict
        with TestClient(create_app(self.service)) as client:
            payload = {'profile': asdict(person()), 'k': 3}
            response = client.post('/api/v2/recommendations', json=payload)
            self.assertEqual(response.status_code, 200)
            data = response.json()['data']
            self.assertEqual(len(data['recommendations']), 3)
            self.assertEqual(data['scorePolicy'], 'required-seats-preference-priority-price-band-v2')
            self.assertTrue(all(r['rankingScoreType'] == 'ml-raw' and 'integratedScore' not in r
                                for r in data['recommendations']))
            json.dumps(data, allow_nan=False)
            self.assertGreater(client.get('/api/v2/recommendation-options').json()['data']['modelNames'], 20)
            payload['profile']['monthly_income'] = -1
            invalid = client.post('/api/v2/recommendations', json=payload)
            self.assertEqual(invalid.status_code, 400)
            self.assertEqual(invalid.headers['content-type'], 'application/problem+json')
            self.assertEqual(invalid.json()['errors'][0]['field'], 'profile.monthly_income')
            payload['profile'] = asdict(person())
            payload['profile']['down_payment'] = 30000000
            legacy = client.post('/api/v2/recommendations', json=payload)
            self.assertEqual(legacy.status_code, 200)
            self.assertEqual(legacy.json()['data'], data)
            payload['profile'] = asdict(person())
            payload['profile']['months'] = False
            self.assertEqual(client.post('/api/v2/recommendations', json=payload).status_code, 400)


if __name__ == '__main__':
    unittest.main()
