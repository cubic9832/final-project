import unittest
from dataclasses import replace

from test_preferences import FixedRanker
from test_vehicle_matching import person,vehicle
from vehicle_matching.finance import assess
from vehicle_matching.preferences import integrated_score
from vehicle_matching.service import CandidateService


class MonthlyAffordabilityTests(unittest.TestCase):
    def test_income_changes_monthly_pressure_and_preference_ranking_without_raising_cash_budget(self):
        gas=vehicle(id='gas',model='Gas',price=40000000,efficiency=4,fuel='GASOLINE',length_mm=4500)
        electric=vehicle(id='electric',model='Electric',price=40000000,efficiency=5,fuel='ELECTRIC',length_mm=4500)
        service=CandidateService(FixedRanker(),[gas,electric])
        low=person(monthly_income=2500000,monthly_expenses=1450000,existing_monthly_payment=200000,
                   monthly_savings=0,preferred_fuel='GASOLINE',cost_importance=5,fuel_importance=1)
        high=replace(low,monthly_income=7500000)
        a,b=service.recommend(low),service.recommend(high)
        self.assertEqual(a['recommendations'][0]['vehicle']['id'],'electric')
        self.assertEqual(b['recommendations'][0]['vehicle']['id'],'gas')
        self.assertEqual(a['budgetPolicy']['financialUpper'],b['budgetPolicy']['financialUpper'])
        self.assertTrue(all(r['cost']['eligible'] for result in (a,b) for r in result['recommendations']))

    def test_savings_debt_and_protected_buffer_reduce_spendable_capacity(self):
        p=person(financing_mode='recommendation',minimum_buffer=300000)
        v=vehicle()
        first=integrated_score(p,v,assess(p,v),.5)['monthlyAffordability']
        changed=replace(p,monthly_savings=p.monthly_savings+200000,existing_monthly_payment=p.existing_monthly_payment+100000)
        second=integrated_score(changed,v,assess(changed,v),.5)['monthlyAffordability']
        self.assertEqual(first['spendableMonthly']-second['spendableMonthly'],300000)
        self.assertGreater(second['runningCostRatio'],first['runningCostRatio'])
        self.assertLess(second['score'],first['score'])

    def test_monthly_boundary_remains_hard_and_zero_capacity_has_no_recommendation(self):
        p=person(financing_mode='recommendation')
        v=vehicle()
        cost=assess(p,v)
        exact=replace(p,minimum_buffer=cost['remaining_monthly'])
        score=integrated_score(exact,v,assess(exact,v),.5)['monthlyAffordability']
        self.assertEqual(score['score'],0)
        self.assertTrue(assess(exact,v)['eligible'])
        self.assertFalse(assess(replace(exact,minimum_buffer=exact.minimum_buffer+1),v)['eligible'])
        poor=replace(p,monthly_income=p.monthly_expenses+p.existing_monthly_payment+p.monthly_savings)
        self.assertEqual(CandidateService(FixedRanker(),[v]).recommend(poor)['recommendations'],[])


if __name__=='__main__': unittest.main()
