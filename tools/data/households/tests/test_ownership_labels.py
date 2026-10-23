from tools.data.households.paths import SYNTHETIC_ROOT

import unittest
from pathlib import Path
import json

from tools.data.households.label_ownership import candidate_budget, preference_score


class OwnershipLabelsTest(unittest.TestCase):
    def setUp(self):
        self.config = json.loads((SYNTHETIC_ROOT/'ownership_config.json').read_text(encoding='utf-8'))
        self.profile = {'monthly_net_income_won':5000000,'monthly_extra_income_won':0,
                        'liquid_cash_won':30000000,'emergency_target_won':6000000,'household_size':4}
        self.expense = {'living_won':2000000,'transport_won':200000,'target_savings_won':500000}
        self.vehicle = {'price_won':20000000,'combined_efficiency':15,'fuel':'GASOLINE','body':'세단','segment':'중형'}

    def test_cash_purchase_preserves_emergency_and_avoids_halved_transport_double_count(self):
        result = candidate_budget(self.profile,self.expense,0,12000,self.vehicle,self.config)
        self.assertEqual(result['monthly_payment_won'],0)
        self.assertEqual(result['cash_remaining_won'],8600000)
        self.assertEqual(result['monthly_remaining_won'],
                         2300000-result['monthly_running_won']+100000)

    def test_no_candidates_when_existing_debt_consumes_income(self):
        self.assertIsNone(candidate_budget(self.profile,self.expense,4000000,12000,self.vehicle,self.config))

    def test_no_candidate_when_registration_uses_emergency(self):
        self.profile['liquid_cash_won']=6000000
        self.assertIsNone(candidate_budget(self.profile,self.expense,0,12000,self.vehicle,self.config))

    def test_family_preference_increases_suv_score_at_same_price(self):
        sedan=preference_score(self.profile,'가족이동','세단',12000,self.vehicle,self.config)
        suv=preference_score(self.profile,'가족이동','세단',12000,dict(self.vehicle,body='SUV'),self.config)
        self.assertGreater(suv,sedan)


if __name__=='__main__': unittest.main()
