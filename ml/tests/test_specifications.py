"""Specification joins must preserve identity, cash eligibility and cost units."""
import json
import tempfile
import unittest
from dataclasses import replace
from pathlib import Path

from vehicle_matching.api import load_service
from vehicle_matching.catalog import ROOT
from vehicle_matching.finance import assess
from vehicle_matching.specifications import apply_specifications
from test_vehicle_matching import person


class SpecificationTests(unittest.TestCase):
    def test_official_energy_consumption_changes_cost_without_changing_cash_price(self):
        before=load_service(ROOT/'ml/experiments/candidate-v2',apply_specification_updates=False)
        after=load_service(ROOT/'ml/experiments/candidate-v2')
        self.assertEqual([(v.id,v.price) for v in before.vehicles],[(v.id,v.price) for v in after.vehicles])
        self.assertEqual(apply_specifications(after.vehicles),after.vehicles)
        for model in ('ES','XC60','Model Y','캐스퍼 일렉트릭','더 뉴 스타리아 Electric'):
            for v in [v for v in after.vehicles if v.model==model]:
                cost=assess(person(financing_mode='recommendation',down_payment=0,months=0,liquid_assets=300000000),v)
                self.assertFalse(cost['efficiency_estimated'])
                self.assertEqual(cost['monthly_payment'],0)
        t8=next(v for v in after.vehicles if v.model=='XC60' and v.trim.startswith('T8'))
        self.assertEqual(t8.fuel,'HYBRID')
        self.assertIn('PHEV',t8.source_note)
        star=next(v for v in after.vehicles if v.model=='더 뉴 스타리아 Electric')
        self.assertIn('11인승',star.default_configuration)
        self.assertEqual(star.efficiency,3.9)
        references=[v for v in after.vehicles if v.efficiency_reference_only]
        self.assertTrue(references)
        for v in references:
            cost=assess(person(),v)
            self.assertTrue(cost['efficiency_estimated'])
            self.assertTrue(v.default_configuration)

    def test_wrong_vehicle_price_cannot_receive_another_configurations_specifications(self):
        base=load_service(ROOT/'ml/experiments/candidate-v2').vehicles
        with self.assertRaisesRegex(ValueError,'identity mismatch'):
            apply_specifications([replace(base[0],price=base[0].price+1)])

    def test_changed_reference_does_not_silently_overwrite_unknown_existing_value(self):
        base=load_service(ROOT/'ml/experiments/candidate-v2').vehicles
        e=next(v for v in base if v.model=='E-Class')
        with self.assertRaisesRegex(ValueError,'Unexpected previous'):
            apply_specifications([replace(e,length_mm=5100)])
