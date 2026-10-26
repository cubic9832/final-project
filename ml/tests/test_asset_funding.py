import unittest
from dataclasses import replace
from test_vehicle_matching import person, vehicle
from vehicle_matching.finance import assess


class AssetFundingTests(unittest.TestCase):
    def test_surplus_assets_cover_no_income_and_deficit(self):
        profile = person(financing_mode='recommendation', liquid_assets=100000000, emergency_reserve=0,
                         monthly_income=2000000, monthly_expenses=2000000, monthly_savings=0,
                         existing_monthly_payment=0)
        for income in (2000000, 1800000):
            result = assess(replace(profile, monthly_income=income), vehicle())
            self.assertTrue(result['eligible'])
            self.assertEqual(result['funding_source'], 'assets')
            self.assertGreaterEqual(result['asset_runway_months'], 12)

    def test_exact_twelve_month_boundary_and_cash_not_double_counted(self):
        profile = person(financing_mode='recommendation', liquid_assets=100000000, emergency_reserve=0,
                         monthly_income=2000000, monthly_expenses=2000000, monthly_savings=0,
                         existing_monthly_payment=0)
        car = vehicle()
        monthly = assess(profile, car)['monthly_asset_drawdown']
        boundary = replace(profile, liquid_assets=car.price+monthly*12)
        self.assertTrue(assess(boundary, car)['eligible'])
        self.assertFalse(assess(replace(boundary, liquid_assets=boundary.liquid_assets-1), car)['eligible'])
        self.assertFalse(assess(replace(profile, liquid_assets=car.price), car)['eligible'])
        self.assertFalse(assess(replace(profile, liquid_assets=car.price-1), car)['eligible'])
