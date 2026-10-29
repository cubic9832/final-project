"""Expand authored personas into coherent, sharded, reproducible comparison data."""
import argparse
from collections import Counter, defaultdict
from contextlib import ExitStack
from dataclasses import asdict
from copy import deepcopy
import hashlib
from itertools import combinations
import json
import math
from pathlib import Path
import random

import numpy as np

from vehicle_matching.catalog import ROOT, read_catalog
from vehicle_matching.finance import Profile, assess
from vehicle_matching.recommendation_policy import seating_status
from vehicle_matching.scenario_features import (
    CHANNELS, FEATURE_NAMES, channel_values, encode_scenario, explain_choice, probability_a, utility,
)
from tools.data.households.scenario_coverage import coverage_report, model_key, select_candidates
from tools.data.vehicles.scenario_seating import apply_registry

HERE = Path(__file__).resolve().parent
DEFAULT_SEEDS = ROOT / 'data/households/synthetic/authored-pilot-v1-20261029'
DEFAULT_CONFIG = HERE / 'scenario_population_v3_config.json'
ROLES = ('train', 'validation', 'test')
FINANCIAL_FIELDS = ('monthly_income', 'monthly_expenses', 'existing_monthly_payment', 'monthly_savings',
                    'liquid_assets', 'emergency_reserve', 'minimum_buffer', 'purchase_price_ceiling')


def canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':'), allow_nan=False)


def file_hash(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def write_json(path, value):
    Path(path).write_text(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + '\n', encoding='utf-8')


def derived_seed(seed, name):
    return int(hashlib.sha256(f'{seed}:{name}'.encode()).hexdigest()[:16], 16)


def load_seeds(directory, catalog, additional_path=None):
    users = [json.loads(line) for line in (directory / 'profiles.jsonl').read_text(encoding='utf-8').splitlines()]
    choices = [json.loads(line) for line in (directory / 'choices.jsonl').read_text(encoding='utf-8').splitlines()]
    lookup = {v.id: v for v in catalog}
    affinities = defaultdict(dict)
    brands = defaultdict(set)
    for row in choices:
        winner, loser = (lookup[row['a']], lookup[row['b']]) if row['label'] else (lookup[row['b']], lookup[row['a']])
        affinities[row['profile_id']][winner.model] = 1.0
        affinities[row['profile_id']].setdefault(loser.model, .35)
        brands[row['profile_id']].add(winner.brand)
    if len(users) < 2 or len({u['id'] for u in users}) != len(users):
        raise ValueError('At least two distinct authored seeds required')
    for user in users:
        user['model_affinities'] = affinities[user['id']]
        user['preferred_brands'] = sorted(brands[user['id']])
    if additional_path:
        by_id = {u['id']:u for u in users}
        for row in json.loads(additional_path.read_text(encoding='utf-8'))['personas']:
            if row['id'] in by_id:
                raise ValueError('Duplicate additional persona ID')
            user = deepcopy(by_id[row['base_id']])
            user.update(id=row['id'],group=row['id'],name=row['name'],scenario=row['scenario'],
                        experience_priorities=row['priorities'],preferred_brands=row['preferred_brands'],
                        model_affinities=row['model_affinities'])
            user['profile'].update(row['profile'])
            user['profile']['cost_importance'] = row['priorities']['cost']
            user['profile']['space_importance'] = row['priorities']['space']
            Profile(**user['profile'])
            if set(user['model_affinities']) - {v.model for v in catalog}:
                raise ValueError('Additional persona references unknown model')
            users.append(user); by_id[user['id']] = user
    return users


def sample_user(primary, secondary, rng, config, number):
    p = dict(primary['profile'])
    # Joint financial scale preserves the seed's household structure, then adds small personal variation.
    scale = rng.lognormvariate(0, config['financial_log_sigma'])
    for field in FINANCIAL_FIELDS:
        if field != 'minimum_buffer':
            p[field] = round(p[field] * scale * rng.uniform(.92, 1.08) / 10000) * 10000
    p['minimum_buffer'] = config['minimum_buffer']
    p['emergency_reserve'] = min(p['emergency_reserve'], p['liquid_assets'])
    p['annual_distance'] = max(2000, min(50000, round(p['annual_distance'] * rng.lognormvariate(0, config['distance_log_sigma']) / 500) * 500))
    mix = rng.uniform(*config['secondary_mix_range'])
    for key in ('preferred_body_type', 'preferred_fuel', 'preferred_size'):
        if rng.random() < config['secondary_preference_probability']:
            p[key] = secondary['profile'][key]
    # Required seating and purpose come from the primary life context, never from a selected vehicle.
    p['charging_available'] = primary['profile']['charging_available'] if rng.random() < .9 else not primary['profile']['charging_available']
    priorities = {key: max(1, min(5, round((1-mix)*value + mix*secondary['experience_priorities'][key] + rng.gauss(0, .45))))
                  for key, value in primary['experience_priorities'].items()}
    p['cost_importance'], p['space_importance'] = priorities['cost'], priorities['space']
    for key in ('body_importance', 'fuel_importance'):
        p[key] = max(1, min(5, p[key] + rng.choice((-1, 0, 0, 1))))
    profile = Profile(**p)
    models = set(primary['model_affinities']) | set(secondary['model_affinities'])
    affinities = {name: round((1-mix)*primary['model_affinities'].get(name, .5)
                              + mix*secondary['model_affinities'].get(name, .5), 4) for name in sorted(models)}
    brand_source = secondary if rng.random() < mix else primary
    # Observable importance is the only coefficient vector used by the choice policy.
    cost_weight = priorities['cost'] / 5
    distance_weight = min(1.5, max(.4, p['annual_distance'] / 15000))
    weights = [cost_weight, cost_weight * distance_weight, p['body_importance']/5,
               p['fuel_importance']/5, priorities['space']/5,
               (priorities['brand']-1)/4, priorities['design']/5,
               .15 if p['charging_available'] else .7]
    if not config.get('identity_preferences',True):
        affinities = {}
        weights[5:7] = [0.,0.]
    group = hashlib.sha256(canonical({k:p[k] for k in FINANCIAL_FIELDS}).encode()).hexdigest()
    user = {'id': number, 'group':group, 'profile':asdict(profile), 'experience_priorities':priorities,
            'preferred_brands':brand_source['preferred_brands'] if config.get('identity_preferences',True) else [], 'model_affinities':affinities,
            'channel_weights':weights}
    user['scenario'] = (f'{p["purpose"]} 중심, 연 {p["annual_distance"]:,}km, 필수 {p["minimum_seats"]}석. '
                        f'안정적 충전 접근 {"가능" if p["charging_available"] else "없음"}. '
                        f'선호 {p["preferred_body_type"]}/{p["preferred_fuel"]}/{p["preferred_size"]}. '
                        f'비용 중요도 {priorities["cost"]}, 디자인 중요도 {priorities["design"]}.')
    audit = {'primary_seed':primary['id'], 'secondary_seed':secondary['id'], 'secondary_mix':mix}
    return user, profile, audit


def eligible_candidates(profile, catalog):
    result = defaultdict(list)
    for index, vehicle in enumerate(catalog):
        if seating_status(profile, vehicle) != 'match':
            continue
        cost = assess(profile, vehicle)
        if cost['eligible']:
            result[vehicle.brand, vehicle.model].append((index, vehicle, cost))
    return result


def choose_pairs(candidates, user, rng, count, modes, required_indices=()):
    values = [channel_values(user, v, cost) for _, v, cost in candidates]
    scores = [utility(v, user['channel_weights']) for v in values]
    pairs = list(combinations(range(len(candidates)), 2))
    if len(pairs) < count:
        return None
    # Different comparison types, without forcing a winner or repeating a pair.
    used, result = set(), []
    uncovered = set(required_indices)
    if len(uncovered)>2*count or not uncovered.issubset(range(len(candidates))):
        raise ValueError('Comparison capacity cannot cover required candidates')
    for position in range(count):
        mode = modes[position % len(modes)]
        available = [pair for pair in pairs if pair not in used]
        if uncovered:
            first_required = min(uncovered)
            other_required = uncovered-{first_required}
            pool = [pair for pair in available if first_required in pair and
                    (not other_required or any(i in other_required for i in pair))]
            mode = 'coverage'
        elif mode == 'near':
            available.sort(key=lambda pair: abs(scores[pair[0]] - scores[pair[1]]))
            pool = available[:max(1, len(available)//5)]
        elif mode == 'tradeoff':
            pool = [pair for pair in available if np.any(values[pair[0]]-values[pair[1]] > .1)
                    and np.any(values[pair[0]]-values[pair[1]] < -.1)] or available
        elif mode == 'similar':
            pool = [pair for pair in available if candidates[pair[0]][1].body_type == candidates[pair[1]][1].body_type
                    and abs(math.log(candidates[pair[0]][1].price/candidates[pair[1]][1].price)) < .25] or available
        else:
            pool = available
        first, second = rng.choice(pool)
        used.add((first, second))
        uncovered.difference_update((first,second))
        if rng.random() < .5:
            first, second = second, first
        result.append((first, second, mode))
    return result, values, scores


def validate_config(config):
    if config['version'] not in ('scenario-population-v1','scenario-population-v2','scenario-population-v3'):
        raise ValueError('Unsupported configuration version')
    for key in ('financial_log_sigma', 'distance_log_sigma'):
        if not math.isfinite(config[key]) or not 0 <= config[key] <= 2:
            raise ValueError(f'Invalid {key}')
    for key in ('secondary_mix_range', 'temperature_range'):
        low, high = config[key]
        if not 0 < low <= high < 1:
            raise ValueError(f'Invalid {key}')
    if not 0 <= config['secondary_preference_probability'] <= 1:
        raise ValueError('Invalid preference probability')
    if len(config['split_fractions']) != 3 or any(v <= 0 for v in config['split_fractions']) or not math.isclose(sum(config['split_fractions']), 1):
        raise ValueError('Invalid split fractions')
    if type(config['pool_models']) is not int or config['pool_models'] < 2:
        raise ValueError('At least two pool models required')
    if not config['pair_modes'] or set(config['pair_modes']) - {'random','near','tradeoff','similar'}:
        raise ValueError('Invalid pair modes')
    if not math.isfinite(config['minimum_buffer']) or config['minimum_buffer'] < 0:
        raise ValueError('Invalid monthly buffer')
    for role,value in config.get('minimum_model_comparisons',{}).items():
        if role not in ROLES or type(value) is not int or value<0:
            raise ValueError('Invalid model coverage minimum')
    if type(config.get('minimum_spec_comparisons',0)) is not int or config.get('minimum_spec_comparisons',0)<0:
        raise ValueError('Invalid specification coverage minimum')


def generate(output, *, profiles=10000, pairs_per_user=10, shard_size=1000, seed=20261029,
             seeds_dir=DEFAULT_SEEDS, config_path=DEFAULT_CONFIG):
    if min(profiles, pairs_per_user, shard_size) < 1:
        raise ValueError('Positive profile, pair and shard counts required')
    config = json.loads(Path(config_path).read_text(encoding='utf-8'))
    validate_config(config)
    if pairs_per_user > math.comb(config['pool_models'], 2):
        raise ValueError('Too many pairs for pool_models')
    catalog_path = seeds_dir / 'catalog.json'
    catalog = read_catalog(catalog_path)
    registry_path = ROOT/config['seating_registry'] if config.get('seating_registry') else None
    additional_path = ROOT/config['additional_personas'] if config.get('additional_personas') else None
    supplements = None
    if registry_path:
        catalog,supplements = apply_registry(catalog,registry_path)
    seeds = load_seeds(seeds_dir, catalog, additional_path)
    model_minima = config.get('minimum_model_comparisons',{})
    spec_minimum = config.get('minimum_spec_comparisons',0)
    if sum(model_minima.values())*len({model_key(v) for v in catalog}) > profiles*pairs_per_user*2:
        raise ValueError('Requested population cannot meet model coverage minima')
    output = Path(output)
    output.mkdir(parents=True, exist_ok=False)
    write_json(output/'configuration.json', {**config,'profiles':profiles,'pairs_per_user':pairs_per_user,
               'shard_size':shard_size,'seed':seed})
    write_json(output/'catalog.json', [asdict(v) for v in catalog])
    if supplements:
        write_json(output/'seating_supplements.json',supplements)
    write_json(output/'seed_personas.json',seeds)
    write_json(output/'feature_schema.json', {'version':config['version'],'features':FEATURE_NAMES,'channels':CHANNELS,
               'inactive_experience_priorities':['performance','ride_comfort','quietness','technology'],
               'input_exclusions':['label','reason','utility_a','utility_b','probability_a','draw','temperature','primary_seed','secondary_seed']})
    # Independent streams prevent candidate sampling from changing future user identities.
    user_rng = random.Random(derived_seed(seed,'users'))
    candidate_rng = random.Random(derived_seed(seed,'candidates'))
    choice_rng = random.Random(derived_seed(seed,'choices'))
    split_seed = derived_seed(seed,'split')
    groups, signatures = set(), set()
    accepted = attempts = 0
    counts, rejected, exposures, wins, seed_counts, modes, labels = (Counter() for _ in range(7))
    model_counts = {role:Counter() for role in ROLES}
    spec_counts = Counter()
    distributions = {k:Counter() for k in ('body','fuel','purpose','charging','minimum_seats','annual_distance_band')}
    shards, preview = [], []
    while accepted < profiles:
        shard = output / f'shard-{len(shards):04}'
        shard.mkdir()
        buckets = {role:{'features':[],'comparisons':[],'labels':[],'profile_ids':[],'vehicle_indices':[]} for role in ROLES}
        shard_profiles = Counter()
        with ExitStack() as stack:
            streams = {role:{name:stack.enter_context((shard/f'{role}_{name}.jsonl').open('w',encoding='utf-8'))
                            for name in ('profiles','choices','audit')} for role in ROLES}
            while sum(shard_profiles.values()) < min(shard_size, profiles-accepted):
                if attempts >= profiles*50:
                    raise ValueError('Too many rejected profiles; inspect financial/seat distribution or pair count')
                primary, secondary = user_rng.sample(seeds,2)
                user, profile, authoring = sample_user(primary,secondary,user_rng,config,accepted+sum(shard_profiles.values()))
                attempts += 1
                signature = hashlib.sha256(canonical({k:user[k] for k in ('profile','experience_priorities','preferred_brands','model_affinities')}).encode()).hexdigest()
                if user['group'] in groups or signature in signatures:
                    rejected['duplicate_financial_group_or_profile'] += 1
                    continue
                pool = eligible_candidates(profile,catalog)
                if math.comb(min(len(pool),config['pool_models']),2) < pairs_per_user:
                    rejected['insufficient_eligible_models'] += 1
                    continue
                fraction = derived_seed(split_seed,user['group']) / 2**64
                role = 'train' if fraction < config['split_fractions'][0] else 'validation' if fraction < sum(config['split_fractions'][:2]) else 'test'
                if model_minima or spec_minimum:
                    candidates,required = select_candidates(pool,candidate_rng,model_counts[role],spec_counts,
                        model_minima.get(role,0),spec_minimum,config['pool_models'],pairs_per_user)
                else:
                    families = candidate_rng.sample(sorted(pool),min(len(pool),config['pool_models']))
                    candidates = [candidate_rng.choice(pool[family]) for family in families]
                    required = []
                pairs, values, scores = choose_pairs(candidates,user,candidate_rng,pairs_per_user,config['pair_modes'],required)
                user['split'] = role
                groups.add(user['group']); signatures.add(signature)
                streams[role]['profiles'].write(canonical(user)+'\n')
                bucket = buckets[role]
                positions = {}
                for i in sorted({i for a,b,_ in pairs for i in (a,b)}):
                    index, vehicle, cost = candidates[i]
                    positions[i] = len(bucket['features'])
                    bucket['features'].append(encode_scenario(user,profile,vehicle,cost))
                    bucket['profile_ids'].append(user['id']); bucket['vehicle_indices'].append(index)
                temperature = choice_rng.uniform(*config['temperature_range'])
                sample_choices = []
                for position,(a,b,mode) in enumerate(pairs):
                    va, vb = candidates[a][1], candidates[b][1]
                    probability = probability_a(scores[a],scores[b],temperature)
                    draw = choice_rng.random(); label = int(draw < probability)
                    reason = explain_choice(va,vb,values[a],values[b],user['channel_weights'],label)
                    row = {'id':f'{user["id"]}:{position}','profile_id':user['id'],'a':va.id,'b':vb.id,
                           'label':label,'sampling_mode':mode,'reason':reason}
                    streams[role]['choices'].write(canonical(row)+'\n')
                    streams[role]['audit'].write(canonical({'choice_id':row['id'],**authoring,'temperature':temperature,
                        'utility_a':scores[a],'utility_b':scores[b],'probability_a':probability,'draw':draw})+'\n')
                    bucket['comparisons'].append((positions[a],positions[b])); bucket['labels'].append(label)
                    exposures.update((va.model,vb.model)); wins.update((va.model if label else vb.model,))
                    model_counts[role].update((model_key(va),model_key(vb)))
                    spec_counts.update((va.id,vb.id))
                    modes.update((mode,)); labels.update((str(label),)); counts[role+'_choices'] += 1
                    sample_choices.append({'a':va.model,'b':vb.model,'label':label,'reason':reason})
                if len(preview) < 20:
                    preview.append({'user':user,'choices':sample_choices})
                seed_counts.update((primary['id'],))
                p = user['profile']
                for key,value in [('body',p['preferred_body_type']),('fuel',p['preferred_fuel']),('purpose',p['purpose']),
                                  ('charging',str(p['charging_available'])),('minimum_seats',str(p['minimum_seats'])),
                                  ('annual_distance_band',str(p['annual_distance']//5000*5000))]:
                    distributions[key].update((value,))
                shard_profiles[role] += 1; counts[role+'_profiles'] += 1
        for role,bucket in buckets.items():
            features = np.asarray(bucket['features'],dtype=np.float32).reshape(-1,len(FEATURE_NAMES))
            if not np.isfinite(features).all():
                raise ValueError('Nonfinite training inputs')
            np.savez_compressed(shard/f'{role}_choices.npz',features=features,
                comparisons=np.asarray(bucket['comparisons'],dtype=np.int64).reshape(-1,2),
                labels=np.asarray(bucket['labels'],dtype=np.float32),profile_ids=np.asarray(bucket['profile_ids'],dtype=np.int64),
                vehicle_indices=np.asarray(bucket['vehicle_indices'],dtype=np.int64))
        files = {p.name:file_hash(p) for p in sorted(shard.iterdir())}
        write_json(shard/'generation_report.json',{'profiles':dict(shard_profiles),'files_sha256':files})
        shards.append({'directory':shard.name,'report_sha256':file_hash(shard/'generation_report.json')})
        accepted += sum(shard_profiles.values())
        print(json.dumps({'profiles':accepted,'target':profiles,'shard':shard.name}),flush=True)
    write_json(output/'preview.json',preview)
    write_json(output/'generation_summary.json',{'profiles':accepted,'comparisons':sum(labels.values()),'attempts':attempts,
        'rejections':dict(rejected),'partitions':dict(counts),'labels':dict(labels),'primary_seeds':dict(seed_counts),
        'pair_modes':dict(modes),'distributions':{k:dict(v) for k,v in distributions.items()},
        'exposure_by_model':dict(exposures),'wins_by_model':dict(wins)})
    coverage = coverage_report(catalog,model_counts,spec_counts,model_minima,spec_minimum)
    write_json(output/'coverage_report.json',coverage)
    if coverage['status']!='passed':
        raise ValueError('Coverage requirements not met; see coverage_report.json. No completed manifest was written.')
    input_paths = [seeds_dir/'profiles.jsonl',seeds_dir/'choices.jsonl',catalog_path,Path(config_path),Path(__file__),
                   ROOT/'ml/vehicle_matching/scenario_features.py',ROOT/'ml/vehicle_matching/finance.py',
                   ROOT/'ml/vehicle_matching/preference_model.py',ROOT/'ml/vehicle_matching/recommendation_policy.py',
                   HERE/'scenario_coverage.py',ROOT/'tools/data/vehicles/scenario_seating.py']
    input_paths += [p for p in (registry_path,additional_path) if p]
    write_json(output/'manifest.json',{'version':config['version'],'profiles':profiles,'comparisons':profiles*pairs_per_user,
               'partitions':{r:{'profiles':counts[r+'_profiles'],'comparisons':counts[r+'_choices']} for r in ROLES},
               'feature_names':FEATURE_NAMES,'catalog_sha256':file_hash(output/'catalog.json'),'shards':shards,
               'source_hashes':{str(p.relative_to(ROOT)) if p.is_relative_to(ROOT) else str(p):file_hash(p) for p in input_paths}})
    return output


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--profiles',type=int,default=10000)
    parser.add_argument('--pairs-per-user',type=int,default=10)
    parser.add_argument('--shard-size',type=int,default=1000)
    parser.add_argument('--seed',type=int,default=20261029)
    parser.add_argument('--seeds-dir',type=Path,default=DEFAULT_SEEDS)
    parser.add_argument('--config',type=Path,default=DEFAULT_CONFIG)
    args = parser.parse_args()
    generate(args.output,profiles=args.profiles,pairs_per_user=args.pairs_per_user,shard_size=args.shard_size,
             seed=args.seed,seeds_dir=args.seeds_dir,config_path=args.config)


if __name__ == '__main__':
    main()
