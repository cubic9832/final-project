from tools.data.households.paths import SYNTHETIC_ROOT

import json
import unittest
from pathlib import Path

from tools.data.households.generate_owner_population import create_catalog,generate_population,validate_population


class OwnerPopulationTest(unittest.TestCase):
    def test_every_profile_owns_vehicle_and_population_is_reproducible(self):
        root=SYNTHETIC_ROOT
        config=json.loads((root/'owner_population_config.json').read_text(encoding='utf-8'))
        config['count']=400
        catalog=create_catalog(json.loads((root/'ownership/vehicle-label-catalog.json').read_text(encoding='utf-8')))
        rows,audit=generate_population(config,catalog)
        self.assertEqual((rows,audit),generate_population(config,catalog))
        self.assertEqual(validate_population(rows,catalog)['profiles'],400)
        self.assertTrue(all(r['보유차량_모델'] for r in rows))
        self.assertTrue(any(r['cross_group_draw'] for r in audit))
        self.assertEqual(len({r['프로필_식별자'] for r in rows}),400)

    def test_catalog_merges_fuel_variants_under_same_model(self):
        source=[{'brand':'현대','model':'예시','segment':'중형','body':'세단'},
                {'brand':'현대','model':'예시 Hybrid','segment':'중형','body':'세단'}]
        catalog=create_catalog(source)
        self.assertEqual(len(catalog),1)
        self.assertEqual(len(catalog[0]['source_variants']),2)


if __name__=='__main__':unittest.main()
