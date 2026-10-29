import unittest
from dataclasses import replace
from test_preferences import FixedRanker
from test_vehicle_matching import person, vehicle
from vehicle_matching.service import CandidateService


class PurposeSensitiveRanker(FixedRanker):
    def predict(self, profile, vehicles):
        return ([.9 if (v.length_mm > 4500) == (profile.purpose == 'family') else .1 for v in vehicles], [False] * len(vehicles))


class PurposeIndependenceTests(unittest.TestCase):
    def test_old_purpose_cannot_change_ml_scores_or_ranking(self):
        service = CandidateService(PurposeSensitiveRanker(), [vehicle(id='small', model='Small', length_mm=3900), vehicle(id='large', model='Large', length_mm=4900)])
        baseline = service.recommend(person(purpose='commute', purpose_importance=1))
        for purpose in ('family', 'leisure', 'business'):
            result = service.recommend(replace(person(), purpose=purpose, purpose_importance=5))
            self.assertEqual(result['recommendations'], baseline['recommendations'])
            self.assertEqual(result['evaluationSummary']['purposeAssessment'], 'not-evaluated')
            self.assertNotIn('purpose', result['appliedPreferences'])
            for row in result['recommendations']:
                self.assertNotIn('purpose', {item['key'] for item in row['preferenceAssessment']['components']})

    def test_explicit_size_orders_equal_ml_scores(self):
        service = CandidateService(FixedRanker(), [vehicle(id='small', model='Small', length_mm=3900), vehicle(id='large', model='Large', length_mm=4900)])
        profile = person(space_importance=5)
        self.assertEqual(service.recommend(replace(profile, preferred_size='small'))['recommendations'][0]['vehicle']['id'], 'small')
        self.assertEqual(service.recommend(replace(profile, preferred_size='large'))['recommendations'][0]['vehicle']['id'], 'large')
