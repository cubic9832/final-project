import tempfile
import unittest
from pathlib import Path

import numpy as np

from legacy.recommender.dataset import NUMERIC_FEATURES
from legacy.recommender.preprocessing import Preprocessor
from legacy.tests.support import make_sample


class PreprocessingTest(unittest.TestCase):
    def test_fit_uses_only_the_rows_it_is_given(self):
        income = NUMERIC_FEATURES.index("개인_평균월실수령소득_원")
        train = [make_sample(income=1000), make_sample(income=1000)]
        preprocessor = Preprocessor()
        preprocessor.fit(train)
        self.assertAlmostEqual(preprocessor.means[income], float(np.log1p(1000)))
        transformed = preprocessor.transform([make_sample(income=1_000_000_000, split="평가")])
        self.assertNotAlmostEqual(transformed.numeric[0, income], 0.0)

    def test_constant_column_stays_finite(self):
        samples = [make_sample(distance=15000), make_sample(distance=15000, label="OWN002", model_name="K8")]
        preprocessor = Preprocessor()
        preprocessor.fit(samples)
        transformed = preprocessor.transform(samples)
        self.assertTrue(np.isfinite(transformed.numeric).all())
        distance = NUMERIC_FEATURES.index("연간_주행거리_km")
        self.assertAlmostEqual(transformed.numeric[0, distance], 0.0)

    def test_unknown_category_uses_the_extra_index(self):
        preprocessor = Preprocessor()
        preprocessor.fit([make_sample(purpose="출퇴근"), make_sample(purpose="출퇴근", label="OWN002", model_name="K8")])
        known = preprocessor.transform([make_sample(purpose="출퇴근")])
        unknown = preprocessor.transform([make_sample(purpose="여가")], include_labels=False)
        self.assertEqual(known.categorical[0, 0], 0)
        self.assertEqual(unknown.categorical[0, 0], 1)
        self.assertEqual(known.category_sizes[0], 2)

    def test_label_index_follows_sorted_code_and_rejects_unseen_label(self):
        preprocessor = Preprocessor()
        preprocessor.fit(
            [
                make_sample(label="OWN002", model_name="K8"),
                make_sample(label="OWN001", model_name="K5"),
            ]
        )
        prepared = preprocessor.transform(
            [
                make_sample(label="OWN002", model_name="K8"),
                make_sample(label="OWN001", model_name="K5"),
            ]
        )
        self.assertEqual([label.code for label in preprocessor.labels], ["OWN001", "OWN002"])
        self.assertEqual(prepared.labels.tolist(), [1, 0])
        with self.assertRaisesRegex(ValueError, "학습에 없는 라벨"):
            preprocessor.transform([make_sample(label="OWN003", model_name="스포티지")])

    def test_saved_preprocessor_reloads_the_same_transform(self):
        samples = [make_sample(), make_sample(label="OWN002", model_name="K8", purpose="여가")]
        preprocessor = Preprocessor()
        preprocessor.fit(samples)
        before = preprocessor.transform(samples)
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "preprocessor.json"
            preprocessor.save(path)
            loaded = Preprocessor.load(path)
        after = loaded.transform(samples)
        np.testing.assert_allclose(before.numeric, after.numeric)
        np.testing.assert_array_equal(before.categorical, after.categorical)
        self.assertEqual(before.labels.tolist(), after.labels.tolist())
