import unittest

from tools.data.households.analyze_no_choice import primary_reason


class NoChoiceAnalysisTests(unittest.TestCase):
    def test_expenses_savings_and_buffer_are_attributed_separately(self):
        self.assertEqual(primary_reason(-100, -200, -300, 5, 200000),
                         '생활지출과기존상환만으로월가용없음')
        self.assertEqual(primary_reason(100, 0, -100, 5, 200000), '저축차감후월가용없음')
        self.assertEqual(primary_reason(100, 50, 0, 5, 200000), '최소여유자금확보후월가용없음')

    def test_running_cost_boundary_is_distinct_from_financing_shortage(self):
        self.assertEqual(primary_reason(500000, 300000, 199999, 5, 200000), '차량최저유지비도부족')
        self.assertEqual(primary_reason(500000, 300000, 200000, 5, 200000), '유지비는가능하지만할부포함시부족')

    def test_empty_seat_price_intersection_is_not_misattributed_to_income(self):
        self.assertEqual(primary_reason(-100, -200, -300, 0, 0), '정원과가격상한의교집합없음')


if __name__ == '__main__':
    unittest.main()
