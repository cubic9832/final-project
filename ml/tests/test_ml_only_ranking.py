import unittest
from dataclasses import replace

import numpy as np
import torch
from torch import nn

from test_vehicle_matching import person, vehicle
from vehicle_matching.preference_model import FEATURE_NAMES, PreferenceRanker
from vehicle_matching.service import CandidateService


class MlOnlyRankingTests(unittest.TestCase):
    def ranker(self):
        # Deliberately prefer length with large logits that all saturate to 1.
        net = nn.Linear(len(FEATURE_NAMES), 1)
        with torch.no_grad():
            net.weight.zero_()
            net.weight[0, FEATURE_NAMES.index('length')] = 10
            net.bias.fill_(20)
        return PreferenceRanker(net, np.zeros(len(FEATURE_NAMES)), np.ones(len(FEATURE_NAMES)),
                                np.full(len(FEATURE_NAMES), -1e10), np.full(len(FEATURE_NAMES), 1e10))

    def test_preferences_override_raw_order_without_losing_raw_score_precision(self):
        small = vehicle(id='a-small', model='Small', price=20000000, length_mm=3900, seats=5)
        large = replace(small, id='z-large', model='Large', price=30000000, length_mm=5000)
        p = person(preferred_size='small', space_importance=5, cost_importance=5, liquid_assets=30000000, emergency_reserve=0, down_payment=0)
        ranker = self.ranker()
        self.assertEqual(ranker.predict(p, [small, large])[0], [1., 1.])
        result = CandidateService(ranker, [small, large]).recommend(p)
        rows = result['recommendations']
        self.assertEqual([r['vehicle']['id'] for r in rows], ['a-small', 'z-large'])
        self.assertLess(rows[0]['rankingScore'], rows[1]['rankingScore'])
        self.assertGreater(rows[0]['rankingScore'], 1)
        self.assertFalse(rows[0]['preferenceAssessment']['rankingApplied'])
        self.assertNotIn('integratedScore', rows[0])
        self.assertNotIn('total', rows[0]['preferenceAssessment'])
        self.assertTrue(all('contribution' not in c for c in rows[0]['preferenceAssessment']['components']))
        self.assertEqual(rows[0]['rankingComparison']['status'], 'preference-priority')
        self.assertNotIn('contributionDifferences', rows[0]['rankingComparison'])

    def test_ml_cannot_override_finances_and_best_trim_is_chosen_per_model(self):
        small = vehicle(id='small', model='Same', price=20000000, length_mm=3900, seats=5)
        best_trim = replace(small, id='best', length_mm=4900)
        unaffordable = replace(small, id='too-expensive', model='Unaffordable', price=1e10, length_mm=6000)
        result = CandidateService(self.ranker(), [small, best_trim, unaffordable]).recommend(person(purchase_price_ceiling=20000000), k=9)
        self.assertEqual([r['vehicle']['id'] for r in result['recommendations']], ['best'])
        self.assertTrue(result['recommendations'][0]['cost']['eligible'])

    def test_negative_logits_and_empty_pool_are_valid(self):
        ranker = self.ranker()
        with torch.no_grad():
            ranker.net.bias.fill_(-100)
        car = vehicle(length_mm=4000, seats=5)
        result = CandidateService(ranker, [car]).recommend(person())
        self.assertLess(result['recommendations'][0]['rankingScore'], 0)
        self.assertEqual(CandidateService(ranker, []).recommend(person())['recommendations'], [])


if __name__ == '__main__':
    unittest.main()
