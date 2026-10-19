import tempfile
import unittest
from pathlib import Path

from recommender.dataset import (
    FEATURE_COLUMNS,
    LEAKED_COLUMNS,
    LOAN_BEFORE,
    NUMERIC_FEATURES,
    SEGMENTS,
    feature_columns,
    load_dataset,
    profile_sample,
    seed_directory,
)
from support import write_tables


class DatasetTest(unittest.TestCase):
    def test_joint_dataset_has_both_catalogs_with_original_splits(self):
        dataset = load_dataset(seed_directory('all-cars'))
        self.assertEqual((len(dataset.train), len(dataset.valid), len(dataset.evaluation)), (11200, 2400, 2400))
        self.assertEqual(len({row.label_code for row in dataset.train}), 20)

    def test_monthly_debt_payment_uses_pre_purchase_audit_not_post_purchase_owner_value(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            write_tables(root, [_row(split, 'OWN001', payment=12345, leaked_payment=999999)
                                for split in ('학습', '검증', '평가')])
            row = load_dataset(root).train[0]
            self.assertEqual(row.numeric[NUMERIC_FEATURES.index('기존월상환액_보정전_원')], 12345)
            self.assertNotIn(999999, row.numeric)

    def test_seed_segments_join_on_profile_and_keep_pre_purchase_loan(self):
        for segment in SEGMENTS:
            dataset = load_dataset(seed_directory(segment))
            self.assertGreater(len(dataset.train), 0)
            self.assertGreater(len(dataset.valid), 0)
            self.assertGreater(len(dataset.evaluation), 0)
            self.assertEqual(len(dataset.train[0].numeric), len(NUMERIC_FEATURES))
            self.assertTrue(all(split == "학습" for split in _splits(dataset.train)))

    def test_feature_columns_leave_out_purchase_outcomes(self):
        self.assertFalse(set(feature_columns()) & set(LEAKED_COLUMNS))
        self.assertFalse(set(FEATURE_COLUMNS) & set(LEAKED_COLUMNS))
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            write_tables(
                root,
                [
                    _row("학습", "OWN001", loan=12345, leaked_loan=999999, price=888),
                    _row("검증", "OWN001", loan=10),
                    _row("평가", "OWN001", loan=10),
                ],
            )
            dataset = load_dataset(root)
            numeric = dataset.train[0].numeric
            self.assertEqual(numeric[NUMERIC_FEATURES.index(LOAN_BEFORE)], 12345.0)
            self.assertNotIn(999999.0, numeric)
            self.assertNotIn(888.0, numeric)

    def test_profile_input_ignores_label_and_post_purchase_loan(self):
        profile = {
            name: 1
            for name in NUMERIC_FEATURES
        }
        profile.update({"성별": "남성", "직업_유형": "근로자", "차량_이용목적": "출퇴근"})
        leaked = dict(profile)
        leaked["보유차량_라벨코드"] = "OWN999"
        leaked["개인_대출잔액_원"] = 999999
        self.assertEqual(profile_sample(profile), profile_sample(leaked))

    def test_duplicate_purchase_missing_purchase_and_inconsistent_label_fail(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            write_tables(root, [_row("학습", "OWN001"), _row("검증", "OWN001"), _row("평가", "OWN001")])
            purchases = (root / "purchases.csv").read_text(encoding="utf-8")
            (root / "purchases.csv").write_text(purchases + purchases.splitlines()[-1] + "\n", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "중복"):
                load_dataset(root)

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            write_tables(root, [_row("학습", "OWN001", id="P000001"), _row("검증", "OWN001"), _row("평가", "OWN001")])
            text = (root / "purchases.csv").read_text(encoding="utf-8")
            (root / "purchases.csv").write_text(text.replace("P000001", "P999999"), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "구매 내역이 없는 보유자"):
                load_dataset(root)

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            write_tables(
                root,
                [
                    _row("학습", "OWN001", model="K5"),
                    _row("학습", "OWN001", model="K8"),
                    _row("검증", "OWN001", model="K5"),
                    _row("평가", "OWN001", model="K5"),
                ],
            )
            with self.assertRaisesRegex(ValueError, "차량 정보가 서로 다릅니다"):
                load_dataset(root)

    def test_unknown_split_and_negative_number_fail(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            write_tables(root, [_row("기타", "OWN001"), _row("검증", "OWN001"), _row("평가", "OWN001")])
            with self.assertRaisesRegex(ValueError, "데이터 구분"):
                load_dataset(root)

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            write_tables(
                root,
                [
                    _row("학습", "OWN001", income=-1),
                    _row("검증", "OWN001"),
                    _row("평가", "OWN001"),
                ],
            )
            with self.assertRaisesRegex(ValueError, "0 이상"):
                load_dataset(root)


def _row(split: str, label: str, **extra: object) -> dict[str, object]:
    return {"split": split, "label": label, **extra}


def _splits(samples) -> list[str]:
    return [sample.split for sample in samples]
