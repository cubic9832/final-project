"""Scenario API contract, saved inference and request isolation."""
from copy import deepcopy
import unittest

from fastapi.testclient import TestClient

from vehicle_matching.api import create_app, load_service
from vehicle_matching.catalog import ROOT
from vehicle_matching.finance import Profile, assess
from vehicle_matching.scenario_service import scenario_user


class ScenarioServingTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.service = load_service(ROOT/'ml/outputs/models/scenario-choices/20261029-v3-broad-taste-10k')

    def request(self):
        return {'profile':{'monthly_income':12000000.,'monthly_expenses':3000000.,'existing_monthly_payment':0.,
                'liquid_assets':1000000000.,'emergency_reserve':100000000.,'monthly_savings':2000000.,
                'annual_distance':20000.,'minimum_seats':5,'charging_available':True,
                'preferred_body_type':'PICKUP','body_importance':5},
                'scenario':{},'k':9}

    def test_options_and_actual_recommendation_use_saved_scenario_scores(self):
        request = self.request()
        with TestClient(create_app(self.service)) as client:
            options = client.get('/api/v2/recommendation-options').json()['data']
            self.assertTrue(options['scenarioSupported'])
            self.assertFalse(options['lifestyleSupported'])
            self.assertEqual(options['featureCount'],68)
            self.assertEqual(options['catalogCount'],308)
            self.assertEqual(options['modelNames'],96)
            result = client.post('/api/v2/recommendations',json=request)
            self.assertEqual(result.status_code,200,result.text)
            data = result.json()['data']
            self.assertEqual(data['modelBundle'],'20261029-v3-broad-taste-10k')
            self.assertEqual(options['brandOptions'],[])
            self.assertNotIn('scenarioModelOptions',options)
            items = data['recommendations']
            self.assertTrue(items)
            scores = [item['rankingScore'] for item in items]
            self.assertEqual(scores,sorted(scores,reverse=True))
            user = scenario_user(Profile(**request['profile'],down_payment=0,months=0,financing_mode='recommendation'),request['scenario'])
            by_id = {v.id:v for v in self.service.vehicles}
            direct = self.service.ranker.score_candidates(user,[by_id[item['vehicle']['id']] for item in items])
            for item,score in zip(items,direct):
                self.assertAlmostEqual(item['rankingScore'],score,places=5)
                self.assertTrue(item['cost']['eligible'])
                self.assertGreaterEqual(item['vehicle']['seats'],5)

    def test_preferences_are_request_local_and_invalid_preferences_are_problems(self):
        request = self.request()
        with TestClient(create_app(self.service)) as client:
            first = client.post('/api/v2/recommendations',json=request).json()['data']
            alternate = deepcopy(request)
            alternate['profile']['preferred_body_type'] = 'SEDAN'
            self.assertEqual(client.post('/api/v2/recommendations',json=alternate).status_code,200)
            repeated = client.post('/api/v2/recommendations',json=request).json()['data']
            self.assertEqual(first,repeated)
            for patch in [{'model_affinities':{'Sierra':1.}}, {'preferred_brands':['GMC']}, {'brand_importance':3}, {'design_importance':3}]:
                invalid = deepcopy(request); invalid['scenario'] = patch
                response = client.post('/api/v2/recommendations',json=invalid)
                self.assertEqual(response.status_code,400,response.text)
                self.assertIn('application/problem+json',response.headers['content-type'])

    def test_infeasible_request_returns_empty_and_unsupported_lifestyle_is_explicit(self):
        request = self.request()
        request['profile']['liquid_assets']=0.
        request['profile']['emergency_reserve']=0.
        with TestClient(create_app(self.service)) as client:
            response = client.post('/api/v2/recommendations',json=request)
            self.assertEqual(response.status_code,200,response.text)
            self.assertEqual(response.json()['data']['recommendations'],[])
            request.pop('scenario'); request['lifestyle']={'acceleration':1.}
            self.assertEqual(client.post('/api/v2/recommendations',json=request).status_code,409)


if __name__=='__main__':
    unittest.main()
