import unittest
from copy import deepcopy
from pathlib import Path
from tempfile import TemporaryDirectory

from tools.data.households.extend_training_preferences import (
    FEATURES, PREFERENCES, ROOT, assert_preserved, extend_owners, legacy_training,
    model_registry, new_training, read_csv, validate_training, extend_additional_source, write_csv,
)
from tools.data.households.generate_candidate_choices import generate, load_candidates


class TrainingPreferenceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.columns, owners = read_csv(ROOT / 'data/seed/domestic-car/owners.csv')
        _, purchases = read_csv(ROOT / 'data/seed/domestic-car/purchases.csv')
        cls.owner = owners[0]
        cls.purchase = next(row for row in purchases if row['프로필_식별자'] == cls.owner['프로필_식별자'])

    def test_only_preferences_are_added_and_vehicle_does_not_drive_them(self):
        original = deepcopy(self.owner)
        extended = extend_owners([original], 42)[0]
        assert_preserved([original], [extended], self.columns)
        self.assertEqual(set(extended) - set(original), set(PREFERENCES))
        changed = {**original, '보유차량_모델': '다른 차량', '보유차량_라벨코드': '다른 라벨'}
        other = extend_owners([changed], 42)[0]
        self.assertEqual([extended[k] for k in PREFERENCES], [other[k] for k in PREFERENCES])
        with self.assertRaises(AssertionError):
            assert_preserved([original], [{**extended, FEATURES[0]: '1'}], self.columns)

    def test_legacy_features_use_pre_purchase_debt_and_separate_expenses(self):
        owner = extend_owners([self.owner], 42)[0]
        purchase = {**self.purchase, FEATURES[4]: '123456', FEATURES[5]: '1200'}
        row = legacy_training([owner], [purchase])[0]
        self.assertEqual(row[FEATURES[4]], '123456')
        self.assertEqual(row[FEATURES[5]], '1200')
        self.assertEqual(row[FEATURES[2]], owner[FEATURES[2]])
        self.assertEqual(row[FEATURES[3]], owner[FEATURES[3]])
        validate_training([row])

    def test_new_rows_complete_and_finance_and_splits_preserved(self):
        vehicles = load_candidates()
        baseline = legacy_training(extend_owners([self.owner], 42), [self.purchase])
        labels, registry = model_registry(baseline, vehicles)
        self.assertEqual(len(registry), len(vehicles))
        generated = generate(20, 20261022, vehicles)
        rows = new_training(generated, labels, 20261022)
        validate_training(rows)
        for before, after in zip(generated, rows):
            self.assertEqual(after[FEATURES[2]] + after[FEATURES[3]], before['monthly_expenses'])
            self.assertEqual(after[FEATURES[4]], before['existing_debt_balance_won'])
            self.assertTrue(all(value not in ('', None) for value in after.values()))
        tampered = deepcopy(rows)
        tampered.append({**rows[0], '프로필_식별자': 'different', '데이터_구분': '검증'
                         if rows[0]['데이터_구분'] != '검증' else '학습'})
        with self.assertRaises(AssertionError):
            validate_training(tampered)

    def test_additional_extension_preserves_rows_and_joins_purchase_by_id(self):
        owners = [self.owner, {**self.owner, '프로필_식별자': 'ADDITIONAL-TEST'}]
        purchases = [self.purchase, {**self.purchase, '프로필_식별자': 'ADDITIONAL-TEST', FEATURES[4]: '12345'}]
        workspace_temp = ROOT / 'tmp'
        workspace_temp.mkdir(exist_ok=True)
        with TemporaryDirectory(dir=workspace_temp) as temporary:
            root = Path(temporary)
            self.assertTrue(root.resolve().is_relative_to(workspace_temp.resolve()))
            source = root / 'owners.csv'
            purchase = root / 'purchases.csv'
            write_csv(source, self.columns, owners)
            write_csv(purchase, list(self.purchase), list(reversed(purchases)))
            original_bytes = source.read_bytes(), purchase.read_bytes()
            baseline, report = extend_additional_source(source, purchase, root / 'extended', 42, expected_rows=2)
            _, extended = read_csv(root / 'extended/owners.csv')
            assert_preserved(owners, extended, self.columns)
            self.assertEqual(baseline[1][FEATURES[4]], '12345')
            self.assertEqual(report['rows'], 2)
            self.assertEqual((source.read_bytes(), purchase.read_bytes()), original_bytes)
            self.assertEqual((root / 'extended/purchases.csv').read_bytes(), original_bytes[1])
            with self.assertRaises(ValueError):
                extend_additional_source(source, purchase, root / 'wrong-count', 42, expected_rows=3)


if __name__ == '__main__':
    unittest.main()
