import unittest

import numpy as np

from experiments.train_quality_choices import NUMERIC, CATEGORIES, prepare, metrics


class QualityExperimentTest(unittest.TestCase):
    def test_preprocessing_uses_training_only_and_excludes_target_metadata(self):
        def row(value,category):
            result={key:str(value) for key in NUMERIC}
            result.update({key:category for key in CATEGORIES})
            result['선택차량_라벨코드']='A'
            result['선택차량가격_원']='999999999'
            return result
        train=[row(10,'known'),row(20,'known')]
        rows={'학습':train,'검증':[row(100000,'unseen')],'평가':[row(30,'known')]}
        prepared,metadata=prepare(rows)
        expected=np.log1p([10,20]).mean()
        self.assertAlmostEqual(metadata['log1p_mean'][0],expected)
        self.assertTrue(np.all(prepared['검증'].categorical==0))
        self.assertNotIn('선택차량가격_원',metadata['numeric'])
        self.assertTrue(np.all(np.isfinite(prepared['검증'].numeric)))

    def test_metrics_distinguish_popularity_from_rare_class_recall(self):
        probs=np.array([[.9,.1],[.9,.1],[.9,.1],[.9,.1]])
        result=metrics(probs,np.array([0,0,0,1]))
        self.assertEqual(result['top1'],.75)
        self.assertEqual(result['macro_recall'],.5)


if __name__=='__main__': unittest.main()
