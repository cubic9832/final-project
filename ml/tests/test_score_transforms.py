import unittest

import numpy as np

from vehicle_matching.score_transforms import fit_sigmoid, transform_scores


class ScoreTransformTests(unittest.TestCase):
    def test_large_logits_preserve_order_after_calibration(self):
        raw = np.array([94.3815,94.5641,94.6654])
        self.assertEqual(len(set(transform_scores(raw,'legacy_sigmoid'))),1)
        for method in ('minmax','calibrated_sigmoid','softmax'):
            scores = transform_scores(raw,method,center=94.5,temperature=.2)
            self.assertTrue(np.all(np.diff(scores)>0))
            self.assertTrue(np.all((scores>=0)&(scores<=1)))

    def test_constant_and_empty_candidates_do_not_create_false_preferences(self):
        np.testing.assert_array_equal(transform_scores([8,8],'minmax'),[.5,.5])
        for method in ('minmax','calibrated_sigmoid','softmax'):
            self.assertEqual(len(transform_scores([],method)),0)
            scores=transform_scores([3,3],method)
            self.assertEqual(scores[0],scores[1])
        np.testing.assert_allclose(transform_scores([10000,10001],'softmax').sum(),1)
        with self.assertRaises(ValueError):transform_scores([1],'softmax',temperature=0)

    def test_fixed_calibration_does_not_depend_on_candidate_membership(self):
        raw=[60,80,94]
        scores=transform_scores(raw,'calibrated_sigmoid',center=70,temperature=10)
        subset=transform_scores(raw[1:],'calibrated_sigmoid',center=70,temperature=10)
        np.testing.assert_array_equal(scores[1:],subset)
        self.assertNotEqual(transform_scores(raw,'minmax')[1],transform_scores(raw[1:],'minmax')[0])

    def test_fitted_calibration_recovers_soft_rule_targets_without_refitting_model(self):
        raw=np.linspace(50,150,100)
        target=transform_scores(raw,'calibrated_sigmoid',center=80,temperature=20)
        parameters=fit_sigmoid(raw,target,np.ones(len(raw)))
        calibrated=transform_scores(raw,'calibrated_sigmoid',center=parameters['center'],temperature=parameters['temperature'])
        self.assertLess(float(np.max(np.abs(calibrated-target))),.001)


if __name__=='__main__':unittest.main()
