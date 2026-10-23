from tools.data.households.paths import SYNTHETIC_ROOT

import json
import unittest
from pathlib import Path

from tools.data.households.refine_owner_purchases import funding_terms,option_variants


class PurchaseRefinementTest(unittest.TestCase):
    def setUp(self):
        self.config=json.loads((SYNTHETIC_ROOT/'purchase_refinement_config.json').read_text(encoding='utf-8'))
        self.row={'경력_구분':'사회초년생','개인_현금성자산_원':10000000,'개인_평균월대출상환액_원':200000}

    def test_dependent_option_cannot_be_selected_alone(self):
        options=self.config['verified_options']['쏘나타 디 엣지|가솔린 1.6 터보|Premium']
        variants=option_variants({'verified_options':options})
        for chosen,total in variants:
            ids={o['id'] for o in chosen}
            if 'SON-PARK1' in ids:self.assertIn('SON-NAV1',ids)
            self.assertEqual(total,sum(o['price_won'] for o in chosen))
        self.assertIn(([],0),variants)

    def test_large_support_does_not_bypass_early_career_price_limit(self):
        self.assertIsNone(funding_terms(self.row,50000000,100000000,35000000,100000000,self.config))

    def test_insufficient_self_funding_is_rejected(self):
        self.assertIsNone(funding_terms(self.row,20000000,0,35000000,0,self.config))

    def test_feasible_purchase_reconciles_cost_and_credit_limit(self):
        terms=funding_terms(self.row,20000000,0,35000000,10000000,self.config)
        self.assertIsNotNone(terms)
        self.assertEqual(terms['cost'],21400000)
        self.assertGreaterEqual(terms['min_own'],1400000)
        self.assertLessEqual(terms['cost']-terms['min_own'],terms['finance_cap'])


if __name__=='__main__':unittest.main()
