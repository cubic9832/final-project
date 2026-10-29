import tempfile
import unittest
from dataclasses import replace
from pathlib import Path

import numpy as np

from test_vehicle_matching import person, vehicle
from vehicle_matching.preference_model import encode_preference, preference_network, PreferenceRanker
from vehicle_matching.model import PairRanker
from vehicle_matching.train_preference_population import generate, independent_eligible, teacher
from vehicle_matching.finance import assess
from vehicle_matching.catalog import ROOT


class PreferencePopulationTests(unittest.TestCase):
    def test_features_change_with_explicit_preferences_not_purpose(self):
        p=person(financing_mode='recommendation')
        car=vehicle(length_mm=4000,seats=5)
        base=encode_preference(p,car)
        np.testing.assert_array_equal(base,encode_preference(replace(p,purpose='family',purpose_importance=5),car))
        self.assertFalse(np.array_equal(base,encode_preference(replace(p,preferred_size='large',space_importance=5),car)))
        self.assertFalse(np.array_equal(base,encode_preference(replace(p,minimum_seats=7,seating_importance=5),car)))

    def test_generator_separates_groups_preserves_unaffordable_cases_and_pair_direction(self):
        cars=[vehicle(id=str(i),brand='현대',model=('코나','베뉴','투싼','싼타페','팰리세이드','캐스퍼','쏘나타 디 엣지','디 올 뉴 아반떼','더 뉴 그랜저','아이오닉 5')[i],price=20000000+i*1000000,length_mm=4000+i*50,seats=5) for i in range(10)]
        with tempfile.TemporaryDirectory(dir=ROOT/'tmp') as temp:
            x,y,pairs,splits,records,report=generate(Path(temp)/'data',cars,42,count=80)
        self.assertEqual(len(records),80)
        group_splits={}
        for record in records:
            self.assertEqual(group_splits.setdefault(record['group'],record['split']),record['split'])
            self.assertEqual(record['profile']['monthly_savings'],0)
            self.assertEqual(record['profile']['months'],0)
        self.assertGreater(report['counts']['no_choice_cases'],0)
        self.assertTrue(np.all(y[pairs[:,0]]>y[pairs[:,1]]))
        self.assertTrue(np.all(splits[pairs[:,0]]==splits[pairs[:,1]]))

    def test_artifact_loader_keeps_new_model_separate_from_legacy(self):
        p=person(financing_mode='recommendation')
        car=vehicle(length_mm=4000,seats=5)
        x=encode_preference(p,car)
        model=PreferenceRanker(preference_network(),np.zeros_like(x),np.ones_like(x),x-1,x+1)
        with tempfile.TemporaryDirectory(dir=ROOT/'tmp') as temp:
            model.save(temp,{'test':True})
            loaded=PairRanker.load(temp)
            self.assertIsInstance(loaded,PreferenceRanker)
            self.assertEqual(model.predict(p,[car]),loaded.predict(p,[car]))

    def test_teacher_never_rewards_price_alone_and_independent_audit_includes_assets(self):
        p=person(financing_mode='recommendation',liquid_assets=100000000,emergency_reserve=0,
                 monthly_income=2000000,monthly_expenses=2200000,monthly_savings=0,existing_monthly_payment=0,cost_importance=1)
        cheap=vehicle(price=30000000,length_mm=4500,seats=5)
        expensive=replace(cheap,price=40000000)
        self.assertGreater(teacher(p,cheap,assess(p,cheap)),teacher(p,expensive,assess(p,expensive)))
        self.assertTrue(independent_eligible(p,cheap,assess(p,cheap)))
        self.assertFalse(independent_eligible(replace(p,liquid_assets=30000000),cheap,assess(replace(p,liquid_assets=30000000),cheap)))
