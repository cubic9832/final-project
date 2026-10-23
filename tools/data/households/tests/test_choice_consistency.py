import unittest

from tools.data.households.audit_choice_consistency import accounting_checks, preference_checks
from tools.data.households.extend_training_preferences import PREFERENCES


class ChoiceConsistencyTests(unittest.TestCase):
    def test_soft_preferences_are_distinct_from_seating_violation(self):
        row = {PREFERENCES[1]: '작음', PREFERENCES[2]: '가솔린', PREFERENCES[3]: 6}
        result = preference_checks(row, '전기', [5000], [5])
        self.assertIn('최소탑승인원위반', result)
        self.assertIn('연료선호불일치_선호차이', result)
        self.assertIn('크기선호불일치_선호차이', result)
        self.assertNotIn('최소탑승인원위반', preference_checks(row, '가솔린', [4100], [6]))

    def test_unknown_specs_and_seating_options_are_not_reported_as_proven_violations(self):
        row = {PREFERENCES[1]: '중간', PREFERENCES[2]: '하이브리드', PREFERENCES[3]: 6}
        result = preference_checks(row, None, [], [5, 7])
        self.assertIn('정원옵션확인필요', result)
        self.assertIn('연료비교불가', result)
        self.assertIn('크기비교불가', result)
        self.assertNotIn('최소탑승인원위반', result)

    def test_purchase_funds_and_cash_must_reconcile(self):
        purchase = {'본인구매자금_원': '10000000', '가족지원금_가정_원': '0',
                    '차량할부원금_원': '22000000', '총구매비용_가정_원': '32000000',
                    '구매직전_현금_원': '15000000', '구매직후_현금_원': '5000000',
                    '옵션포함가격_원': '30000000', '등록비_가정_원': '2000000'}
        self.assertEqual(accounting_checks(purchase), [])
        purchase['차량할부원금_원'] = '21000000'
        self.assertEqual(accounting_checks(purchase), ['구매자금합계불일치'])


if __name__ == '__main__':
    unittest.main()
