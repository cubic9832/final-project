"""Prevent unverified sales facts from becoming prices/years or purchase decisions."""
from copy import deepcopy
import unittest

from vehicle_matching.api import load_service
from vehicle_matching.catalog import ROOT
from vehicle_matching.sales_evidence import load_sales_evidence, sales_display_specifications


class SalesEvidenceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.service = load_service(ROOT / 'ml/outputs/models/preference-cohorts/20261028-v6-web-recheck')

    def test_unverified_sales_values_do_not_expose_synthetic_defaults_as_facts(self):
        service = self.service
        car = next(car for car in service.catalog if car['model'] == 'Amalfi Spider')
        original = service.traits[car['id']]['specifications']
        before = deepcopy(original)
        result = sales_display_specifications(original, service.sales_evidence[car['id']])
        self.assertEqual(result['price_won']['value'], 433000000)
        self.assertEqual(result['price_won']['status'], 'estimated-price')
        self.assertEqual(result['model_year']['value'], '미확인')
        self.assertIn('2+ 구조', result['seats']['value'])
        self.assertEqual(original, before)
        self.assertEqual(result['price_won']['training_assumption'], before['price_won'])
        roma = next(car for car in service.catalog if car['model'] == 'Roma Spider')
        self.assertEqual(service.sales_evidence[roma['id']]['price']['value'], 375000000)
        self.assertEqual(service.sales_evidence[roma['id']]['price']['status'], 'secondary-reference')

    def test_wrong_year_or_trim_never_borrows_verification_from_same_model(self):
        car = next(car for car in self.service.catalog if car['brand'] == 'Porsche' and car['trim'] == 'GT3')
        self.assertIn(car['id'], load_sales_evidence([car]))
        for key, value in [('year', '2026'), ('trim', 'GT3 with Touring Package'), ('brand', 'Ferrari')]:
            changed = dict(car, **{key: value})
            self.assertNotIn(car['id'], load_sales_evidence([changed]))

    def test_sales_review_keeps_every_research_configuration_out_of_financial_pool(self):
        research = [car for car in self.service.catalog if car['provenance']['kind'] != 'existing-snapshot']
        reviewed = self.service.sales_evidence
        self.assertEqual({car['id'] for car in research}, set(reviewed))
        financial_ids = {car.id for car in self.service.vehicles}
        for car in research:
            self.assertNotIn(car['id'], financial_ids)
            record = reviewed[car['id']]
            self.assertGreater(record['price']['value'], 0)
            self.assertTrue(record['price']['sources'])
            self.assertTrue(record['domestic']['sources'])
            self.assertNotIn('미확인', record['domestic']['value'])
            self.assertIsNone(record['order']['value'])
            self.assertEqual(record['financial_assessment'], 'not-assessed')
            if car['brand'] == 'Porsche':
                self.assertEqual(record['price']['value'], car['price'])
                self.assertEqual(record['year']['value'], car['year'])
                self.assertEqual(record['price']['status'], 'official-reference')


if __name__ == '__main__':
    unittest.main()
