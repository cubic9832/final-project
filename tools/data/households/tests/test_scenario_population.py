"""Core finance, preference and persisted-dataset contracts."""
from dataclasses import replace
from collections import Counter
import json
from pathlib import Path
import random
import tempfile
import unittest

import numpy as np

from vehicle_matching.catalog import ROOT, read_catalog
from vehicle_matching.finance import Profile, assess
from vehicle_matching.scenario_features import channel_values, utility, probability_a
from tools.data.households.audit_scenario_population import audit
from tools.data.households.generate_scenario_population import (
    DEFAULT_CONFIG, DEFAULT_SEEDS, choose_pairs, eligible_candidates, generate, load_seeds, sample_user,
)
from tools.data.households.scenario_coverage import coverage_report, model_key, select_candidates
from tools.data.vehicles.scenario_seating import apply_registry


class ScenarioPopulationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cars = read_catalog(DEFAULT_SEEDS/'catalog.json')
        cls.seeds = load_seeds(DEFAULT_SEEDS,cls.cars)
        cls.config = json.loads(DEFAULT_CONFIG.read_text(encoding='utf-8'))
        cls.small_config = DEFAULT_CONFIG.with_name('scenario_population_config.json')
        cls.temp_root = ROOT / 'tmp' / 'scenario-tests'
        cls.temp_root.mkdir(parents=True, exist_ok=True)

    def test_financial_and_seating_constraints_reject_candidates(self):
        user, profile, _ = sample_user(self.seeds[0],self.seeds[1],random.Random(3),self.config,0)
        self.assertFalse(eligible_candidates(replace(profile,liquid_assets=100000,emergency_reserve=0),self.cars))
        high_seats = replace(profile,minimum_seats=9,liquid_assets=300000000,purchase_price_ceiling=200000000)
        pool = eligible_candidates(high_seats,self.cars)
        self.assertTrue(pool)
        self.assertTrue(all(v.seats>=9 for entries in pool.values() for _,v,_ in entries))

    def test_cash_boundary_and_asset_supported_deficit(self):
        v = min(self.cars,key=lambda c:c.price)
        p = Profile(**self.seeds[0]['profile'])
        p = replace(p,liquid_assets=v.price,emergency_reserve=0,purchase_price_ceiling=v.price)
        self.assertTrue(assess(p,v)['eligible'])
        self.assertFalse(assess(replace(p,liquid_assets=v.price-1),v)['eligible'])
        deficit_profile = replace(p,monthly_income=0,monthly_expenses=100000,monthly_savings=0,existing_monthly_payment=0,minimum_buffer=0)
        running = assess(deficit_profile,v)['monthly_running_cost']
        boundary = v.price+12*(running+100000)
        self.assertTrue(assess(replace(deficit_profile,liquid_assets=boundary),v)['eligible'])
        self.assertFalse(assess(replace(deficit_profile,liquid_assets=boundary-1),v)['eligible'])

    def test_observable_taste_can_reverse_same_finance_comparison(self):
        user,p,_ = sample_user(self.seeds[0],self.seeds[1],random.Random(4),self.config,0)
        cars = [next(v for v in self.cars if v.model==name) for name in ('모닝','베뉴')]
        user['profile']['preferred_body_type']='HATCHBACK'
        first = [channel_values(user,v,assess(p,v)) for v in cars]
        weights = [0,0,1,0,0,0,0,0]
        self.assertGreater(utility(first[0],weights),utility(first[1],weights))
        user['profile']['preferred_body_type']='SUV'
        second = [channel_values(user,v,assess(p,v)) for v in cars]
        self.assertLess(utility(second[0],weights),utility(second[1],weights))

    def test_probability_symmetry_and_invalid_temperature(self):
        self.assertAlmostEqual(probability_a(.3,.8,.05)+probability_a(.8,.3,.05),1)
        self.assertEqual(probability_a(1,1,.05),.5)
        with self.assertRaises(ValueError):
            probability_a(1,1,0)

    def test_broad_taste_choices_have_no_brand_or_model_preference_signal(self):
        config = {**self.config,'identity_preferences':False}
        for index in range(20):
            user,_,_ = sample_user(self.seeds[index],self.seeds[(index+1)%len(self.seeds)],random.Random(index),config,index)
            self.assertEqual(user['preferred_brands'],[])
            self.assertEqual(user['model_affinities'],{})
            self.assertEqual(user['channel_weights'][5:7],[0.,0.])

    def test_saved_generation_is_reproducible_auditable_and_refuses_overwrite(self):
        with tempfile.TemporaryDirectory(dir=self.temp_root) as temp:
            first,second = Path(temp)/'a',Path(temp)/'b'
            for output in (first,second):
                generate(output,profiles=12,pairs_per_user=4,shard_size=5,seed=41,config_path=self.small_config)
                self.assertEqual(audit(output)['comparisons'],48)
            for path in first.rglob('*'):
                if path.is_file():
                    self.assertEqual(path.read_bytes(),(second/path.relative_to(first)).read_bytes(),str(path))
            with self.assertRaises(FileExistsError):
                generate(first,profiles=12,pairs_per_user=4,config_path=self.small_config)
            npz = next(first.glob('shard-*/*_choices.npz'))
            npz.write_bytes(b'corrupted')
            with self.assertRaisesRegex(ValueError,'Checksum mismatch'):
                audit(first)

    def test_impossible_pair_request_fails_before_creating_output(self):
        with tempfile.TemporaryDirectory(dir=self.temp_root) as temp:
            output = Path(temp)/'impossible'
            with self.assertRaises(ValueError):
                generate(output,pairs_per_user=1000)
            self.assertFalse(output.exists())

    def test_seating_supplement_preserves_original_and_rejects_conflict(self):
        fixed,report = apply_registry(self.cars,ROOT/'data/vehicles/scenario-seating-20261029/registry.json')
        self.assertEqual(report['models'],6)
        self.assertEqual(report['specifications'],14)
        for before,after in zip(self.cars,fixed):
            if before.seats is None:
                self.assertEqual(after.seats,5)
                self.assertTrue(after.seats_source_url)
                self.assertIsNone(before.seats)
        conflicting = [replace(v,seats=2) if v.model=='Golf GTI' else v for v in self.cars]
        with self.assertRaisesRegex(ValueError,'Conflicting'):
            apply_registry(conflicting,ROOT/'data/vehicles/scenario-seating-20261029/registry.json')

    def test_added_personas_supply_expensive_pickup_and_hatchback_candidates(self):
        fixed,_ = apply_registry(self.cars,ROOT/'data/vehicles/scenario-seating-20261029/registry.json')
        seeds = load_seeds(DEFAULT_SEEDS,fixed,ROOT/'data/households/synthetic/scenario-seeds-v2-20261029/additional_personas.json')
        lookup = {u['id']:u for u in seeds}
        for name,model in [('AP031','HUMMER EV SUV'),('AP034','무쏘'),('AP035','무쏘 EV'),('AP036','Sierra'),
                           ('AP037','Golf'),('AP038','Golf GTI'),('AP039','308 SMART HYBRID')]:
            user = lookup[name]
            pool = eligible_candidates(Profile(**user['profile']),fixed)
            self.assertTrue(any(family[1]==model for family in pool),name)

    def test_low_exposure_candidates_enter_actual_pairs_without_rewriting_users(self):
        user,p,_ = sample_user(self.seeds[0],self.seeds[1],random.Random(6),self.config,0)
        pool = eligible_candidates(p,self.cars)
        families = list(pool)
        counts = Counter({model_key(entries[0][1]):100 for entries in pool.values()})
        target = pool[families[0]][0][1]
        counts[model_key(target)] = 0
        candidates,required = select_candidates(pool,random.Random(6),counts,Counter(),2,0,6,3)
        pairs,_,_ = choose_pairs(candidates,user,random.Random(6),3,['random'],required)
        used_models = {candidates[i][1].model for a,b,_ in pairs for i in (a,b)}
        self.assertIn(target.model,used_models)
        # Missing train exposure must fail even when another split already used the model.
        report = coverage_report([target],{'train':Counter(),'test':Counter({model_key(target):10})},
                                  Counter({target.id:10}),{'train':1},1)
        self.assertEqual(report['status'],'failed')


if __name__=='__main__':
    unittest.main()
