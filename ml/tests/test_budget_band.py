import unittest
from dataclasses import replace

from test_preferences import FixedRanker
from test_vehicle_matching import person,vehicle
from vehicle_matching.service import CandidateService
from vehicle_matching.budget import recommendation_budget
from vehicle_matching.finance import assess


class BudgetBandTests(unittest.TestCase):
    def test_price_does_not_break_equal_ml_score_ties(self):
        cars=[vehicle(id='cheap',model='Cheap',price=10000000,length_mm=4100),
              vehicle(id='a',model='A',price=40000000,length_mm=6000),
              vehicle(id='b',model='B',price=45000000,length_mm=6000),
              vehicle(id='c',model='C',price=50000000,length_mm=6000)]
        result=CandidateService(FixedRanker(),cars).recommend(person(cost_importance=5))
        self.assertEqual({r['vehicle']['model'] for r in result['recommendations']},{'A','B','C'})
        self.assertEqual(result['recommendations'][0]['vehicle']['model'], 'A')
        self.assertEqual(result['budgetPolicy']['lower'],0)

    def test_weighted_ranking_includes_lower_distinct_models_and_never_exceeds_cap(self):
        cars=[vehicle(id=str(i),model=str(i),price=price) for i,price in enumerate((10000000,25000000,30000000,50000000,100000000))]
        p=person(purchase_price_ceiling=50000000)
        result=CandidateService(FixedRanker(),cars).recommend(p)
        self.assertEqual([r['vehicle']['price'] for r in result['recommendations']],[10000000,25000000,30000000])
        self.assertTrue(all(r['cost']['eligible'] for r in result['recommendations']))

    def test_fuel_preference_orders_equal_ml_scores_without_exceeding_cash(self):
        cars = [vehicle(id='ev', model='Electric', price=30000000, fuel='ELECTRIC', efficiency=5),
                vehicle(id='gas', model='Gas', price=45000000, fuel='GASOLINE', efficiency=12),
                vehicle(id='expensive', model='Expensive', price=60000000, fuel='ELECTRIC', efficiency=5)]
        service = CandidateService(FixedRanker(), cars)
        p = person(preferred_fuel='ELECTRIC', fuel_importance=5, cost_importance=1)
        electric = service.recommend(p)
        gas = service.recommend(replace(p, preferred_fuel='GASOLINE'))
        self.assertEqual(electric['recommendations'][0]['vehicle']['id'], 'ev')
        self.assertEqual(gas['recommendations'][0]['vehicle']['id'], 'gas')
        self.assertEqual(len(electric['recommendations']), 2)
        self.assertTrue(all(r['cost']['eligible'] for r in electric['recommendations']))
        self.assertNotIn('expensive', [r['vehicle']['id'] for r in electric['recommendations']])
        self.assertTrue(all(electric['recommendations'][i]['rankingScore'] >=
                            electric['recommendations'][i+1]['rankingScore']
                            for i in range(len(electric['recommendations'])-1)))

    def test_more_funds_raise_reference_price_band_when_catalog_has_candidates(self):
        cars=[vehicle(id=str(i),model=str(i),price=i*10000000) for i in range(1,16)]
        service=CandidateService(FixedRanker(),cars)
        p=person(monthly_income=3000000,monthly_expenses=1500000,monthly_savings=500000,
                 existing_monthly_payment=200000,liquid_assets=30000000,down_payment=0,emergency_reserve=5000000)
        low=service.recommend(p); high=service.recommend(replace(p,monthly_income=6000000,liquid_assets=60000000))
        self.assertGreater(high['budgetPolicy']['upper'],low['budgetPolicy']['upper'])
        self.assertTrue(all(r['vehicle']['price'] <= high['budgetPolicy']['financialUpper'] for r in high['recommendations']))

    def test_income_never_becomes_purchase_cash_or_raises_cash_budget(self):
        cars=[vehicle(id=str(i),model=str(i),price=i*10000000) for i in range(1,16)]
        service=CandidateService(FixedRanker(),cars)
        p=person(liquid_assets=30000000,down_payment=0,emergency_reserve=5000000)
        first=service.recommend(p); rich_salary=service.recommend(replace(p,monthly_income=30000000))
        self.assertEqual(first['budgetPolicy']['financialUpper'],25000000)
        self.assertEqual(first['budgetPolicy']['upper'],rich_salary['budgetPolicy']['upper'])
        self.assertTrue(all(r['vehicle']['price']<=25000000 for r in rich_salary['recommendations']))
        no_cash=replace(p,monthly_income=30000000,liquid_assets=0,emergency_reserve=0)
        self.assertEqual(service.recommend(no_cash)['recommendations'],[])

    def test_empty_or_sparse_financial_pool_is_not_filled_with_ineligible_cars(self):
        poor=person(monthly_income=1000000,monthly_expenses=1000000,monthly_savings=0,
                    existing_monthly_payment=0,liquid_assets=0,emergency_reserve=0,down_payment=0)
        service=CandidateService(FixedRanker(),[vehicle()])
        self.assertEqual(service.recommend(poor)['recommendations'],[])
        self.assertEqual(len(service.recommend(person())['recommendations']),1)


if __name__=='__main__': unittest.main()
