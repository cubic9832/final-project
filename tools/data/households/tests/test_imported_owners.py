from tools.data.households.paths import SYNTHETIC_ROOT

import json
import unittest
from pathlib import Path

from tools.data.households.generate_imported_owners import create_dataset,inventory_from_catalog,validate


class ImportedOwnersTest(unittest.TestCase):
    def test_balanced_owners_have_reconciled_funding_and_noncolliding_ids(self):
        root=SYNTHETIC_ROOT / 'imported-owners'
        config=json.loads((root/'generation_config.json').read_text(encoding='utf-8'))
        catalog=json.loads((root/'catalog.json').read_text(encoding='utf-8'))
        config.update(owners_per_model=10,candidate_count=600)
        inventory=inventory_from_catalog(catalog)
        rows,audit,rejected=create_dataset(config,catalog,inventory)
        self.assertEqual((rows,audit,rejected),create_dataset(config,catalog,inventory))
        report=validate(rows,audit,catalog,inventory)
        self.assertEqual(report['profiles'],60)
        self.assertEqual(set(report['model_counts'].values()),{10})
        self.assertTrue(all(int(r['프로필_식별자'][1:])>10000 for r in rows))
        self.assertTrue(all(a['가족지원금_가정_원']<=10000000 for a in audit))


if __name__=='__main__':unittest.main()
