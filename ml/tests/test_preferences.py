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

    def score_candidates(self, profile, vehicles):
        return self.predict(profile, vehicles)


class PreferenceTests(unittest.TestCase):
    def test_base_and_paid_seating_options_are_not_confused(self):
        car = vehicle(seats=5, seat_options=(5, 6, 7))
        self.assertEqual(exclusions(person(minimum_seats=5), car), [])
        self.assertEqual(exclusions(person(minimum_seats=6), car), ['seats-unverified'])
        self.assertEqual(exclusions(person(minimum_seats=8), car), ['insufficient-seats'])
        reduced = vehicle(seats=5, seat_options=(4, 5))
        self.assertEqual(exclusions(person(minimum_seats=5), reduced), [])

    def test_standard_assumption_passes_four_but_not_five_and_exceptions_need_evidence(self):
        for count in (2, 3, 4):
            self.assertEqual(exclusions(person(minimum_seats=count), vehicle()), [])
        self.assertEqual(exclusions(person(minimum_seats=5), vehicle()), ['seats-unverified'])
        self.assertEqual(exclusions(person(minimum_seats=3), vehicle(model='더 뉴 스타리아 Hybrid')), ['seats-unverified'])
        self.assertEqual(exclusions(person(minimum_seats=3), vehicle(seats=2)), ['insufficient-seats'])

    def test_size_preference_orders_equal_ml_scores_without_relaxing_budget(self):
        cheap = vehicle(id='cheap', model='Cheap', price=37000000, length_mm=4700, seats=5)
        spacious = vehicle(id='large', model='Large', price=45000000, length_mm=5000, seats=5)
        service = CandidateService(FixedRanker(), [cheap, spacious])
        cost_first = person(preferred_size='large', cost_importance=5, space_importance=1)
        space_first = replace(cost_first, cost_importance=1, space_importance=5)
        self.assertEqual(service.recommend(cost_first)['recommendations'][0]['vehicle']['id'], 'large')
        self.assertEqual(service.recommend(space_first)['recommendations'][0]['vehicle']['id'], 'large')
        impossible = replace(space_first, minimum_buffer=6000000)
        self.assertEqual(service.recommend(impossible)['recommendations'], [])

    def test_seating_gap_is_reported_for_relative_scoring(self):
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
        self.assertEqual({c['key'] for c in score['components']}, {'cost', 'model', 'fuel'})

    def test_unknown_seats_are_conditional_without_relaxing_finances(self):
        service = CandidateService(FixedRanker(), [vehicle(length_mm=4000)])
        p = person(minimum_seats=5, preferred_size='small')
        result = service.recommend(p)
        self.assertEqual(result['recommendations'], [])
        self.assertEqual(result['eligibleCount'], 1)
        self.assertEqual(len(result['conditionalRecommendations']), 1)
        self.assertTrue(result['conditionalRecommendations'][0]['seatingVerificationRequired'])
        self.assertTrue(result['conditionalRecommendations'][0]['cost']['eligible'])
        impossible = service.recommend(replace(p, minimum_buffer=6000000))
        self.assertEqual(impossible['conditionalRecommendations'], [])

    def test_optional_seats_require_confirmation_and_shortfall_is_excluded(self):
        car = vehicle(seat_options=(5, 6, 7))
        self.assertEqual(exclusions(person(minimum_seats=3), car), [])
        self.assertEqual(exclusions(person(minimum_seats=6), car), ['seats-unverified'])
        self.assertEqual(exclusions(person(minimum_seats=8), car), ['insufficient-seats'])
        result = CandidateService(FixedRanker(), [vehicle(seats=5)]).recommend(person(minimum_seats=6))
        self.assertEqual(result['recommendations'], [])
        self.assertEqual(result['seatingExcludedCount'], 1)
        self.assertEqual(result['conditionalRecommendations'], [])

    def test_actual_catalog_three_person_regression_and_seat_sources(self):
        from vehicle_matching.api import load_service
        from vehicle_matching.catalog import ROOT
        service = load_service(ROOT / 'ml/experiments/candidate-v2')
        p = person(monthly_income=3000000, monthly_expenses=1500000,
                   existing_monthly_payment=0, monthly_savings=0,
                   liquid_assets=40000000, emergency_reserve=10000000, down_payment=0,
                   minimum_seats=3, preferred_size='small', charging_available=False,
                   preferred_fuel=None, cost_importance=5, space_importance=4)
        result = service.recommend(p)
        self.assertTrue(result['recommendations'])
        for candidate in result['recommendations']:
            car = candidate['vehicle']
            if car['assumed_seat_range']:
                self.assertEqual(car['assumed_seat_range'], [2, 4])
            else:
                self.assertGreaterEqual(car['seats'] or min(car['seat_options']), 3)
                self.assertTrue(car['seats_source_url'] or car['seats_status'] == 'user-provided')
        for candidate in result['conditionalRecommendations']:
            self.assertTrue(candidate['seatingVerificationRequired'])
            self.assertEqual(candidate['cost']['exclusions'], [])

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
