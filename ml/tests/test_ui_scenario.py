"""UI meanings and learned serving behavior, including previous failure cases."""
from dataclasses import asdict, replace
import json
import unittest
import numpy as np
from fastapi.testclient import TestClient
from vehicle_matching.api import create_app, load_service
from vehicle_matching.catalog import ROOT, read_catalog
from vehicle_matching.finance import Profile
from vehicle_matching.ui_scenario_features import FEATURE_NAMES, encode_ui_scenario, choice_utility

BUNDLE=ROOT/'ml/outputs/models/scenario-choices/20261030-ui-v1-10k'


class UiScenarioFeaturesTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cars=read_catalog(ROOT/'ml/outputs/models/scenario-choices/20261029-v3-broad-taste-10k/catalog.json')
        cls.traits=json.loads((ROOT/'data/vehicles/scenario-traits-20261030/vehicle_traits.json').read_text(encoding='utf-8'))['vehicles']

    def profile(self,**changes):
        p=Profile(monthly_income=6000000,monthly_expenses=1500000,existing_monthly_payment=0,
                  liquid_assets=500000000,down_payment=0,emergency_reserve=0,monthly_savings=0,
                  annual_distance=15000,months=0,financing_mode='recommendation')
        return replace(p,**changes)

    def test_single_taste_importance_has_absolute_effect(self):
        car=self.cars[0];base=self.traits[car.id]
        near={**base,'values':{**base['values'],'exterior_angularity':0.}}
        far={**base,'values':{**base['values'],'exterior_angularity':1.}}
        differences=[]
        for weight in (1,5):
            user={'profile':asdict(self.profile()),'preferences':{'angularity':0.,'design_importance':weight}}
            differences.append(choice_utility(encode_ui_scenario(user,car,near))-choice_utility(encode_ui_scenario(user,car,far)))
        self.assertGreater(differences[1],differences[0]*4)

    def test_unknown_charging_is_neutral_and_retired_body_does_not_enter_features(self):
        car=next(car for car in self.cars if car.fuel=='ELECTRIC')
        user={'profile':asdict(self.profile()),'preferences':{}}
        first=encode_ui_scenario(user,car,self.traits[car.id])
        user['profile']['charging_available']=True
        second=encode_ui_scenario(user,car,self.traits[car.id])
        np.testing.assert_array_equal(first,second)
        self.assertEqual(first[FEATURE_NAMES.index('charging_known')],0)
        user['profile']['preferred_fuel']='ELECTRIC'
        third=encode_ui_scenario(user,car,self.traits[car.id])
        self.assertEqual(third[FEATURE_NAMES.index('charging_known')],1)
        self.assertEqual(third[FEATURE_NAMES.index('charging')],1)


class UiScenarioServingTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        import torch
        torch.set_num_threads(4)
        cls.service=load_service(BUNDLE)

    def request(self):
        return {'profile':{'monthly_income':6000000.,'monthly_expenses':1500000.,'existing_monthly_payment':0.,
                          'liquid_assets':50000000.,'emergency_reserve':0.,'monthly_savings':0.,
                          'annual_distance':15000.,'minimum_seats':0,'preferred_body_type':'any'},
                'scenario':{'angularity':0.,'design_importance':1},'k':9}

    def test_api_returns_learned_order_and_scores_change_with_single_importance(self):
        with TestClient(create_app(self.service)) as client:
            request=self.request();responses=[]
            for importance in (1,5):
                request['scenario']['design_importance']=importance
                response=client.post('/api/v2/recommendations',json=request)
                self.assertEqual(response.status_code,200,response.text)
                result=response.json()['data'];responses.append(result)
                self.assertEqual(result['rankingPolicy'],'required-eligibility-then-ui-scenario-ml')
                scores=[item['rankingScore'] for item in result['recommendations']]
                self.assertEqual(scores,sorted(scores,reverse=True))
                self.assertTrue(all(item['cost']['eligible'] for item in result['recommendations']))
            self.assertNotEqual([item['rankingScore'] for item in responses[0]['recommendations']],
                                [item['rankingScore'] for item in responses[1]['recommendations']])
            self.assertNotEqual([item['vehicle']['id'] for item in responses[0]['recommendations']],
                                [item['vehicle']['id'] for item in responses[1]['recommendations']])
            self.assertTrue(all(not item['outsideTrainingRange'] for result in responses for item in result['recommendations']))
            request['profile']['minimum_seats']=7
            result=client.post('/api/v2/recommendations',json=request)
            self.assertEqual(result.status_code,200,result.text)
            self.assertTrue(all(item['vehicle']['seats']>=7 for item in result.json()['data']['recommendations']))
