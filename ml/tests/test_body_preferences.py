import unittest
from dataclasses import replace

from vehicle_matching.body_types import apply_body_types
from vehicle_matching.explanations import preference_evidence
from vehicle_matching.finance import assess
from vehicle_matching.preferences import integrated_score
from test_vehicle_matching import person, vehicle
from test_preferences import FixedRanker
from vehicle_matching.service import CandidateService


class BodyPreferenceTests(unittest.TestCase):
    def test_body_preference_orders_equal_ml_scores_without_overriding_cash(self):
        sedan=vehicle(id='sedan',model='Sedan',price=30000000,body_type='SEDAN')
        suv=replace(sedan,id='suv',model='SUV',body_type='SUV')
        p=person(preferred_body_type='SUV',body_importance=5)
        result=CandidateService(FixedRanker(),[sedan,suv]).recommend(p)
        self.assertEqual(result['recommendations'][0]['vehicle']['id'],'suv')
        self.assertEqual(len(result['recommendations']),2)
        self.assertEqual(CandidateService(FixedRanker(),[suv]).recommend(replace(p,liquid_assets=1000000,down_payment=0,emergency_reserve=0))['recommendations'],[])

    def test_unknown_is_not_match_and_any_has_no_score(self):
        p=person(preferred_body_type='SUV')
        car=vehicle()
        score=integrated_score(p,car,assess(p,car),.5)
        item=next(v for v in preference_evidence(p,car,score['components']) if v['key']=='body')
        self.assertEqual(item['status'],'unknown')
        self.assertFalse(any(v['key']=='body' for v in integrated_score(replace(p,preferred_body_type='any'),car,assess(p,car),.5)['components']))

    def test_registry_distinguishes_body_from_size_and_model_name_keywords(self):
        examples=[vehicle(brand='현대',model='캐스퍼'), vehicle(brand='기아',model='EV4'),vehicle(brand='제네시스',model='G70 Shooting Brake'),vehicle(brand='제네시스',model='GV80 Coupe'),vehicle(brand='기아',model='레이')]
        self.assertEqual([v.body_type for v in apply_body_types(examples)],['SUV','SEDAN','WAGON','SUV','BOX'])
        with self.assertRaises(ValueError):apply_body_types([vehicle(brand='unknown',model='SUV')])

