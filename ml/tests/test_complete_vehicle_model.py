import unittest
from fastapi.testclient import TestClient
from vehicle_matching.api import create_app, load_service
from vehicle_matching.catalog import ROOT


class CompleteVehicleModelTests(unittest.TestCase):
    def test_completed_specs_reach_results_without_promoting_research_eligibility(self):
        service=load_service(ROOT/'ml/outputs/models/preference-cohorts/20261028-v4-complete')
        request={'profile':{'monthly_income':10000000.,'monthly_expenses':2000000.,
            'existing_monthly_payment':0.,'liquid_assets':1000000000.,'minimum_seats':4,
            'emergency_reserve':0.,'monthly_savings':0.,'annual_distance':15000.,
            'preferred_body_type':'COUPE','body_importance':5,'preferred_size':'large','space_importance':5},
            'lifestyle':{'acceleration':1.,'performance_importance':5},'k':6}
        with TestClient(create_app(service)) as client:
            response=client.post('/api/v2/recommendations',json=request)
            self.assertEqual(response.status_code,200,response.text)
            data=response.json()['data']
            self.assertTrue(all(n==323 for n in data['traitCoverage'].values()))
            self.assertTrue(data['recommendations'])
            self.assertTrue(data['researchSuggestions'])
            for row in data['recommendations']:
                specs=row['lifestyleEvidence']['specifications']
                self.assertTrue(all(s['value'] is not None and s['value']!='' for s in specs.values()))
                self.assertTrue(row['cost']['eligible'])
                self.assertGreaterEqual(row['vehicle']['seats'],4)
            for row in data['researchSuggestions']:
                self.assertIsNone(row['financialEligible'])
                self.assertEqual(len(row['specifications']),28)
                self.assertNotIn('cost',row)
            request['profile']['minimum_seats']=0
            response=client.post('/api/v2/recommendations',json=request)
            self.assertEqual(response.status_code,200,response.text)
            self.assertTrue(response.json()['data']['recommendations'])


if __name__=='__main__':
    unittest.main()
