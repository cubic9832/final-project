import unittest
from dataclasses import replace

from test_preferences import FixedRanker
from test_vehicle_matching import person, vehicle
from vehicle_matching.service import CandidateService
from vehicle_matching.finance import assess


class FinancialSoftPolicyTests(unittest.TestCase):
    def test_known_shortfall_is_excluded_even_with_available_cash(self):
        class LowRanker(FixedRanker):
            def predict(self,profile,vehicles): return [1e-30]*len(vehicles),[False]*len(vehicles)
        cars=[vehicle(id=str(i),model=str(i),price=10000000+i*100000, fuel='ELECTRIC',seats=2) for i in range(4)]
        cars.append(replace(cars[0],id='another-trim'))
        result=CandidateService(LowRanker(),cars).recommend(person(minimum_seats=7,preferred_size='large',charging_available=False))
        self.assertEqual(result['recommendations'],[])
        self.assertEqual(result['seatingExcludedCount'],5)

    def test_purchase_price_and_monthly_funds_cannot_be_bypassed_by_matching_preferences(self):
        p=person(monthly_income=2000000,monthly_expenses=1500000,monthly_savings=200000,
                 existing_monthly_payment=0,liquid_assets=0,emergency_reserve=0,down_payment=0,
                 preferred_fuel='ELECTRIC',preferred_size='large',cost_importance=1,space_importance=5)
        service=CandidateService(FixedRanker(),[vehicle(price=100000000,fuel='ELECTRIC',length_mm=5000,seats=9)])
        result=service.recommend(p)
        self.assertEqual(result['recommendations'],[])
        self.assertEqual(result['status'],'no-financially-eligible-vehicle')
        self.assertEqual(service.recommend(replace(person(),purchase_price_ceiling=1000000))['recommendations'],[])

    def test_fewer_than_three_financial_models_returns_only_available_models(self):
        result=CandidateService(FixedRanker(),[vehicle()]).recommend(person())
        self.assertEqual(len(result['recommendations']),1)

    def test_fuel_and_seating_rules_do_not_override_equal_ml_scores(self):
        gas=vehicle(id='gas',model='gas',seats=7,fuel='GASOLINE',price=20000000)
        hybrid=vehicle(id='hybrid',model='hybrid',seats=2,fuel='HYBRID',price=20000000)
        service=CandidateService(FixedRanker(),[gas,hybrid])
        p=person(minimum_seats=7,fuel_importance=5,seating_importance=1)
        self.assertEqual(service.recommend(p)['recommendations'][0]['vehicle']['id'],'gas')
        self.assertEqual(service.recommend(replace(p,fuel_importance=1,seating_importance=5))['recommendations'][0]['vehicle']['id'],'gas')

    def test_cash_purchase_has_no_loan_and_monthly_boundary_uses_running_costs(self):
        p=person(financing_mode='recommendation',down_payment=0)
        v=vehicle()
        p=replace(p,liquid_assets=v.price+p.emergency_reserve)
        cost=assess(p,v)
        self.assertEqual(cost['monthly_payment'],0)
        self.assertEqual(cost['financing_months'],0)
        self.assertEqual(cost['financing_annual_rate'],0)
        exact=replace(p,minimum_buffer=cost['remaining_monthly'])
        self.assertTrue(assess(exact,v)['eligible'])
        self.assertFalse(assess(replace(exact,minimum_buffer=exact.minimum_buffer+1),v)['eligible'])


if __name__=='__main__': unittest.main()
