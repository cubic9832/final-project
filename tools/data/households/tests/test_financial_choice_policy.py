import unittest

from tools.data.households.financial_choice_policy import FinancialChoicePolicy,WEIGHTS
from tools.data.households.tests import test_quality_training
from tools.data.households.tests.test_preference_relabeling import vehicle


class FinancialChoicePolicyTests(unittest.TestCase):
    def setUp(self):
        fixture=test_quality_training.QualityTrainingTests(); fixture.setUp()
        self.row={**fixture.row,**dict(zip(WEIGHTS,('3','3','3','1')))}
        self.context=fixture.context

    def test_size_fuel_seats_and_missing_dimensions_never_remove_financial_candidates(self):
        policy=FinancialChoicePolicy([vehicle('A'),vehicle('B',length=6000,seats=2,fuel='ELECTRIC'),
                                      vehicle('C',length=None,seats=2)])
        pool,reason=policy.pool(self.row,self.context)
        self.assertIsNotNone(pool,reason)
        self.assertEqual(pool['eligible_models'],3)
        self.assertEqual(len(policy.top_three(pool)),3)
        self.assertEqual(len(pool['shortlist']),3)

    def test_price_ceiling_can_leave_one_candidate_and_income_shortfall_leaves_none(self):
        policy=FinancialChoicePolicy([vehicle('A',price=10000000),vehicle('B',price=21000000),vehicle('C',price=22000000)])
        pool,_=policy.pool(self.row,{**self.context,'ceiling':15000000})
        self.assertEqual(len(policy.top_three(pool)),1)
        self.assertIsNone(policy.pool({**self.row,'개인_평균월실수령소득_원':'1'},self.context)[0])


if __name__=='__main__': unittest.main()
