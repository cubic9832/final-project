"""Controlled preferences, missing evidence, finance safety and saved-data replay."""
import json
from pathlib import Path
import tempfile
import unittest

from tools.data.households.generate_preference_cohorts import (
    ROOT, add_acceleration_evidence, audit_saved, cohort_pool, generate,
    rank_candidates, record_for, sha256,
)
from tools.data.households.generate_lifestyle_choices import safe_cost
from vehicle_matching.finance import Profile


def car(identifier, price, model=None, research=False):
    return {'id':identifier,'brand':'fixture','model':model or identifier,'trim':'base','year':'2026',
        'price':price,'fuel':'GASOLINE','efficiency':12,'source_url':'https://example.test/spec',
        'checked_on':'2026-10-28','seats':4,'seats_status':'official-source-verified',
        'seats_source_url':'https://example.test/spec','length_mm':4300,
        'provenance':{'kind':'unverified-research-candidate' if research else 'existing-snapshot'}}


def traits():
    return {name:{'body_type':body,'body_sources':['https://example.test/spec'],
        'values':{'acceleration_performance':value,'exterior_angularity':None,
                  'exterior_sportiness':None,'seat_capacity':None,'compactness':None},
        'evidence':{'acceleration_performance':{'source_url':'https://example.test/spec'}}}
        for name,body,value in [('a','SEDAN',.2),('b','COUPE',.9),('c','SUV',None)]}


class PreferenceCohortTests(unittest.TestCase):
    def test_preference_alone_reverses_order_and_equal_scores_share_rank(self):
        cars = [car('a',2000000),car('b',1000000)]
        attrs = traits()
        self.assertEqual(rank_candidates(cars,attrs,'acceleration_performance',0)[0]['vehicle_id'],'a')
        self.assertEqual(rank_candidates(cars,attrs,'acceleration_performance',1)[0]['vehicle_id'],'b')
        # A tie must not silently make the lexicographically first ID the winner.
        attrs['a']['values']['acceleration_performance'] = .5
        attrs['b']['values']['acceleration_performance'] = .5
        self.assertEqual([r['rank'] for r in rank_candidates(cars,attrs,'acceleration_performance',1)],[1,1])

    def test_unknown_values_are_excluded_for_all_targets_not_scored_as_zero(self):
        cars = [car(name,1000000) for name in ('a','b','c')]
        attrs = traits()
        pool = cohort_pool(cars,attrs,'acceleration_performance')
        row = record_for('g','test','taste-only',{},cars,attrs,'acceleration_performance',{})
        self.assertEqual(row['candidate_ids'],['a','b'])
        self.assertEqual(row['excluded_unknown_count'],1)
        self.assertTrue(all({r['vehicle_id'] for r in p['ranking']}=={'a','b'} for p in row['profiles']))
        with self.assertRaisesRegex(ValueError,'Unknown trait'):
            rank_candidates(cars,attrs,'acceleration_performance',1)
        self.assertEqual(len(pool),2)

    def test_finance_gate_excludes_fast_unaffordable_and_research_cars(self):
        profile = Profile(5000000,1000000,0,10000000,0,0,0,15000,0,financing_mode='recommendation')
        cars = [car('a',2000000),car('b',20000000),car('c',1000000,research=True)]
        self.assertIsNotNone(safe_cost(profile,cars[0]))
        self.assertIsNone(safe_cost(profile,cars[1]))
        self.assertIsNone(safe_cost(profile,cars[2]))

    def test_acceleration_import_requires_exact_identity_and_unambiguous_units(self):
        cars, attrs = [car('a',1000000)], {'a':traits()['a']}
        attrs['a']['values']['acceleration_performance'] = None
        attrs['a']['evidence'] = {}
        row = {**cars[0],'source_url':'https://example.test/spec',
            'fields':[{'label':'0–100 km/h','value':'4.2 s'}]}
        enriched = add_acceleration_evidence(cars,attrs,{'vehicles':[row]})
        self.assertAlmostEqual(enriched['a']['values']['acceleration_performance'],.78)
        self.assertIsNone(attrs['a']['values']['acceleration_performance'])
        dealer = {**row,'fields':[{'label':'Performance · 0-100 km/h','value':'3.3s'}]}
        self.assertAlmostEqual(add_acceleration_evidence(cars,attrs,{'vehicles':[dealer]})['a']['values']['acceleration_performance'],.87)
        with self.assertRaisesRegex(ValueError,'identity mismatch'):
            add_acceleration_evidence(cars,attrs,{'vehicles':[{**row,'year':'2020'}]})
        for fields in ([{'label':'0–100 km/h','value':'4.2 / 4.5 s'}],
                       [{'label':'0–100 km/h','value':'4.2 s','status':'source-conflict'}],
                       [{'label':'0–100 km/h','value':'4.2 s'},{'label':'가속','value':'4.5 SEC'}]):
            result = add_acceleration_evidence(cars,attrs,{'vehicles':[{**row,'fields':fields}]})
            self.assertIsNone(result['a']['values']['acceleration_performance'])

    def test_generation_is_reproducible_financially_grouped_and_auditable(self):
        cars = [car(name,1000000) for name in ('a','b','c')]
        (ROOT/'tmp').mkdir(exist_ok=True)
        with tempfile.TemporaryDirectory(dir=ROOT/'tmp') as temporary:
            a,b = Path(temporary)/'a',Path(temporary)/'b'
            reports = [generate(path,rows,traits(),groups=4,seed=33) for path,rows in ((a,cars),(b,list(reversed(cars))))]
            self.assertEqual((a/'comparisons.jsonl').read_bytes(),(b/'comparisons.jsonl').read_bytes())
            self.assertEqual((a/'rankings.csv').read_bytes(),(b/'rankings.csv').read_bytes())
            groups = {}
            rows = [json.loads(line) for line in (a/'comparisons.jsonl').read_text(encoding='utf-8').splitlines()]
            for row in rows:
                self.assertEqual(groups.setdefault(row['group_id'],(row['financial'],row['split'])),(row['financial'],row['split']))
                if row['task']=='taste-only':
                    self.assertIsNone(row['financial_eligible'])
                    self.assertEqual(row['costs'],{})
            self.assertEqual(audit_saved(a)['comparisons_checked'],reports[0]['comparisons'])
            with self.assertRaises(FileExistsError):
                generate(a,cars,traits(),groups=1)
            # Even when a caller refreshes the file hash, replay catches wrong labels.
            rows[0]['profiles'][0]['ranking'][0]['policy_score'] = .123
            (a/'comparisons.jsonl').write_text('\n'.join(json.dumps(row) for row in rows)+'\n',encoding='utf-8')
            report = json.loads((a/'generation_report.json').read_text(encoding='utf-8'))
            report['snapshot_hashes']['comparisons.jsonl'] = sha256(a/'comparisons.jsonl')
            (a/'generation_report.json').write_text(json.dumps(report),encoding='utf-8')
            with self.assertRaisesRegex(ValueError,'ranking or candidate pool'):
                audit_saved(a)


if __name__ == '__main__':
    unittest.main()
