import unittest
from dataclasses import replace
from vehicle_matching.budget import recommendation_budget
from vehicle_matching.service import CandidateService
from test_preferences import FixedRanker
from test_vehicle_matching import person,vehicle

class ImportancePriceBandTests(unittest.TestCase):
 def profile(self, importance=3, **changes):
  return person(liquid_assets=100000000,emergency_reserve=0,down_payment=0,monthly_income=3600000,monthly_expenses=0,existing_monthly_payment=0,monthly_savings=0,cost_importance=importance,**changes)
 def test_low_medium_high_use_exact_cash_percentages(self):
  for importance,lower in [(1,80000000),(2,80000000),(3,70000000),(4,60000000),(5,60000000)]:
   with self.subTest(importance=importance):
    band=recommendation_budget(self.profile(importance),[],{})
    self.assertEqual((band['lower'],band['upper']),(lower,100000000))
 def test_boundaries_and_both_regular_and_conditional_results_obey_band(self):
  cars=[vehicle(id=str(price),model=str(price),price=price,seats=5,body_type='SUV') for price in (79999999,80000000,90000000,100000000,100000001)]
  cars.append(vehicle(id='unknown-low',model='Unknown low',price=20000000,seats=None))
  cars.append(vehicle(id='unknown-in-band',model='Unknown',price=85000000,seats=None))
  r=CandidateService(FixedRanker(),cars).recommend(self.profile(1,minimum_seats=5),9)
  self.assertEqual({v['vehicle']['price'] for v in r['recommendations']},{80000000,90000000,100000000})
  self.assertEqual([v['vehicle']['id'] for v in r['conditionalRecommendations']],['unknown-in-band'])
 def test_no_band_candidates_does_not_silently_lower_floor(self):
  r=CandidateService(FixedRanker(),[vehicle(price=20000000)]).recommend(self.profile(1))
  self.assertEqual(r['recommendations'],[])
  self.assertEqual(r['status'],'no-price-band-match')
  self.assertEqual(r['budgetPolicy']['lower'],80000000)
 def test_reserve_and_explicit_ceiling_are_respected_and_salary_is_not_cash(self):
  p=replace(self.profile(3),liquid_assets=110000000,emergency_reserve=10000000,purchase_price_ceiling=50000000)
  band=recommendation_budget(p,[],{})
  self.assertEqual((band['lower'],band['upper']),(35000000,50000000))
  self.assertEqual(recommendation_budget(replace(p,monthly_income=1e9),[],{})['lower'],band['lower'])
  tiny=recommendation_budget(replace(p,liquid_assets=10000003,emergency_reserve=0,purchase_price_ceiling=0),[],{})
  self.assertEqual(tiny['lower'],7000003)
 def test_band_never_relaxes_monthly_or_required_seating_conditions(self):
  cars=[vehicle(id='wrong-seats',model='Wrong seats',price=85000000,seats=5),vehicle(id='unaffordable',model='Too expensive',price=110000000,seats=7)]
  self.assertEqual(CandidateService(FixedRanker(),cars).recommend(self.profile(1,minimum_seats=7))['recommendations'],[])
  poor=replace(self.profile(1),monthly_income=0,liquid_assets=100000000)
  self.assertEqual(CandidateService(FixedRanker(),[vehicle(price=100000000,seats=7)]).recommend(poor)['recommendations'],[])
