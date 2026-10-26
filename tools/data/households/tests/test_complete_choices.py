import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

import numpy as np

from tools.data.households.complete_preference_choices import context_from_row, make_group_plans, repair_plan
from tools.data.households.extend_training_preferences import ROOT, write_csv
from tools.data.households.relabel_preference_choices import ChoicePolicy, FEATURES, PREFERENCES
from tools.data.households.tests.test_preference_relabeling import vehicle


class CompleteChoiceTests(unittest.TestCase):
    def setUp(self):
        self.row = dict(zip(FEATURES, ('8000000', '30000000', '500000', '1000000', '1000000', '100000', '15000', '출퇴근')))
        self.row.update(dict(zip(PREFERENCES, ('3', '작음', '가솔린', '2'))))
        self.row.update({'월저축액_원': '1000000', '비상자금_원': '5000000',
                         '구매투입가능자금_원': '20000000', '최소월여유자금_원': '300000',
                         '구매가격상한_원_0이면미지정': '0'})

    def test_feasible_input_is_not_repaired(self):
        self.assertEqual(repair_plan(ChoicePolicy([vehicle('A')]), self.row), {'income_delta': 0, 'ceiling': 0})

    def test_income_repair_uses_minimum_boundary_plus_one_won_guard(self):
        policy = ChoicePolicy([vehicle('A')])
        row = {**self.row, FEATURES[0]: '1000000'}
        plan = repair_plan(policy, row)
        self.assertGreater(plan['income_delta'], 0)
        context = {'savings': 1000000, 'reserve': 5000000, 'funds': 20000000, 'buffer': 300000, 'ceiling': 0}
        for offset, expected in ((0, True), (-2, False)):
            adjusted = {**row, FEATURES[0]: str(int(row[FEATURES[0]]) + plan['income_delta'] + offset)}
            self.assertEqual(bool(np.any(np.isfinite(policy.evaluate(adjusted, context)[0]))), expected)

    def test_conflicting_price_cap_is_raised_without_changing_required_seats_or_income(self):
        policy = ChoicePolicy([vehicle('A', price=20000000, seats=5), vehicle('B', price=35000000, seats=7)])
        row = {**self.row, PREFERENCES[3]: '6', '구매가격상한_원_0이면미지정': '20000000'}
        self.assertEqual(repair_plan(policy, row), {'income_delta': 0, 'ceiling': 35000000})
        self.assertEqual(row[PREFERENCES[3]], '6')

    def test_income_and_conflicting_cap_can_both_be_repaired(self):
        policy = ChoicePolicy([vehicle('A', price=20000000, seats=5), vehicle('B', price=35000000, seats=7)])
        row = {**self.row, FEATURES[0]: '1000000', PREFERENCES[3]: '6',
               '구매가격상한_원_0이면미지정': '20000000'}
        plan = repair_plan(policy, row)
        self.assertGreater(plan['income_delta'], 0)
        self.assertEqual(plan['ceiling'], 35000000)
        with self.assertRaises(ValueError):
            repair_plan(policy, {**row, PREFERENCES[3]: '9'})

    def test_financial_group_gets_one_shared_correction_before_any_choice(self):
        policy = ChoicePolicy([vehicle('A', price=20000000, seats=5), vehicle('B', price=35000000, seats=7)])
        first = {**self.row, FEATURES[0]: '1000000', '프로필_식별자': 'A', '재무조건그룹번호': 'G'}
        second = {**first, '프로필_식별자': 'B', PREFERENCES[3]: '6'}
        temporary_root = ROOT / 'tmp'
        temporary_root.mkdir(exist_ok=True)
        with TemporaryDirectory(dir=temporary_root) as temporary:
            folder = Path(temporary)
            self.assertTrue(folder.resolve().is_relative_to(temporary_root.resolve()))
            source = folder / 'profiles.csv'
            write_csv(source, list(first), [first, second])
            plans, increases = make_group_plans(policy, source)
            self.assertGreater(plans['B']['income_delta'], plans['A']['income_delta'])
            for row in (first, second):
                adjusted = {**row, FEATURES[0]: str(int(row[FEATURES[0]]) + increases['G'])}
                self.assertTrue(np.any(np.isfinite(policy.evaluate(adjusted, context_from_row(adjusted))[0])))


if __name__ == '__main__':
    unittest.main()
