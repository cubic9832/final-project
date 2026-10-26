import copy
import unittest
from collections import Counter

import numpy as np

from tools.data.households.expand_quality_training import CoveragePolicy, coverage_candidates
from tools.data.households.tests import test_quality_training


class QualityExpansionTests(unittest.TestCase):
    def setUp(self):
        fixture=test_quality_training.QualityTrainingTests()
        fixture.setUp()
        self.row,self.context=fixture.row,fixture.context
        self.policy=CoveragePolicy(fixture.policy.vehicles)

    def test_rare_selection_stays_in_original_preference_pool_and_preserves_inputs(self):
        pool,_=self.policy.pool(self.row,self.context)
        labels={v.id:v.id for v in self.policy.vehicles}
        counts={'학습':Counter({'A':0,'B':1000,'C':0})}
        candidates=coverage_candidates(pool,self.policy,labels,counts,'학습')
        self.assertEqual([self.policy.vehicles[self.policy.starts[m]].id for m in candidates],['A'])
        before=copy.deepcopy((self.row,self.context))
        pool['coverage_shortlist']=candidates
        selected=self.policy.select(self.row,self.context,pool,7)
        self.assertEqual(selected['vehicle'].id,'A')
        self.assertEqual(selected['comparison_models'],len(pool['shortlist']))
        self.assertEqual((self.row,self.context),before)

    def test_no_coverage_candidate_does_not_relax_feasibility_or_force_another_label(self):
        pool,_=self.policy.pool(self.row,self.context)
        labels={v.id:v.id for v in self.policy.vehicles}
        counts={'평가':Counter({'A':100,'B':100,'C':0})}
        self.assertEqual(len(coverage_candidates(pool,self.policy,labels,counts,'평가')),0)
        self.assertTrue(all(np.isfinite(pool['model_scores'][m]) for m in pool['shortlist']))


if __name__=='__main__': unittest.main()
