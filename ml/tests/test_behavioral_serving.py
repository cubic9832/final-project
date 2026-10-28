import unittest
from dataclasses import asdict, replace

from fastapi.testclient import TestClient

from test_preferences import FixedRanker
from test_vehicle_matching import person, vehicle
from vehicle_matching.api import create_app, load_service
from vehicle_matching.catalog import ROOT
from vehicle_matching.service import CandidateService


class ChoiceRanker(FixedRanker):
    def score_candidates(self, profile, cars):
        return [100 if car.id == 'unpreferred' else 1 for car in cars], [False] * len(cars)


class BehavioralServingTests(unittest.TestCase):
    def test_learned_order_can_trade_preferences_but_cannot_relax_required_seats(self):
        profile = person(preferred_fuel='HYBRID', fuel_importance=5, minimum_seats=5)
        cars = [vehicle(id='preferred', model='Preferred', fuel='HYBRID', seats=7),
                vehicle(id='unpreferred', model='Unpreferred', fuel='GASOLINE', seats=5),
                vehicle(id='expensive', model='Expensive', seats=7, price=1e10)]
        self.assertEqual(CandidateService(ChoiceRanker(), cars).recommend(profile)['recommendations'][0]['vehicle']['id'], 'preferred')
        service = CandidateService(ChoiceRanker(), cars, ml_only=True)
        result = service.recommend(profile)
        self.assertEqual([row['vehicle']['id'] for row in result['recommendations']], ['unpreferred', 'preferred'])
        self.assertEqual(result['recommendations'][0]['rankingComparison']['status'], 'ml-ranked')
        self.assertEqual([row['vehicle']['id'] for row in service.recommend(replace(profile, minimum_seats=7))['recommendations']], ['preferred'])

    def test_checkpoint_metadata_selects_experimental_policy_and_api_serves_predictions(self):
        service = load_service(ROOT / 'ml/outputs/models/behavioral-choices/20261028-million-v1')
        with TestClient(create_app(service)) as client:
            options = client.get('/api/v2/recommendation-options').json()['data']
            self.assertEqual(options['modelBundle'], '20261028-million-v1')
            self.assertEqual(options['scorePolicy'], 'required-eligibility-then-ml-only-experimental')
            payload = asdict(person(preferred_body_type='OTHER', minimum_seats=0))
            response = client.post('/api/v2/recommendations', json={'profile': payload, 'k': 3})
            self.assertEqual(response.status_code, 200, response.text)
            result = response.json()['data']
            scores = [row['rankingScore'] for row in result['recommendations']]
            self.assertGreater(len(scores), 0)
            self.assertEqual(scores, sorted(scores, reverse=True))
            self.assertEqual(result['scorePolicy'], options['scorePolicy'])


if __name__ == '__main__':
    unittest.main()
