import unittest
from dataclasses import replace

from tools.data.households.relabel_preference_choices import (
    ChoicePolicy, FEATURES, PREFERENCES, output_row, verify_selected,
)
from vehicle_matching.catalog import Vehicle


def vehicle(identity, price=20000000, fuel='GASOLINE', length=4000, seats=5):
    return Vehicle(identity, '테스트', identity, '기본', '2026', price, fuel, 15,
                   'https://example.com/source', '2026-10-22', length_mm=length, seats=seats)


class PreferenceRelabelingTests(unittest.TestCase):
    def setUp(self):
        self.row = dict(zip(FEATURES, ('8000000', '30000000', '500000', '1000000', '1000000', '100000', '15000', '출퇴근')))
        self.row.update(dict(zip(PREFERENCES, ('3', '작음', '가솔린', '2'))))
        self.row.update({'프로필_식별자': 'P1', '재무조건그룹번호': 'P1', '데이터_구분': '학습',
                         '선택차량_라벨코드': 'OLD', '선택차량_브랜드': '기존', '선택차량_모델': '기존차량',
                         '선택상태': '기존합성선택', '선호값_출처': '기존선택과무관한합성보충'})
        self.context = {'savings': 1000000, 'reserve': 5000000, 'funds': 20000000,
                        'buffer': 300000, 'ceiling': 0}

    def test_preferences_change_vehicle_without_changing_financial_inputs(self):
        small = vehicle('작은가솔린')
        large = vehicle('큰전기', price=40000000, fuel='ELECTRIC', length=5000)
        policy = ChoicePolicy([small, large])
        first = policy.choose(self.row, self.context, 42)
        changed = {**self.row, PREFERENCES[1]: '큼', PREFERENCES[2]: '전기'}
        second = policy.choose(changed, self.context, 42)
        self.assertEqual(first['vehicle'].id, small.id)
        self.assertEqual(second['vehicle'].id, large.id)
        verify_selected(self.row, self.context, first)
        verify_selected(changed, self.context, second)
        output = output_row(self.row, self.context, second, {large.id: 'NEW-LARGE'})
        self.assertEqual([output[k] for k in (*FEATURES, *PREFERENCES)],
                         [self.row[k] for k in (*FEATURES, *PREFERENCES)])
        self.assertEqual(output['원래선택차량_라벨코드'], 'OLD')

    def test_seats_price_and_monthly_budget_override_preferences(self):
        small = vehicle('적격차량')
        too_small = vehicle('정원부족', seats=1)
        optional = replace(vehicle('옵션확인필요', seats=None), seat_options=(2, 7))
        policy = ChoicePolicy([small, too_small, optional])
        row = {**self.row, PREFERENCES[3]: '4'}
        chosen = policy.choose(row, self.context, 42)
        self.assertEqual(chosen['vehicle'].id, small.id)
        self.assertIsNone(policy.choose(row, {**self.context, 'ceiling': 1}, 42))
        self.assertIsNone(policy.choose({**row, FEATURES[0]: '1000000'}, self.context, 42))
        self.assertIsNone(ChoicePolicy([vehicle('미확인정원', seats=None)]).choose(self.row, self.context, 42))

    def test_near_equal_candidates_remain_diverse_and_seed_is_reproducible(self):
        policy = ChoicePolicy([vehicle('A'), vehicle('B', price=20100000)])
        outcomes = set()
        for index in range(40):
            row = {**self.row, '프로필_식별자': f'P{index}', PREFERENCES[0]: '5'}
            first = policy.choose(row, self.context, 42)
            self.assertEqual(first, policy.choose(row, self.context, 42))
            verify_selected(row, self.context, first)
            outcomes.add(first['vehicle'].id)
        self.assertEqual(outcomes, {'A', 'B'})

    def test_scalar_finance_matches_vectorized_cost_with_and_without_cash(self):
        policy = ChoicePolicy([vehicle('A', price=42345000)])
        for funds in (0, 20000000, 25000000):
            context = {**self.context, 'funds': funds}
            chosen = policy.choose(self.row, context, 42)
            verify_selected(self.row, context, chosen)
            self.assertGreater(chosen['payment'], 0)
            self.assertGreaterEqual(chosen['remaining'], context['buffer'])

    def test_cost_importance_changes_the_cost_space_tradeoff(self):
        policy = ChoicePolicy([vehicle('A', price=20000000, length=4700),
                               vehicle('B', price=40000000, length=4900)])
        row = {**self.row, FEATURES[0]: '4500000', FEATURES[7]: '가족이동', PREFERENCES[1]: '큼'}
        low = policy.evaluate({**row, PREFERENCES[0]: '1'}, self.context)[0]
        high = policy.evaluate({**row, PREFERENCES[0]: '5'}, self.context)[0]
        self.assertGreater(low[1], low[0])
        self.assertGreater(high[0], high[1])


if __name__ == '__main__':
    unittest.main()
