import unittest
from dataclasses import replace

from tools.data.households.audit_complete_choices import FEATURES, independent_cost
from tools.data.households.tests.test_preference_relabeling import vehicle


class CompleteQualityTests(unittest.TestCase):
    def row(self, funds='10000000', rate='0', distance='15000'):
        return {'구매투입가능자금_원': funds, '가정연금리_퍼센트': rate,
                '가정할부기간_개월': '60', FEATURES[6]: distance}

    def test_zero_interest_loan_and_operating_cost_recomputed_from_amounts(self):
        car = vehicle('A', price=30000000)
        self.assertEqual(independent_cost(self.row(), car), (10000000, 333334, 335000))

    def test_cash_purchase_caps_upfront_and_has_no_installment(self):
        car = vehicle('A', price=20000000)
        self.assertEqual(independent_cost(self.row(funds='30000000', rate='6'), car),
                         (20000000, 0, 335000))

    def test_unknown_efficiency_uses_explicit_midpoint_not_zero(self):
        car = replace(vehicle('A'), efficiency=None)
        upfront, payment, running = independent_cost(self.row(distance='13200'), car)
        self.assertEqual(running, 365000)
        self.assertGreater(payment, 0)


if __name__ == '__main__':
    unittest.main()
