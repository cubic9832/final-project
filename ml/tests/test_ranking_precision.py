import unittest
import numpy as np
import torch
from vehicle_matching.preference_model import PreferenceRanker,FEATURE_NAMES
from test_vehicle_matching import person,vehicle

class RankingPrecisionTests(unittest.TestCase):
    def test_ranking_preserves_order_when_bounded_scores_saturate(self):
        net=torch.nn.Linear(len(FEATURE_NAMES),1)
        with torch.no_grad():
            net.weight.zero_();net.bias.zero_();net.weight[0,4]=2
        model=PreferenceRanker(net,np.zeros(len(FEATURE_NAMES),dtype=np.float32),np.ones(len(FEATURE_NAMES),dtype=np.float32),np.zeros(len(FEATURE_NAMES)),np.ones(len(FEATURE_NAMES))*100)
        p=person(liquid_assets=100000000,down_payment=0,emergency_reserve=0,monthly_savings=0,financing_mode='recommendation')
        cars=[vehicle(price=30000000),vehicle(price=40000000)]
        bounded,_=model.predict(p,cars)
        self.assertEqual(bounded[0],bounded[1])
        raw=model.ranking_scores(p,cars)
        self.assertLess(raw[0],raw[1])
        self.assertEqual(model.ranking_scores(p,[]),[])
