import unittest
from dataclasses import replace

from test_preferences import FixedRanker
from test_vehicle_matching import person, vehicle
from vehicle_matching.service import CandidateService


class RecommendationBudgetTests(unittest.TestCase):
    def test_fractional_cash_keeps_reserve_without_float_addition_rejection(self):
        cash, reserve = 194965331.33385697, 57558379.91220878
        p = person(liquid_assets=cash, emergency_reserve=reserve, down_payment=0)
        service = CandidateService(FixedRanker(), [vehicle(price=cash-reserve-1)])
        result = service.recommend(p)
        self.assertEqual(len(result['recommendations']), 1)
        self.assertTrue(result['recommendations'][0]['cost']['eligible'])
        with self.assertRaises(ValueError):
            replace(p, down_payment=cash-reserve+1)

    def test_saved_financing_does_not_affect_recommendations_or_generate_upfront_cash(self):
        service = CandidateService(FixedRanker(), [vehicle(price=15000000)])
        p = person(monthly_income=3500000, monthly_expenses=2000000,
                   existing_monthly_payment=0, monthly_savings=1000000,
                   liquid_assets=30000000, emergency_reserve=1000000, down_payment=0, purchase_price_ceiling=15000000)
        first = service.recommend(p)
        self.assertTrue(first['recommendations'])
        changed = service.recommend(replace(p, down_payment=20000000, months=72, annual_rate=0.2))
        self.assertEqual(first, changed)
        cost = first['recommendations'][0]['cost']
        self.assertEqual(cost['remaining_monthly'], round(500000 - cost['monthly_running_cost'], 2))
        for field in ('required_down_payment', 'upfront_available', 'cash_after_purchase', 'monthly_payment'):
            self.assertNotIn(field, cost)
        self.assertEqual(service.recommend(replace(p, minimum_buffer=2000000))['recommendations'], [])

    def test_ml_receives_no_assumed_financing_parameters(self):
        class RecordingRanker(FixedRanker):
            def predict(self, profile, vehicles):
                self.profile = profile
                return super().predict(profile, vehicles)
        ranker = RecordingRanker()
        result = CandidateService(ranker, [vehicle()]).recommend(person())
        self.assertTrue(result['recommendations'])
        self.assertEqual(ranker.profile.down_payment, 0)
        self.assertEqual(ranker.profile.months, 0)
        self.assertEqual(ranker.profile.annual_rate, 0)
