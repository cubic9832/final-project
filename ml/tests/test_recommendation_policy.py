import unittest
from dataclasses import replace
from vehicle_matching.service import CandidateService
from test_vehicle_matching import person,vehicle
from test_preferences import FixedRanker
class PreferBadRanker(FixedRanker):
 def score_candidates(self,p,cars):return [1000 if v.id=='bad' else 1 for v in cars],[False]*len(cars)
class RecommendationPolicyTests(unittest.TestCase):
 def test_seats_never_relaxed_for_high_ml_or_optional_upgrade(self):
  p=person(minimum_seats=7,preferred_fuel=None)
  cars=[vehicle(id='bad',model='Bad',seats=5,seat_options=(5,7)),vehicle(id='good',model='Good',seats=7)]
  r=CandidateService(PreferBadRanker(),cars).recommend(p)
  self.assertEqual([x['vehicle']['id'] for x in r['recommendations']],['good'])
 def test_conflict_is_separate_and_no_input_leaves_seating_unrestricted(self):
  c=vehicle(seats=7,seats_status='official-reference-conflict')
  service=CandidateService(FixedRanker(),[c])
  result=service.recommend(person(minimum_seats=7))
  self.assertEqual(result['recommendations'],[])
  self.assertEqual(len(result['conditionalRecommendations']),1)
  self.assertEqual(result['conditionalRecommendations'][0]['decisionEvidence']['preferences'][-1]['status'],'unknown')
  self.assertEqual(len(service.recommend(person(minimum_seats=0))['recommendations']),1)
 def test_higher_importance_fuel_beats_size_and_priority_can_reverse(self):
  p=person(minimum_seats=5,preferred_fuel='HYBRID',preferred_size='small',fuel_importance=5,space_importance=4)
  large=vehicle(id='good',model='Large',seats=5,fuel='HYBRID',length_mm=5000)
  small=vehicle(id='bad',model='Small',seats=5,fuel='GASOLINE',length_mm=4000)
  service=CandidateService(PreferBadRanker(),[large,small])
  self.assertEqual(service.recommend(p)['recommendations'][0]['vehicle']['id'],'good')
  self.assertEqual(service.recommend(replace(p,fuel_importance=4,space_importance=5))['recommendations'][0]['vehicle']['id'],'bad')
 def test_size_distance_is_continuous_and_no_preferences_preserve_raw_order(self):
  p=person(preferred_fuel=None,preferred_size='small')
  near=vehicle(id='near',model='Near',length_mm=4201)
  far=vehicle(id='bad',model='Far',length_mm=5000)
  service=CandidateService(PreferBadRanker(),[near,far])
  self.assertEqual(service.recommend(p)['recommendations'][0]['vehicle']['id'],'near')
  self.assertEqual(service.recommend(replace(p,preferred_size='any'))['recommendations'][0]['vehicle']['id'],'bad')
