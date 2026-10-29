import unittest
from dataclasses import replace
from test_vehicle_matching import person, vehicle
from vehicle_matching.finance import assess, Assumptions
class ManagedCostTests(unittest.TestCase):
 def test_custom_costs_zero_and_reset(self):
  p=person();v=vehicle();defaults=Assumptions()
  baseline=assess(p,v)['monthly_running_cost']
  changed=replace(v,monthly_insurance=0,monthly_tax=12000,monthly_maintenance=30000)
  expected=baseline-defaults.monthly_insurance-defaults.monthly_tax-defaults.monthly_maintenance+42000
  self.assertAlmostEqual(assess(p,changed)['monthly_running_cost'],expected,places=2)
  self.assertEqual(assess(p,replace(changed,monthly_insurance=None,monthly_tax=None,monthly_maintenance=None))['monthly_running_cost'],baseline)
 def test_negative_cost_is_rejected(self):
  with self.assertRaises(ValueError):replace(vehicle(),monthly_tax=-1)
