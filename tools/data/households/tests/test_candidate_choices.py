import unittest
from dataclasses import replace

from tools.data.households.generate_candidate_choices import (
    choice_distribution, generate, korean_row, load_candidates, validate,
)
from vehicle_matching.dataset import profiles


class CandidateChoiceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.vehicles = load_candidates()

    def test_reproducible_choices_and_unseen_combinations(self):
        rows = generate(50, 1234, self.vehicles)
        self.assertEqual(rows, generate(50, 1234, self.vehicles))
        report = validate(rows, self.vehicles)
        self.assertGreater(report['same_inputs_multiple_models'], 0)
        self.assertGreater(report['split_counts']['combination_test'], 0)
        for row in rows:
            if row['minimum_seats'] >= 6:
                self.assertEqual(row['preferred_size'], 'large')
            if row['minimum_seats'] == 5:
                self.assertNotEqual(row['preferred_size'], 'small')
            for value in korean_row(row).values():
                self.assertNotIsInstance(value, float)

    def test_no_car_when_monthly_budget_is_exhausted(self):
        profile = replace(profiles(1, 1)[0], monthly_expenses=20000000,
                          preferred_size='small')
        self.assertEqual(choice_distribution(profile, self.vehicles), [])

    def test_high_cost_importance_does_not_force_single_model(self):
        profile = replace(profiles(1, 1)[0], monthly_income=10000000,
                          monthly_expenses=1000000, existing_monthly_payment=0,
                          monthly_savings=0, cost_importance=5, preferred_size='small',
                          minimum_seats=2, charging_available=False, preferred_fuel=None,
                          months=60, annual_rate=0.06, down_payment=0, financing_mode='fixed')
        options = choice_distribution(profile, self.vehicles)
        self.assertGreater(len(options), 1)
        self.assertAlmostEqual(sum(option[2] for option in options), 1)
        self.assertTrue(any(option[0].fuel == 'ELECTRIC' for option in options))
        self.assertTrue(any(option[0].length_mm and option[0].length_mm > 4200 for option in options))

    def test_fuel_and_charging_are_not_hard_exclusions(self):
        profile = replace(profiles(1, 1)[0], monthly_income=10000000,
                          monthly_expenses=1000000, existing_monthly_payment=0,
                          monthly_savings=0, preferred_size='large', minimum_seats=2,
                          preferred_fuel='ELECTRIC', charging_available=False,
                          months=60, annual_rate=0.06, down_payment=0, financing_mode='fixed')
        original = choice_distribution(profile, self.vehicles)
        options = choice_distribution(replace(profile, charging_available=True), self.vehicles)
        self.assertTrue(options)
        self.assertEqual(original, options)
        self.assertTrue(any(option[0].fuel != 'ELECTRIC' for option in options))

    def test_price_ceiling_and_purchase_cost_are_mandatory(self):
        profile = replace(profiles(1, 1)[0], monthly_income=10000000,
                          monthly_expenses=1000000, existing_monthly_payment=0, monthly_savings=0,
                          minimum_seats=2, months=60, annual_rate=0.06, down_payment=0,
                          financing_mode='fixed')
        options = choice_distribution(profile, self.vehicles, maximum_price=20000000)
        self.assertTrue(options)
        self.assertTrue(all(option[0].price <= 20000000 for option in options))
        self.assertEqual(choice_distribution(profile, self.vehicles, maximum_price=1), [])
        # With zero purchase funds, cash-only purchases cannot be funded even at high income.
        self.assertEqual(choice_distribution(replace(profile, months=0), self.vehicles), [])


if __name__ == '__main__':
    unittest.main()
