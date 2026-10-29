"""Replacement-model API, request isolation and research/eligibility boundaries."""
import copy
import unittest
import numpy as np
from fastapi.testclient import TestClient
from vehicle_matching.api import create_app, load_service
from vehicle_matching.catalog import ROOT


class CohortModelTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.service = load_service(ROOT/'ml/outputs/models/preference-cohorts/20261028-v1')

    def test_masked_or_retired_preferences_do_not_affect_scores(self):
        model = self.service.ranker
        a,b = np.zeros((2,13),dtype=np.float32),np.ones((2,13),dtype=np.float32)
        weights,masks = np.ones_like(a),np.ones_like(a)
        masks[:,0]=0
        expected = model.pair_logits(a,b,weights,masks)
        a[:,[0,11,12]]=999
        b[:,[0,11,12]]=-999
        np.testing.assert_array_equal(expected,model.pair_logits(a,b,weights,masks))
        np.testing.assert_allclose(expected,-model.pair_logits(b,a,weights,masks))

    def test_same_pool_reverses_with_acceleration_target_and_preserves_ties(self):
        model = self.service.ranker
        weights,masks = np.zeros((2,13),dtype=np.float32),np.zeros((2,13),dtype=np.float32)
        weights[:,4]=masks[:,4]=1
        a,b = np.zeros_like(weights),np.zeros_like(weights)
        a[:,4]=[.2,.8];b[:,4]=[.8,.2]
        logits = model.pair_logits(a,b,weights,masks)
        self.assertLess(logits[0],0);self.assertGreater(logits[1],0)
        np.testing.assert_array_equal(model.pair_logits(a,a,weights,masks),np.zeros(2))

    def test_default_bundle_contract_research_visibility_and_request_isolation(self):
        request = {'profile':{'monthly_income':10000000.,'monthly_expenses':2000000.,
            'existing_monthly_payment':0.,'liquid_assets':1000000000.,'minimum_seats':4,
            'emergency_reserve':0.,'monthly_savings':0.,'annual_distance':15000.,
            'preferred_body_type':'COUPE','body_importance':5},
            'lifestyle':{'acceleration':1.,'performance_importance':5},'k':6}
        with TestClient(create_app(self.service)) as client:
            self.assertTrue(client.get('/api/v2/recommendation-options').json()['data']['lifestyleSupported'])
            response = client.post('/api/v2/recommendations',json=request)
            self.assertEqual(response.status_code,200,response.text)
            data = response.json()['data']
            self.assertEqual(data['trainingScope'],'controlled-synthetic-policy')
            self.assertEqual(data['trainingCatalogCount'],323)
            self.assertEqual(data['traitCoverage']['acceleration_performance'],35)
            self.assertTrue(data['researchSuggestions'])
            self.assertTrue(any(r['vehicle']['body_type']=='COUPE' for r in data['researchSuggestions']))
            for row in data['recommendations']:
                self.assertFalse(row['vehicle']['id'].startswith('research-'))
                self.assertTrue(row['cost']['eligible'])
                self.assertGreaterEqual(row['vehicle']['seats'],4)
            for row in data['researchSuggestions']:
                self.assertIsNone(row['financialEligible'])
                self.assertNotIn('cost',row)
                self.assertEqual(row['comparisonScope'],'taste-only')
                self.assertIn('acceleration_performance',row['evidence'])
            changed = copy.deepcopy(request);changed['lifestyle']['acceleration']=.5
            self.assertEqual(client.post('/api/v2/recommendations',json=changed).status_code,200)
            self.assertEqual(data,client.post('/api/v2/recommendations',json=request).json()['data'])
            invalid = copy.deepcopy(request);invalid['lifestyle']['brand']='BMW'
            self.assertEqual(client.post('/api/v2/recommendations',json=invalid).status_code,400)


if __name__=='__main__':
    unittest.main()
