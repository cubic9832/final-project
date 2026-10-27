import unittest
from dataclasses import replace
from test_vehicle_matching import person,vehicle
from vehicle_matching.retrain_verified_catalog import teacher_keys
class VerifiedCatalogTrainingTests(unittest.TestCase):
 def test_teacher_uses_priority_before_economy_and_cost_only_for_ties(self):
  from vehicle_matching.finance import assess
  p=person(preferred_fuel='HYBRID',fuel_importance=5)
  cheap=vehicle(id='cheap',price=20000000,fuel='GASOLINE')
  matching=vehicle(id='matching',price=30000000,fuel='HYBRID')
  keys=teacher_keys(p,[cheap,matching],[assess(p,v) for v in [cheap,matching]])
  self.assertLess(keys[1],keys[0])
  more_expensive=replace(matching,id='expensive',price=35000000)
  keys=teacher_keys(p,[matching,more_expensive],[assess(p,v) for v in [matching,more_expensive]])
  self.assertLess(keys[0],keys[1])
 def test_new_bundle_preserves_audited_seats_instead_of_legacy_override(self):
  import json,shutil,tempfile
  from pathlib import Path
  from vehicle_matching.api import load_service
  from vehicle_matching.catalog import ROOT,catalog_fingerprint
  source=ROOT/'ml/outputs/models/candidate-preferences/20261026-body-v1'
  with tempfile.TemporaryDirectory() as directory:
   target=Path(directory)
   for name in ('model.pt','metadata.json','catalog.json'):shutil.copyfile(source/name,target/name)
   rows=json.loads((target/'catalog.json').read_text(encoding='utf-8'))
   entry=next(r for r in rows if r['id']=='V-354f355b55d99324')
   entry.update(seats=9,seat_options=[9],seats_status='official-source-verified',trim='Modern 9인승')
   (target/'catalog.json').write_text(json.dumps(rows,ensure_ascii=False),encoding='utf-8')
   meta=json.loads((target/'metadata.json').read_text(encoding='utf-8'))
   meta['training'].update(catalog_mode='verified-runtime-snapshot',catalog_sha256=catalog_fingerprint(target/'catalog.json'))
   (target/'metadata.json').write_text(json.dumps(meta),encoding='utf-8')
   service=load_service(target)
   actual=next(v for v in service.vehicles if v.id==entry['id'])
   self.assertEqual((actual.seats,actual.trim),(9,'Modern 9인승'))
