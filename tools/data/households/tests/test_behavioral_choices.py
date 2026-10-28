"""Financial safety, trade-offs and reproducible stochastic choice generation."""
from dataclasses import replace
import json
from pathlib import Path
import tempfile
import unittest

import numpy as np

from vehicle_matching.catalog import ROOT, Vehicle
from vehicle_matching.finance import Assumptions, Profile, assess
from tools.data.households.generate_behavioral_choices import (
    audit_saved, choice_probability, eligible_cost, generate, utility,
)


def profile(**changes):
    return replace(Profile(monthly_income=6000000, monthly_expenses=2000000,
        existing_monthly_payment=0, liquid_assets=100000000, down_payment=0,
        emergency_reserve=0, monthly_savings=0, annual_distance=15000, months=0,
        annual_rate=0, financing_mode='recommendation', preferred_body_type='SUV'), **changes)


def car(**changes):
    return replace(Vehicle('A', 'Brand', 'Model A', 'Base', '2026', 30000000,
        'GASOLINE', 12, 'https://example.com', '2026-10-28', seats=5,
        length_mm=4500, body_type='SEDAN', seats_status='official-source-verified'), **changes)


class BehavioralChoiceTests(unittest.TestCase):
    def test_financial_boundary_and_required_seats_are_hard_constraints(self):
        vehicle = car()
        cost = assess(profile(monthly_income=0, monthly_expenses=0), vehicle)
        boundary = vehicle.price + 12 * cost['monthly_running_cost']
        self.assertIsNotNone(eligible_cost(profile(monthly_income=0, monthly_expenses=0,
            liquid_assets=boundary), vehicle, Assumptions()))
        self.assertIsNone(eligible_cost(profile(monthly_income=0, monthly_expenses=0,
            liquid_assets=boundary - 1), vehicle, Assumptions()))
        self.assertIsNone(eligible_cost(profile(minimum_seats=6), vehicle, Assumptions()))
        self.assertIsNone(eligible_cost(profile(minimum_seats=2), car(seats=None), Assumptions()))
        self.assertIsNotNone(eligible_cost(profile(minimum_seats=0), car(seats=None), Assumptions()))

    def test_observed_importance_can_reverse_cost_and_body_tradeoff(self):
        cheap, suv = car(price=10000000), car(id='B', model='Model B', price=65000000, body_type='SUV')
        coefficients = (1, 1, 1, 1, 1)
        economy = profile(cost_importance=5, body_importance=1)
        taste = profile(cost_importance=1, body_importance=5)
        score = lambda p, v: utility(p, v, assess(p, v), coefficients)
        self.assertGreater(score(economy, cheap), score(economy, suv))
        self.assertGreater(score(taste, suv), score(taste, cheap))
        self.assertEqual(choice_probability(0, 0, .1), .5)
        self.assertGreater(choice_probability(0, -.1, .1), .5)
        self.assertGreater(choice_probability(-.1, 0, .1), 0)
        self.assertEqual(choice_probability(-1000, 1000, .05), 0)

    def test_generated_choices_are_reproducible_audited_and_not_always_utility_winners(self):
        vehicles = [car(id=str(i), model=f'Model {i}', price=10000000 + i * 1000000,
                        body_type='SUV' if i % 2 else 'SEDAN') for i in range(5)]
        (ROOT / 'tmp').mkdir(exist_ok=True)
        with tempfile.TemporaryDirectory(dir=ROOT / 'tmp') as folder:
            first, second = Path(folder) / 'a', Path(folder) / 'b'
            generate(first, vehicles, groups=40, seed=17)
            generate(second, list(reversed(vehicles)), groups=40, seed=17)
            lower_utility_wins = 0
            total = 0
            for role in ('train', 'validation', 'test'):
                self.assertEqual((first / f'{role}_profiles.jsonl').read_bytes(), (second / f'{role}_profiles.jsonl').read_bytes())
                self.assertEqual((first / f'{role}_audit.jsonl').read_bytes(), (second / f'{role}_audit.jsonl').read_bytes())
                with np.load(first / f'{role}_choices.npz') as a, np.load(second / f'{role}_choices.npz') as b:
                    for key in a.files:
                        np.testing.assert_array_equal(a[key], b[key])
                for line in (first / f'{role}_audit.jsonl').read_text(encoding='utf-8').splitlines():
                    record = json.loads(line)
                    lower_utility_wins += int((record['utility_a'] < record['utility_b'] and record['label'] == 1)
                        or (record['utility_b'] < record['utility_a'] and record['label'] == 0))
                    total += 1
            self.assertGreater(total, 0)
            self.assertGreater(lower_utility_wins, 0)
            self.assertEqual(audit_saved(first)['comparisons_checked'], total)
            with self.assertRaises(FileExistsError):
                generate(first, vehicles, groups=1)
            path = first / 'train_audit.jsonl'
            path.write_text(path.read_text(encoding='utf-8') + '{}\n', encoding='utf-8')
            with self.assertRaisesRegex(ValueError, 'checksum'):
                audit_saved(first)


if __name__ == '__main__':
    unittest.main()
