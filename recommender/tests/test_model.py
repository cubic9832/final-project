import json
import tempfile
import unittest
from pathlib import Path

import numpy as np

from recommender.artifact import read_report
from recommender.dataset import NUMERIC_FEATURES, load_dataset
from recommender.evaluate import evaluate_run
from recommender.metrics import top_k_hit_rate
from recommender.models.mlp import MlpConfig, MlpRanker
from recommender.predict import recommend
from recommender.preprocessing import Preprocessor
from recommender.ranking import select_best
from recommender.train import train
from support import make_sample, profile_from_sample, write_tables


class ModelTest(unittest.TestCase):
    def test_top3_counts_a_hit_only_inside_the_first_three(self):
        probabilities = np.array(
            [
                [0.1, 0.2, 0.3, 0.4],
                [0.5, 0.4, 0.05, 0.05],
            ]
        )
        labels = np.array([0, 0])
        self.assertEqual(top_k_hit_rate(probabilities, labels, k=3), 0.5)

    def test_select_best_keeps_the_higher_score_and_the_earlier_tie(self):
        first, second, third = object(), object(), object()
        chosen, score = select_best([(first, 0.2), (second, 0.2), (third, 0.1)])
        self.assertIs(chosen, first)
        self.assertEqual(score, 0.2)
        chosen, score = select_best([(first, 0.2), (second, 0.4)])
        self.assertIs(chosen, second)
        self.assertEqual(score, 0.4)
        with self.assertRaisesRegex(ValueError, "비교할 모델이 없습니다"):
            select_best([])

    def test_probabilities_match_label_count_sum_to_one_and_reload(self):
        samples = [make_sample(), make_sample(label="OWN002", model_name="K8")]
        preprocessor = Preprocessor()
        preprocessor.fit(samples)
        prepared = preprocessor.transform(samples)
        ranker = MlpRanker(MlpConfig(hidden=(8, 4), epochs=2, batch_size=2, dropout=0.0))
        ranker.fit(prepared, prepared)
        probabilities = ranker.predict_proba(prepared)
        self.assertEqual(probabilities.shape, (len(samples), prepared.class_count))
        np.testing.assert_allclose(probabilities.sum(axis=1), np.ones(len(samples)), atol=1e-5)
        with tempfile.TemporaryDirectory() as directory:
            ranker.save(Path(directory))
            loaded = MlpRanker.load(Path(directory))
        np.testing.assert_allclose(probabilities, loaded.predict_proba(prepared), atol=1e-6)

    def test_training_fits_on_train_split_and_recommends_top_k(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            data = root / "data"
            data.mkdir()
            write_tables(data, _tiny_rows())
            run = train(
                data,
                segment="domestic-car",
                run_dir=root / "run",
                candidates=[
                    MlpRanker(MlpConfig(hidden=(8, 4), epochs=2, batch_size=8, dropout=0.0, lr=1e-2)),
                    MlpRanker(MlpConfig(hidden=(16, 8), epochs=2, batch_size=8, dropout=0.0, lr=1e-2)),
                ],
            )
            report = read_report(run)
            self.assertEqual(report["selected"]["hidden"], [8, 4])
            income = NUMERIC_FEATURES.index("개인_연간세전소득_원")
            saved = json.loads((run / "preprocessor.json").read_text(encoding="utf-8"))
            self.assertAlmostEqual(saved["means"][income], float(np.log1p(1000)))

            dataset = load_dataset(data)
            profile = profile_from_sample(dataset.train[0])
            leaked = dict(profile)
            leaked["보유차량_라벨코드"] = "OWN999"
            leaked["개인_대출잔액_원"] = 999999
            results = recommend(run, profile, k=3)
            self.assertEqual(results, recommend(run, leaked, k=3))
            self.assertEqual(len(results), 2)
            self.assertGreaterEqual(results[0]["확률"], results[1]["확률"])
            self.assertAlmostEqual(results[0]["확률"] + results[1]["확률"], 1.0, places=5)
            self.assertEqual({item["라벨코드"] for item in results}, {"OWN001", "OWN002"})
            self.assertEqual(set(results[0]), {"라벨코드", "모델", "차체", "차급", "확률"})
            self.assertEqual(evaluate_run(run, data)["top3"], report["evaluation"]["top3"])
            with self.assertRaisesRegex(ValueError, "k는 1 이상"):
                recommend(run, profile, k=0)
            with self.assertRaisesRegex(ValueError, "파일이 없습니다"):
                recommend(root / "missing", profile, k=1)


def _tiny_rows() -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for _ in range(4):
        rows.append({"split": "학습", "label": "OWN001", "model": "K5", "income": 1000, "loan": 10})
        rows.append(
            {
                "split": "학습",
                "label": "OWN002",
                "model": "K8",
                "body": "세단",
                "grade": "준대형",
                "income": 1000,
                "loan": 10,
            }
        )
    for split, income in (("검증", 5_000_000_000), ("평가", 9_000_000_000)):
        rows.append({"split": split, "label": "OWN001", "model": "K5", "income": income, "loan": 10})
        rows.append(
            {
                "split": split,
                "label": "OWN002",
                "model": "K8",
                "body": "세단",
                "grade": "준대형",
                "income": income,
                "loan": 10,
            }
        )
    return rows
