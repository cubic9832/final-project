"""End-to-end scenario training, persisted inference and split isolation."""
import contextlib
import io
import json
from pathlib import Path
import tempfile
import unittest

import numpy as np

from vehicle_matching.catalog import ROOT
from vehicle_matching.scenario_features import FEATURE_NAMES
from vehicle_matching.scenario_model import ScenarioRanker
from vehicle_matching.train_scenario_choices import normalization, train
from tools.data.households.generate_scenario_population import DEFAULT_CONFIG, generate


class ScenarioTrainingTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp_root = ROOT/'tmp/scenario-training-tests'
        cls.temp_root.mkdir(parents=True,exist_ok=True)

    def test_full_training_saved_inference_and_checkpoint_integrity(self):
        with tempfile.TemporaryDirectory(dir=self.temp_root) as folder:
            data,output = Path(folder)/'data',Path(folder)/'model'
            with contextlib.redirect_stdout(io.StringIO()):
                generate(data,profiles=60,pairs_per_user=4,shard_size=20,seed=41,
                         config_path=DEFAULT_CONFIG.with_name('scenario_population_config.json'))
                report = train(data,output,epochs=2,batch_size=64,threads=1)
            self.assertEqual(report['saved_inference_verification']['status'],'passed')
            self.assertEqual(report['test']['mlp']['comparisons'],report['partitions']['test']['comparisons'])
            best = min(report['history'],key=lambda row:row['validation']['log_loss'])
            self.assertEqual(report['training']['selected_epoch'],best['epoch'])
            loaded = ScenarioRanker.load(output)
            self.assertEqual(len(loaded.mean),68)
            self.assertTrue(np.isfinite(loaded.score_features(np.zeros((2,len(FEATURE_NAMES)),dtype=np.float32))).all())
            with self.assertRaisesRegex(ValueError,'68-column'):
                loaded.score_features(np.zeros((2,52),dtype=np.float32))
            with self.assertRaises(FileExistsError):
                train(data,output,epochs=2)
            (output/'catalog.json').write_text('[]',encoding='utf-8')
            with self.assertRaisesRegex(ValueError,'checksum mismatch'):
                ScenarioRanker.load(output)

    def test_normalization_uses_training_rows_only(self):
        with tempfile.TemporaryDirectory(dir=self.temp_root) as folder:
            data = Path(folder)
            shard = data/'shard-0000'; shard.mkdir()
            for role,level in [('train',2),('validation',1000),('test',-1000)]:
                np.savez(shard/f'{role}_choices.npz',features=np.full((2,len(FEATURE_NAMES)),level,dtype=np.float32),
                         comparisons=np.array([[0,1]]),labels=np.array([1],dtype=np.float32))
            mean,scale,minimum,maximum = normalization(data,{'shards':[{'directory':shard.name}]})
            np.testing.assert_array_equal(mean,np.full(len(FEATURE_NAMES),2))
            self.assertTrue(np.all(scale>0))
            self.assertEqual(float(minimum.min()),2)
            self.assertEqual(float(maximum.max()),2)


if __name__=='__main__':
    unittest.main()
