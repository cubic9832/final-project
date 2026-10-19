from tools.data.households.paths import SYNTHETIC_ROOT

import unittest

from tools.data.households.budget_simulation import loan_payment, simulate_budget


class BudgetSimulationTest(unittest.TestCase):
    def test_zero_interest_and_bullet_maturity(self):
        self.assertEqual(loan_payment(1200000, 0, 12, 'annuity'), (100000, 0))
        self.assertEqual(loan_payment(1200000, 0.12, 12, 'bullet'), (0, 12000))
        self.assertEqual(loan_payment(1200000, 0.12, 12, 'equal_principal'), (100000, 12000))

    def test_annuity_pays_off_balance(self):
        principal, interest = loan_payment(20000000, 0.06, 60, 'annuity')
        balance = 20000000
        for _ in range(60):
            balance = balance * 1.005 - principal - interest
        self.assertLess(abs(balance), 80)

    def test_invalid_terms(self):
        for terms in [(-1, 0.1, 12, 'annuity'), (1, -0.1, 12, 'annuity'), (1, 0.1, 0, 'annuity'), (1, 0.1, 12, 'unknown')]:
            with self.assertRaises(ValueError): loan_payment(*terms)

    def test_cash_purchase_shortfall_and_transport_replacement(self):
        p = {'monthly_net_income_won': 3000000, 'monthly_extra_income_won': 0,
             'liquid_cash_won': 1000000, 'emergency_target_won': 600000}
        e = {'living_won': 1000000, 'transport_won': 200000, 'target_savings_won': 300000}
        s = {'vehicle_price_won': 2000000, 'down_payment_won': 2000000, 'installment_months': 0,
             'registration_cost_assumed_won': 140000, 'monthly_operating_cost_won': 300000,
             'monthly_replaced_transport_won': 100000, 'annual_rate_assumed': 0.06}
        r = simulate_budget(p, e, [], s, {'income_stress_drop': 0.2, 'rate_stress_increase': 0.02})
        self.assertEqual(r['monthly_after_purchase_won'], 1300000)
        self.assertEqual(r['upfront_funding_gap_won'], 1140000)
        self.assertEqual(r['cash_runway_months'], 0)
        self.assertTrue(r['budget_exceeded_rule'])


if __name__ == '__main__':
    unittest.main()
