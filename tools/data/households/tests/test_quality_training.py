import random
import unittest
from dataclasses import replace

from tools.data.households.build_quality_training import holdout, new_group, small_repair
from tools.data.households.quality_choice_policy import QualityPolicy
from tools.data.households.tests.test_preference_relabeling import vehicle
from tools.data.households.relabel_preference_choices import FEATURES, PREFERENCES


class QualityTrainingTests(unittest.TestCase):
    def setUp(self):
        self.row = dict(zip(FEATURES,('8000000','30000000','500000','1000000','1000000','100000','15000','출퇴근')))
        self.row.update(dict(zip(PREFERENCES,('3','작음','가솔린','2'))))
        self.row['프로필_식별자']='TEST'
        self.context={'savings':1000000,'reserve':5000000,'funds':20000000,'buffer':300000,'ceiling':0}
        self.policy=QualityPolicy([vehicle('A',price=30000000),vehicle('B',price=31000000),
                                   vehicle('C',price=20000000,fuel='ELECTRIC',length=4500)])

    def test_both_preferences_take_priority_when_multiple_candidates_exist(self):
        pool,reason=self.policy.pool(self.row,self.context)
        self.assertIsNotNone(pool,reason)
        for seed in range(10):
            selected=self.policy.select(self.row,self.context,pool,seed)
            self.assertIn(selected['vehicle'].id,('A','B'))
            self.assertGreaterEqual(selected['remaining']-self.context['buffer'],selected['required_headroom'])
            self.assertGreaterEqual(selected['comparison_models'],2)

    def test_insufficient_headroom_or_single_candidate_is_rejected(self):
        pool,_=self.policy.pool({**self.row,FEATURES[0]:'2700000'},self.context)
        self.assertIsNone(pool)
        one=QualityPolicy([vehicle('A')])
        self.assertIsNone(one.pool(self.row,self.context)[0])

    def test_large_financial_repairs_are_not_applied_to_legacy_rows(self):
        original={**self.row,FEATURES[0]:'1000000'}
        result,pool,delta,_=small_repair(self.policy,original,self.context)
        self.assertIsNone(result)
        self.assertIsNone(pool)
        self.assertEqual(original[FEATURES[0]],'1000000')

    def test_generated_inputs_are_reproducible_and_have_no_chosen_vehicle(self):
        a=new_group(100,random.Random(1),random.Random(2))
        b=new_group(100,random.Random(1),random.Random(2))
        self.assertEqual(a,b)
        people,context=a
        for row in people:
            self.assertEqual(row['선택차량_라벨코드'],'UNASSIGNED')
            self.assertEqual([row[k] for k in FEATURES[:6]],[people[0][k] for k in FEATURES[:6]])
            self.assertLessEqual(context['funds']+context['reserve'],int(row[FEATURES[1]]))

    def test_unknown_size_is_pending_evidence_not_a_zero_score_vehicle_rejection(self):
        policy=QualityPolicy([vehicle('A'),vehicle('B',price=21000000),vehicle('C',price=22000000),
                              replace(vehicle('UNKNOWN'),length_mm=None)])
        pool,reason=policy.pool(self.row,self.context)
        self.assertIsNotNone(pool,reason)
        self.assertEqual(pool['unknown_pending'],1)
        for seed in range(5):
            self.assertNotEqual(policy.select(self.row,self.context,pool,seed)['vehicle'].id,'UNKNOWN')

    def test_phev_fuel_preference_is_hybrid_without_invented_electric_savings(self):
        policy=QualityPolicy([replace(vehicle('PHEV1',length=4500),original_fuel='PHEV'),
                              replace(vehicle('PHEV2',price=21000000,length=4500),original_fuel='PHEV'),
                              vehicle('GAS',price=22000000,length=4500)])
        row={**self.row,PREFERENCES[1]:'중간',PREFERENCES[2]:'하이브리드'}
        pool,reason=policy.pool(row,self.context)
        self.assertIsNotNone(pool,reason)
        selected=policy.select(row,self.context,pool,1)
        self.assertEqual(selected['semantic_fuel'],'하이브리드')
        self.assertEqual(selected['vehicle'].fuel,'GASOLINE')


if __name__=='__main__':
    unittest.main()
