import copy
import json
import unittest

from tools.data.vehicles.recheck_vehicle_evidence import apply_reviews,select_evidence
from tools.data.vehicles.recheck_official_dimensions import dimensions,ROOT


def sample(number,value,**extra):
    return dict(publisher=f'publisher-{number}',origin_id=f'origin-{number}',
        url=f'https://site{number}.example/specs',values={'width_mm':value},
        conditions='same generation, same body, width excludes mirrors',
        evidence_type='reported-specification',verification='page-reviewed',compatible=True,**extra)


class WebRecheckTests(unittest.TestCase):
    def test_three_sources_are_required_and_median_keeps_range(self):
        rows=[sample(1,1850),sample(2,1852),sample(3,1854)]
        self.assertIsNone(select_evidence('width_mm',rows[:2])[0])
        result,_=select_evidence('width_mm',rows)
        self.assertEqual(result['value'],1852)
        self.assertEqual(result['observed_range'],[1850,1854])
        self.assertEqual(result['status'],'cross-site-reported')
        rows.append(sample(4,2000))
        self.assertEqual(select_evidence('width_mm',rows)[1],'conflicting-values')

    def test_copies_and_same_site_never_inflate_count(self):
        rows=[sample(n,1852) for n in range(3)]
        for key in ('publisher','origin_id','url'):
            clones=copy.deepcopy(rows)
            for r in clones:r[key]=rows[0][key]
            self.assertIsNone(select_evidence('width_mm',clones)[0])

    def test_conditions_and_measurement_types_cannot_be_mixed(self):
        rows=[sample(n,1852) for n in range(3)]
        rows[0]['compatible']=False
        self.assertIsNone(select_evidence('width_mm',rows)[0])
        rows[0]['compatible']=True;rows[0]['evidence_type']='instrumented-test'
        self.assertIsNone(select_evidence('width_mm',rows)[0])
        rows[0]['verification']='search-snippet-only'
        self.assertIsNone(select_evidence('width_mm',rows)[0])

    def test_official_priority_units_and_conflicting_official_copies(self):
        rows=[sample(1,1852,official=True),sample(2,2000),sample(3,2000)]
        result,_=select_evidence('width_mm',rows)
        self.assertEqual(result['value'],1852)
        rows.append(sample(4,1900,official=True))
        self.assertIsNone(select_evidence('width_mm',rows)[0])
        inch=sample(1,72.9);inch['units']={'width_mm':'inch'};inch['official']=True
        self.assertAlmostEqual(select_evidence('width_mm',[inch])[0]['value'],1851.7)

    def test_only_estimates_are_replaced_without_mutating_input(self):
        cars=[{'id':'car','brand':'brand','model':'model','trim':'trim','specifications':
            {'width_mm':{'value':1800,'status':'estimated'},'height_mm':{'value':1400,'status':'official-reference'}}}]
        registry={'reviews':[{'selector':{'brand':'brand','model':'model','trims':['trim']},
            'scope':'same body','samples':[sample(n,1852) for n in range(3)]}]}
        updated,changes,_=apply_reviews(cars,registry)
        self.assertEqual(updated[0]['specifications']['width_mm']['value'],1852)
        self.assertEqual(cars[0]['specifications']['width_mm']['value'],1800)
        self.assertEqual(updated[0]['specifications']['height_mm']['value'],1400)
        self.assertEqual(len(changes),1)
        registry['reviews'][0]['selector']['trims']=['different']
        self.assertEqual(apply_reviews(cars,registry)[1],[])

    def test_ambiguous_dimensions_and_invalid_units_are_rejected(self):
        document={'pages':[{'text':'전장(mm) 4,910\n전폭(mm) 1,860\n전고(mm) 1,445\n축간거리(mm) 2,840'},
            {'text':'전고(mm) 1,470'}]}
        parsed=dimensions(document)
        self.assertNotIn('height_mm',parsed)
        self.assertEqual(parsed['wheelbase_mm'],2840)
        wrong=sample(1,1852,official=True);wrong['units']={'width_mm':'kg'}
        with self.assertRaises(ValueError):select_evidence('width_mm',[wrong])
        with self.assertRaises(ValueError):select_evidence('width_mm',[sample(1,11686,official=True)])

    def test_saved_recheck_preserves_verified_values_and_documents_three_site_changes(self):
        read=lambda p:json.loads(p.read_text(encoding='utf-8'))
        base={r['id']:r for r in read(ROOT/'data/vehicles/complete-specifications-20261028/vehicles.json')}
        current=read(ROOT/'data/vehicles/web-recheck-20261028/vehicles.json')
        self.assertEqual(set(base),{r['id'] for r in current})
        for car in current:
            for key,spec in car['specifications'].items():
                self.assertNotIn(spec['value'],(None,''))
                if base[car['id']]['specifications'][key]['status']!='estimated':
                    self.assertEqual(spec,base[car['id']]['specifications'][key])
                if spec['status'].startswith('cross-site'):
                    self.assertGreaterEqual(spec['source_count'],3)
                    self.assertIn('previous_estimate',spec)
                    self.assertEqual(spec['evidence_type'],'reported-specification')


if __name__=='__main__':
    unittest.main()
