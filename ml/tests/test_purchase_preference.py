import unittest
from dataclasses import replace

from test_preferences import FixedRanker
from test_vehicle_matching import person, vehicle
from vehicle_matching.service import CandidateService


class PurchasePreferenceTests(unittest.TestCase):
    def test_low_importance_never_rewards_price_alone(self):
        cheap = vehicle(id='cheap', model='Cheap', price=42000000, length_mm=4500, seats=5)
        expensive = replace(cheap, id='expensive', model='Expensive', price=49000000)
        over = replace(cheap, id='over', model='Over budget', price=51000000)
        service = CandidateService(FixedRanker(), [cheap, expensive, over])
        profile = person(financing_mode='recommendation', liquid_assets=50000000,
                         emergency_reserve=0, preferred_fuel=None, cost_importance=1)
        low = service.recommend(profile)
        high = service.recommend(replace(profile, cost_importance=5))
        self.assertEqual(low['recommendations'][0]['vehicle']['id'], 'cheap')
        self.assertEqual(high['recommendations'][0]['vehicle']['id'], 'cheap')
        for result in (low, high):
            self.assertNotIn('over', [row['vehicle']['id'] for row in result['recommendations']])
            self.assertTrue(all(row['cost']['eligible'] for row in result['recommendations']))
            self.assertTrue(all('budget' not in {item['key'] for item in row['preferenceAssessment']['components']} for row in result['recommendations']))

    def test_size_preference_is_respected_at_both_cost_importances(self):
        cheap = vehicle(id='cheap', model='Cheap', price=30000000, length_mm=4600, seats=5)
        matching = replace(cheap, id='matching', model='Matching', price=49000000, length_mm=4900)
        service = CandidateService(FixedRanker(), [cheap, matching])
        profile = person(financing_mode='recommendation', liquid_assets=50000000, emergency_reserve=0,
                         preferred_fuel=None, preferred_size='large', space_importance=3, purpose_importance=1)
        self.assertEqual(service.recommend(replace(profile, cost_importance=1))['recommendations'][0]['vehicle']['id'], 'matching')
        self.assertEqual(service.recommend(replace(profile, cost_importance=5))['recommendations'][0]['vehicle']['id'], 'matching')

    def test_low_cost_importance_does_not_override_strong_fuel_preference(self):
        electric = vehicle(id='ev', model='EV', price=40000000, fuel='ELECTRIC', efficiency=5, length_mm=4500)
        gasoline = vehicle(id='gas', model='Gas', price=49000000, length_mm=4500)
        profile = person(financing_mode='recommendation', liquid_assets=50000000, emergency_reserve=0,
                         cost_importance=1, preferred_fuel='ELECTRIC', fuel_importance=5)
        result = CandidateService(FixedRanker(), [electric, gasoline]).recommend(profile)
        self.assertEqual(result['recommendations'][0]['vehicle']['id'], 'ev')
