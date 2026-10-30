"""Generate choices for current UI, without changing prior datasets or checkpoints."""
import argparse
from collections import Counter
from dataclasses import asdict
import hashlib
import itertools
import json
import math
from pathlib import Path
import random
import numpy as np

from vehicle_matching.catalog import ROOT, read_catalog
from vehicle_matching.finance import Profile, assess
from vehicle_matching.recommendation_policy import seating_status
from vehicle_matching.ui_scenario_features import FEATURE_NAMES, encode_ui_scenario, choice_utility
from tools.data.households.generate_scenario_population import file_hash, write_json
from tools.data.households.scenario_coverage import select_candidates, model_key, coverage_report

SOURCE = ROOT/'data/households/synthetic/scenario-population-v3-broad-taste-10k-20261029'
TRAITS = ROOT/'data/vehicles/scenario-traits-20261030/vehicle_traits.json'
VERSION = 'ui-scenario-population-v1'


def generate(output, profiles=10000, seed=20261030):
    output = Path(output); output.mkdir(parents=True,exist_ok=False)
    rng = random.Random(seed)
    seeds = json.loads((SOURCE/'seed_personas.json').read_text(encoding='utf-8'))
    catalog = read_catalog(SOURCE/'catalog.json')
    traits = json.loads(TRAITS.read_text(encoding='utf-8'))['vehicles']
    (output/'catalog.json').write_bytes((SOURCE/'catalog.json').read_bytes())
    (output/'vehicle_traits.json').write_bytes(TRAITS.read_bytes())
    model_counts = {role:Counter() for role in ('train','validation','test')}
    spec_counts, counts, seen, partitions, attempts = Counter(), Counter(), set(), {}, 0
    shards = []
    settings = {'version':VERSION,'seed':seed,'profiles':profiles,'pairs_per_user_max':10,'source_personas':len(seeds),
                'optional_probability':.35,'temperature':.25,'split':[.7,.15,.15],
                'distance':15000,'retired_body_preference':'any','unknown_charging':'neutral',
                'model_minimum':{'train':20,'validation':5,'test':5},'spec_minimum':1}
    write_json(output/'configuration.json',settings)
    accepted = 0
    while accepted < profiles:
        buckets = {role:dict(features=[],comparisons=[],labels=[],profile_ids=[],vehicle_indices=[],users=[],choices=[])
                   for role in model_counts}
        target = min(1000,profiles-accepted); number = 0
        while number < target:
            attempts += 1
            if attempts > profiles*30: raise ValueError('Insufficient eligible user contexts')
            source = rng.choice(seeds)
            p = dict(source['profile']); scale = rng.lognormvariate(0,.35)
            for name in ('monthly_income','monthly_expenses','existing_monthly_payment','liquid_assets'):
                p[name] = round(p[name]*scale*rng.uniform(.9,1.1)/10000)*10000
            p.update(down_payment=0,months=0,annual_rate=0,emergency_reserve=0,monthly_savings=0,
                     minimum_buffer=0,annual_distance=15000,purpose='commute',purpose_importance=1,
                     preferred_body_type='any',body_importance=3,seating_importance=3,
                     financing_mode='recommendation',purchase_price_ceiling=0)
            p['minimum_seats'] = rng.choice([0,0,0,2,3,4,5,5,6,7,8,9])
            p['preferred_fuel'] = None if rng.random()<.35 else rng.choice(['GASOLINE','HYBRID','DIESEL','LPG','ELECTRIC'])
            p['preferred_size'] = 'any' if rng.random()<.35 else rng.choice(['small','medium','large'])
            p['charging_available'] = rng.choice([True,False]) if p['preferred_fuel']=='ELECTRIC' else False
            for name in ('cost_importance','space_importance','fuel_importance'):p[name]=rng.choice([1,3,5])
            profile = Profile(**p)
            finance = {key:p[key] for key in ('monthly_income','monthly_expenses','existing_monthly_payment','liquid_assets')}
            group = hashlib.sha256(json.dumps(finance,sort_keys=True).encode()).hexdigest()
            if group in seen:continue
            split = int(group[:8],16)/0xffffffff
            role = 'train' if split<.7 else 'validation' if split<.85 else 'test'
            prefs = {'sportiness':None,'angularity':None if rng.random()<.35 else rng.choice([0.,.5,1.]),
                     'acceleration':None if rng.random()<.35 else rng.choice([0.,.5,1.])}
            for name in ('design_importance','performance_importance','asset_retention_importance','running_cost_importance'):
                prefs[name] = rng.choice([1,3,5])
            user = {'id':accepted+number,'group':group,'profile':asdict(profile),'preferences':prefs,'split':role}
            pool = {}
            for index,car in enumerate(catalog):
                if seating_status(profile,car) != 'match':continue
                cost = assess(profile,car)
                if cost['eligible']:pool.setdefault((car.brand,car.model),[]).append((index,car,cost))
            if len(pool)<2:continue
            pair_count = min(10,math.comb(len(pool),2))
            candidates,required = select_candidates(pool,rng,model_counts[role],spec_counts,
                settings['model_minimum'][role],1,20,pair_count)
            features = [encode_ui_scenario(user,car,traits[car.id],cost) for _,car,cost in candidates]
            scores = [choice_utility(x) for x in features]
            pairs = list(itertools.combinations(range(len(candidates)),2));rng.shuffle(pairs)
            chosen,uncovered = [],set(required)
            while len(chosen)<pair_count:
                pair = next((pair for pair in pairs if uncovered.intersection(pair)),pairs[0])
                pairs.remove(pair);uncovered.difference_update(pair);chosen.append(pair)
            bucket = buckets[role];positions={}
            for index in sorted({i for pair in chosen for i in pair}):
                positions[index]=len(bucket['features']);bucket['features'].append(features[index])
                bucket['profile_ids'].append(user['id']);bucket['vehicle_indices'].append(candidates[index][0])
            for a,b in chosen:
                delta=max(-60,min(60,(scores[a]-scores[b])/.25));probability=1/(1+math.exp(-delta))
                draw=rng.random();label=int(draw<probability)
                bucket['comparisons'].append([positions[a],positions[b]]);bucket['labels'].append(label)
                bucket['choices'].append({'user_id':user['id'],'a':candidates[a][0],'b':candidates[b][0],
                    'label':label,'probability_a':probability,'draw':draw})
                for i in (a,b):model_counts[role][model_key(candidates[i][1])]+=1;spec_counts[candidates[i][1].id]+=1
            bucket['users'].append(user);seen.add(group);partitions[group]=role
            counts[role+'_profiles']+=1;counts[role+'_comparisons']+=len(chosen);number+=1
        directory=output/f'shard-{len(shards):04d}';directory.mkdir()
        for role,bucket in buckets.items():
            np.savez_compressed(directory/f'{role}_choices.npz',features=np.asarray(bucket['features'],dtype=np.float32).reshape(-1,len(FEATURE_NAMES)),
                comparisons=np.asarray(bucket['comparisons'],dtype=np.int64).reshape(-1,2),labels=np.asarray(bucket['labels'],dtype=np.float32),
                profile_ids=np.asarray(bucket['profile_ids'],dtype=np.int64),vehicle_indices=np.asarray(bucket['vehicle_indices'],dtype=np.int64))
            for suffix,rows in [('profiles',bucket['users']),('choices',bucket['choices'])]:
                (directory/f'{role}_{suffix}.jsonl').write_text(''.join(json.dumps(row,ensure_ascii=False)+'\n' for row in rows),encoding='utf-8')
        shards.append({'directory':directory.name});accepted+=number
        print(json.dumps({'profiles':accepted,'target':profiles}),flush=True)
    coverage=coverage_report(catalog,model_counts,spec_counts,settings['model_minimum'],1)
    write_json(output/'coverage_report.json',coverage)
    if coverage['status']!='passed':raise ValueError('Vehicle coverage failed')
    write_json(output/'manifest.json',{'version':VERSION,'feature_names':FEATURE_NAMES,'profiles':profiles,
        'comparisons':sum(counts[role+'_comparisons'] for role in model_counts),
        'partitions':{role:{'profiles':counts[role+'_profiles'],'comparisons':counts[role+'_comparisons']} for role in model_counts},
        'shards':shards,'files_sha256':{str(path.relative_to(output)):file_hash(path) for path in output.rglob('*') if path.is_file()},
        'source_sha256':{str(path.relative_to(ROOT)):file_hash(path) for path in (Path(__file__),ROOT/'ml/vehicle_matching/ui_scenario_features.py',SOURCE/'seed_personas.json',TRAITS)}})


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--output',type=Path,required=True);parser.add_argument('--profiles',type=int,default=10000)
    args=parser.parse_args();generate(args.output,args.profiles)
