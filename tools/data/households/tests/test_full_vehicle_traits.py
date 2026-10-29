import json
import unittest

from vehicle_matching.catalog import ROOT
from tools.data.vehicles.build_full_vehicle_traits import OUTPUT, CATALOG, DETAILS, estimate_acceleration, match_specification
from tools.data.households.generate_preference_cohorts import add_acceleration_evidence
from tools.data.vehicles.lifestyle_traits import build_traits


class FullVehicleTraitsTests(unittest.TestCase):
    def test_official_priority_complete_coverage_and_estimate_disclosure(self):
        read = lambda path: json.loads(path.read_text(encoding='utf-8'))
        cars = read(CATALOG)
        traits = read(OUTPUT/'vehicle_traits.json')['vehicles']
        old = add_acceleration_evidence(cars,build_traits(cars,read(OUTPUT/'visual-reviews.json')),read(DETAILS))
        for car in cars:
            row = traits[car['id']]
            for name in ('exterior_sportiness','exterior_angularity','acceleration_performance'):
                self.assertIsNotNone(row['values'][name])
                self.assertTrue(0 <= row['values'][name] <= 1)
            acceleration = row['evidence']['acceleration_performance']
            if old[car['id']]['values']['acceleration_performance'] is not None:
                self.assertEqual(acceleration,old[car['id']]['evidence']['acceleration_performance'])
            if acceleration['kind']=='estimated-acceleration':
                self.assertIsNone(acceleration['source_url'])
                lo,hi = acceleration['heuristic_range_seconds']
                self.assertLess(lo,acceleration['seconds_0_100']);self.assertGreater(hi,acceleration['seconds_0_100'])
                self.assertIn('unvalidated',acceleration['confidence'])
            self.assertIsNone(row['values']['ride_comfort'])

    def test_estimates_ignore_brand_price_and_visual_scores(self):
        base = {'body_type':'SUV','fuel':'GASOLINE','brand':'A','price':1}
        self.assertEqual(estimate_acceleration(base),estimate_acceleration(dict(base,brand='B',price=999999999,exterior_sportiness=1)))
        with_engine = estimate_acceleration(base,{'displacement_cc':3000,'curb_weight_kg':1800})
        self.assertLess(with_engine['seconds_0_100'],estimate_acceleration(base)['seconds_0_100'])
        self.assertEqual(estimate_acceleration(base),estimate_acceleration(base,{'displacement_cc':float('nan')}))

    def test_ambiguous_powertrain_never_supplies_measurements(self):
        car = {'brand':'A','model':'B','trim':'C','year':'2026','price':100}
        spec = dict(brand='A',model='B',trim='C',model_year=2026,price_won=100,displacement_cc=2000)
        self.assertEqual(match_specification(car,[spec]),spec)
        self.assertIsNone(match_specification(car,[spec,dict(spec,displacement_cc=3000)]))
        self.assertIsNone(match_specification(dict(car,year=''),[spec]))


if __name__ == '__main__':
    unittest.main()
