import json
import unittest

from vehicle_matching.api import load_service
from vehicle_matching.catalog import ROOT, read_catalog
from vehicle_matching.catalog_merge import LEGACY_CATALOGS, expand_catalog
from vehicle_matching.service import CandidateService
from test_vehicle_matching import person


class CatalogExpansionTests(unittest.TestCase):
    def test_expansion_preserves_every_old_configuration_and_every_new_candidate(self):
        original = read_catalog(ROOT / 'ml/experiments/candidate-v2/catalog.json')
        merged, _ = expand_catalog(original)
        by_id = {v.id: v for v in merged}
        for v in original:
            self.assertEqual(by_id[v.id], v)
        for path in LEGACY_CATALOGS:
            for row in json.loads(path.read_text(encoding='utf-8')):
                self.assertTrue(any(v.brand == row['brand'] and v.model == row['model']
                                    and v.trim == row['trim'] and v.price == row['price_won']
                                    and v.source_url == row['source_url'] for v in merged), row['configuration_id'])
        again, _ = expand_catalog(merged)
        self.assertEqual(merged, again)
        self.assertEqual(len(by_id), len(merged))

    def test_all_imported_models_reach_inference_and_unknown_dimensions_remain_visible(self):
        service = load_service(ROOT / 'ml/experiments/candidate-v2')
        imported = [v for v in service.vehicles if v.id.startswith('legacy-IMP-')]
        expected = {(v.brand, v.model) for v in imported}
        self.assertEqual(len(expected), 6)
        subset = CandidateService(service.ranker, imported)
        from dataclasses import replace
        rich = replace(person(),liquid_assets=300000000)
        result = subset.recommend(rich, k=20)
        self.assertEqual({(r['vehicle']['brand'], r['vehicle']['model']) for r in result['recommendations']}, expected)
        unknown_size = subset.recommend(replace(rich, preferred_size='medium'), k=20)
        self.assertEqual(unknown_size['conditionalRecommendations'], [])
        self.assertEqual({(r['vehicle']['brand'], r['vehicle']['model']) for r in unknown_size['recommendations']}, expected)
        for row in unknown_size['recommendations']:
            self.assertEqual(row['lengthVerificationRequired'], row['vehicle']['length_mm'] is None)
            self.assertFalse(row['seatingVerificationRequired'])
            if row['lengthVerificationRequired']:
                self.assertEqual(next(c for c in row['preferenceAssessment']['components'] if c['key'] == 'space')['score'], 50)
        unknown = CandidateService(service.ranker, [replace(imported[0], length_mm=None)])
        missing = unknown.recommend(replace(rich, preferred_size='medium'))['recommendations'][0]
        self.assertTrue(missing['lengthVerificationRequired'])
        self.assertEqual(next(c for c in missing['preferenceAssessment']['components'] if c['key']=='space')['score'],50)
        poor = subset.recommend(replace(person(), monthly_income=1000000), k=20)
        self.assertEqual(poor['recommendations'] + poor['conditionalRecommendations'], [])

    def test_supplement_fills_affordable_electric_and_small_car_gaps_without_breaking_cash_limit(self):
        from dataclasses import replace
        service = load_service(ROOT / 'ml/experiments/candidate-v2')
        base = replace(person(), liquid_assets=45000000, preferred_fuel='ELECTRIC', fuel_importance=5)
        result = service.recommend(base)
        models = {r['vehicle']['model'] for r in result['recommendations']}
        self.assertIn('레이 EV', models)
        self.assertIn('캐스퍼 일렉트릭', models)
        self.assertTrue(all(r['vehicle']['fuel'] == 'ELECTRIC' for r in result['recommendations']))
        self.assertTrue(all(r['vehicle']['price'] <= 40000000 for r in result['recommendations']))
        cheap = service.recommend(replace(base, liquid_assets=25000000, preferred_fuel='GASOLINE'), k=20)
        self.assertIn('캐스퍼', {r['vehicle']['model'] for r in cheap['recommendations']})
        diesel = service.recommend(replace(base, liquid_assets=100000000, preferred_fuel='DIESEL'), k=20)
        self.assertTrue(any(r['vehicle']['id'].startswith('supp-') and r['vehicle']['fuel']=='DIESEL'
                            for r in diesel['recommendations']))
        self.assertTrue(all(r['cost']['eligible'] for r in diesel['recommendations']))

    def test_official_corrections_enrich_saved_catalog_and_change_running_cost(self):
        from dataclasses import replace
        from vehicle_matching.finance import assess
        service = load_service(ROOT / 'ml/experiments/candidate-v2')
        saved = [replace(v, efficiency=None, length_mm=None, space_source_url=None)
                 if v.model == '레이 EV' else v for v in service.vehicles]
        service.vehicles, _ = expand_catalog(saved)
        rays = [v for v in service.vehicles if v.model == '레이 EV']
        self.assertEqual(len(rays), 2)
        p = replace(person(), financing_mode='recommendation', down_payment=0, months=0)
        for v in rays:
            cost = assess(p, v)
            self.assertFalse(cost['efficiency_estimated'])
            self.assertEqual(cost['monthly_running_cost'], 270785)
            score = service.recommend(replace(p, preferred_size='small', preferred_fuel='ELECTRIC'), k=20)
            row = next(r for r in score['recommendations'] if r['vehicle']['model'] == '레이 EV')
            self.assertFalse(row['lengthVerificationRequired'])
        x5 = next(v for v in service.vehicles if v.id.startswith('supp-') and v.model == 'X5')
        self.assertEqual(x5.seats, 7)
        merged, _ = expand_catalog(service.vehicles)
        self.assertEqual(merged, service.vehicles)
