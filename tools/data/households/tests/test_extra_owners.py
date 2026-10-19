from tools.data.households.paths import SYNTHETIC_ROOT

import copy
import json
import unittest
from pathlib import Path

from tools.data.households.generate_extra_owners import validate
from tools.data.households.refine_owner_purchases import build_inventory


class ExtraOwnersTest(unittest.TestCase):
    def test_validator_detects_corrupted_purchase_funding(self):
        parent=SYNTHETIC_ROOT
        def read(path):return json.loads(path.read_text(encoding='utf-8'))
        rows=read(parent/'owner-funded/learning-rows.json')[:1]
        audit=read(parent/'owner-funded/purchase-audit.json')[:1]
        inventory=build_inventory(read(parent.parent.parent/'vehicles/normalized-vehicle-details.json'),
                                  read(parent/'owner-population/vehicle-label-catalog.json'),
                                  read(parent/'purchase_refinement_config.json'))
        validate(rows,audit,inventory,1)
        broken=copy.deepcopy(audit)
        broken[0]['본인구매자금_원']+=1000
        with self.assertRaises(AssertionError):validate(rows,broken,inventory,1)


if __name__=='__main__':unittest.main()
