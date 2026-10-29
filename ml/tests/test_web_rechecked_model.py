import unittest
from fastapi.testclient import TestClient
from vehicle_matching.api import create_app,load_service
from vehicle_matching.catalog import ROOT


class WebRecheckedModelTests(unittest.TestCase):
    def test_rechecked_evidence_reaches_api_without_financial_promotion(self):
        service=load_service(ROOT/'ml/outputs/models/preference-cohorts/20261028-v6-web-recheck')
        old=load_service(ROOT/'ml/outputs/models/preference-cohorts/20261028-v4-complete')
        self.assertEqual(service.catalog,old.catalog)
        reference=[r for r in service.traits.values() if r['specifications']['width_mm']['status']=='cross-site-reported']
        self.assertTrue(reference)
        self.assertTrue(all(r['specifications']['width_mm']['source_count']>=3 for r in reference))
        request={'profile':{'monthly_income':10000000.,'monthly_expenses':2000000.,
            'existing_monthly_payment':0.,'liquid_assets':1000000000.,'minimum_seats':0,
            'emergency_reserve':0.,'monthly_savings':0.,'annual_distance':15000.,
            'preferred_size':'large','space_importance':5},'lifestyle':{'acceleration':1.},'k':6}
        with TestClient(create_app(service)) as client:
            response=client.post('/api/v2/recommendations',json=request)
            self.assertEqual(response.status_code,200,response.text)
            data=response.json()['data']
            self.assertEqual(data['modelBundle'],'20261028-v6-web-recheck')
            self.assertTrue(data['recommendations'])
            for row in data['recommendations']:
                self.assertTrue(row['cost']['eligible'])
                self.assertEqual(len(row['lifestyleEvidence']['specifications']),28)
            for row in data['researchSuggestions']:
                self.assertIsNone(row['financialEligible'])
                self.assertNotIn('cost',row)
                verification=row['salesVerification']
                self.assertEqual(verification['identity']['id'],row['vehicle']['id'])
                self.assertEqual(verification['financial_assessment'],'not-assessed')
                if verification['price']['value'] is None:
                    self.assertEqual(row['specifications']['price_won']['value'],'미확인')


if __name__=='__main__':
    unittest.main()
