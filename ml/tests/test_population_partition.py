import tempfile
import unittest
from pathlib import Path

import numpy as np

from vehicle_matching.catalog import ROOT
from vehicle_matching.partition_preference_population import compact_pairs, partition
from vehicle_matching.train_preference_population import generate
from vehicle_matching.audit_preference_population import audit
from test_vehicle_matching import vehicle


class PopulationPartitionTests(unittest.TestCase):
    def test_compaction_preserves_pair_targets_and_drops_unused_candidates(self):
        data={'features':np.arange(20).reshape(5,4),'targets':np.array([.1,.4,.8,.2,.9]),
              'pairs':np.array([[2,1],[4,3]]),'splits':np.array([0,0,0,2,2]),
              'profile_ids':np.array([5,5,5,7,7]),'vehicle_indices':np.arange(5)}
        result=compact_pairs(data,0)
        np.testing.assert_array_equal(result['source_candidate_indices'],[1,2])
        np.testing.assert_array_equal(result['pairs'],[[1,0]])
        np.testing.assert_array_equal(result['targets'][result['pairs']],data['targets'][[[2,1]]])

    def test_all_cases_partition_once_without_changing_original_splits_or_cells(self):
        models = ('코나', '베뉴', '투싼', '싼타페', '팰리세이드', '캐스퍼', '쏘나타 디 엣지', '디 올 뉴 아반떼', '더 뉴 그랜저', '아이오닉 5')
        cars=[vehicle(id=str(i),brand='현대',model=models[i],price=20000000+i*1000000,length_mm=4000+i*50,seats=5) for i in range(10)]
        with tempfile.TemporaryDirectory(dir=ROOT/'tmp') as temp:
            source=Path(temp)/'source';destination=Path(temp)/'partitioned'
            generate(source,cars,42,count=80)
            audit(source)
            result=partition(source,destination)
            self.assertEqual(sum(result['partition_counts'].values()),80)
            self.assertGreater(result['partition_counts']['financial'],0)
            self.assertEqual(result['missing_cases'],0)
            self.assertEqual(result['original_cell_changes'],0)
            self.assertEqual(result['source_split_changes'],0)
            for role in ('train','validation','test'):
                with np.load(destination/f'{role}_pairs.npz') as data:
                    self.assertTrue(np.all(data['targets'][data['pairs'][:,0]]>data['targets'][data['pairs'][:,1]]))
            with self.assertRaises(ValueError):partition(source,source)
            with self.assertRaises(ValueError):partition(source,destination)
