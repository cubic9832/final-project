import unittest

from test_vehicle_matching import person, vehicle
from vehicle_matching.recommendation_policy import preference_penalties
from vehicle_matching.explanations import preference_evidence
from vehicle_matching.preference_model import encode_body


class GroupedBodyPreferenceTests(unittest.TestCase):
    def test_other_group_matches_each_subtype_in_ranking_and_evidence(self):
        profile = person(preferred_body_type='OTHER')
        for body in ('HATCHBACK', 'WAGON', 'MPV', 'BOX', 'PICKUP', 'COUPE', 'CONVERTIBLE', 'ROADSTER'):
            with self.subTest(body=body):
                car = vehicle(body_type=body)
                penalties = preference_penalties(profile, car)
                self.assertEqual(next(value for key, _, value in penalties if key == 'body'), 0)
                evidence = preference_evidence(profile, car, [])
                self.assertEqual(next(row for row in evidence if row['key'] == 'body')['status'], 'match')
                self.assertEqual(encode_body(profile, car)[0], 1)

    def test_other_does_not_match_sedan_suv_or_unknown(self):
        profile = person(preferred_body_type='OTHER')
        for body in ('SEDAN', 'SUV', None):
            car = vehicle(body_type=body)
            self.assertEqual(next(value for key, _, value in preference_penalties(profile, car) if key == 'body'), 1)
            evidence = next(row for row in preference_evidence(profile, car, []) if row['key'] == 'body')
            self.assertEqual(evidence['status'], 'unknown' if body is None else 'mismatch')


if __name__ == '__main__':
    unittest.main()
