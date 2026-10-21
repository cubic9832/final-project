import unittest
from dataclasses import replace

from vehicle_matching.finance import assess
from vehicle_matching.preferences import exclusions, integrated_score
from vehicle_matching.service import CandidateService
from test_vehicle_matching import person, vehicle


class FixedRanker:
    from vehicle_matching.finance import Assumptions
    assumptions = Assumptions()

    def predict(self, profile, vehicles):
        return [0.5] * len(vehicles), [False] * len(vehicles)


class PreferenceTests(unittest.TestCase):
    def test_user_importance_changes_ranking_without_relaxing_budget(self):
        cheap = vehicle(id='cheap', model='Cheap', price=15000000, length_mm=4300, seats=5)
        spacious = vehicle(id='large', model='Large', price=45000000, length_mm=5000, seats=5)
        service = CandidateService(FixedRanker(), [cheap, spacious])
        cost_first = person(preferred_size='large', cost_importance=5, space_importance=1)
        space_first = replace(cost_first, cost_importance=1, space_importance=5)
        self.assertEqual(service.recommend(cost_first)['recommendations'][0]['vehicle']['id'], 'cheap')
        self.assertEqual(service.recommend(space_first)['recommendations'][0]['vehicle']['id'], 'large')
        impossible = replace(space_first, minimum_buffer=6000000)
        self.assertEqual(service.recommend(impossible)['recommendations'], [])

    def test_minimum_seats_is_mandatory_even_when_space_weight_is_low(self):
        p = person(minimum_seats=5, space_importance=1)
        self.assertEqual(exclusions(p, vehicle(seats=4)), ['insufficient-seats'])
        self.assertEqual(exclusions(p, vehicle()), ['seats-unverified'])
        self.assertEqual(exclusions(p, vehicle(seats=5)), [])

    def test_missing_length_is_not_invented_or_rewarded(self):
        p = person(preferred_size='large')
        self.assertEqual(exclusions(p, vehicle()), ['length-unverified'])
        no_preference = replace(p, preferred_size='any')
        score = integrated_score(no_preference, vehicle(), assess(no_preference, vehicle()), 0.5)
        self.assertFalse(score['spaceEvaluated'])
        self.assertEqual({c['key'] for c in score['components']}, {'cost', 'model'})

    def test_cost_does_not_count_financed_principal_twice_and_components_sum(self):
        p, v = person(annual_rate=0), vehicle(length_mm=4500)
        cost = assess(p, v)
        result = integrated_score(p, v, cost, 0.5)
        self.assertAlmostEqual(result['estimatedOwnershipCost'], cost['total_purchase_cost'] + cost['monthly_running_cost'] * 60, places=2)
        self.assertAlmostEqual(result['total'], sum(c['contribution'] for c in result['components']))
        self.assertTrue(0 <= result['total'] <= 100)

    def test_more_expensive_or_larger_is_not_automatically_better(self):
        p = person(preferred_size='small')
        small = vehicle(length_mm=4000)
        big = replace(small, length_mm=5000)
        self.assertGreater(integrated_score(p, small, assess(p, small), 0.5)['total'], integrated_score(p, big, assess(p, big), 0.5)['total'])

    def test_invalid_preference_values_are_rejected(self):
        for changes in ({'cost_importance': 0}, {'space_importance': True}, {'minimum_seats': -1}, {'preferred_size': 'unknown'}):
            with self.subTest(changes=changes), self.assertRaises(ValueError):
                person(**changes)
