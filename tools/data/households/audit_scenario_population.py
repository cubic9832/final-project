"""Read saved shards and independently check finance, identity, labels and feature alignment."""
import argparse
import hashlib
from collections import Counter
from decimal import Decimal
import json
import math
from pathlib import Path

import numpy as np

from vehicle_matching.catalog import read_catalog
from vehicle_matching.finance import Profile, assess
from vehicle_matching.recommendation_policy import seating_status
from vehicle_matching.scenario_features import CHANNELS, FEATURE_NAMES, encode_scenario, probability_a, utility
from tools.data.households.generate_scenario_population import FINANCIAL_FIELDS, canonical, file_hash, write_json
from tools.data.households.scenario_coverage import coverage_report, model_key


def require(condition, message):
    if not condition:
        raise ValueError(message)


def read_jsonl(path):
    with path.open(encoding='utf-8') as stream:
        return [json.loads(line) for line in stream]


def audit(directory):
    directory = Path(directory)
    manifest = json.loads((directory/'manifest.json').read_text(encoding='utf-8'))
    catalog_path = directory/'catalog.json'
    require(file_hash(catalog_path)==manifest['catalog_sha256'],'Catalog checksum mismatch')
    require(manifest['feature_names']==list(FEATURE_NAMES),'Feature contract mismatch')
    catalog = read_catalog(catalog_path)
    seen_groups, seen_users, seen_choices, signatures = set(), set(), set(), set()
    counts = Counter()
    config = json.loads((directory/'configuration.json').read_text(encoding='utf-8'))
    model_counts = {role:Counter() for role in ('train','validation','test')}
    spec_counts = Counter()
    for shard in manifest['shards']:
        path = directory/shard['directory']
        require(file_hash(path/'generation_report.json')==shard['report_sha256'],'Shard report checksum mismatch')
        report = json.loads((path/'generation_report.json').read_text(encoding='utf-8'))
        for filename, digest in report['files_sha256'].items():
            require(file_hash(path/filename)==digest,f'Checksum mismatch: {filename}')
        for role in ('train','validation','test'):
            records = read_jsonl(path/f'{role}_profiles.jsonl')
            users = {u['id']:u for u in records}
            require(len(users)==len(records),'Duplicate user in shard')
            for user in records:
                if config.get('identity_preferences') is False:
                    require(not user['preferred_brands'] and not user['model_affinities'] and
                            user['channel_weights'][5:7]==[0.,0.],'Identity preferences found in broad-taste dataset')
                require(user['split']==role,'Wrong user split')
                require(user['id'] not in seen_users and user['group'] not in seen_groups,'User/financial group leakage')
                # Recompute financial identity instead of trusting the stored group string.
                group = hashlib.sha256(canonical({k:user['profile'][k] for k in FINANCIAL_FIELDS}).encode()).hexdigest()
                require(group==user['group'],'Wrong financial group identity')
                signature = hashlib.sha256(canonical({k:user[k] for k in ('profile','experience_priorities','preferred_brands','model_affinities')}).encode()).hexdigest()
                require(signature not in signatures,'Duplicate user signature')
                seen_users.add(user['id']); seen_groups.add(group); signatures.add(signature)
            choices = read_jsonl(path/f'{role}_choices.jsonl')
            audit_rows = read_jsonl(path/f'{role}_audit.jsonl')
            with np.load(path/f'{role}_choices.npz',allow_pickle=False) as arrays:
                x, pairs, labels = arrays['features'],arrays['comparisons'],arrays['labels']
                ids, indices = arrays['profile_ids'],arrays['vehicle_indices']
            require(x.shape==(len(ids),len(FEATURE_NAMES)) and np.isfinite(x).all(),'Invalid feature array')
            require(len(choices)==len(pairs)==len(labels)==len(audit_rows),'Choice array length mismatch')
            require(pairs.shape==(len(choices),2),'Invalid pair array')
            require(not len(pairs) or (pairs.min()>=0 and pairs.max()<len(x)),'Invalid comparison index')
            require(not len(indices) or (indices.min()>=0 and indices.max()<len(catalog)),'Invalid vehicle index')
            usage = Counter()
            seen_pairs = set()
            # Rebuild every stored candidate from inference-visible user + catalog data.
            for position,(user_id,car_index) in enumerate(zip(ids,indices)):
                require(int(user_id) in users,'Unknown user referenced by feature row')
                user = users[int(user_id)]; profile = Profile(**user['profile']); vehicle = catalog[int(car_index)]
                cost = assess(profile,vehicle)
                require(cost['eligible'] and seating_status(profile,vehicle)=='match','Ineligible candidate')
                d = lambda value: Decimal(str(value))
                funds = d(profile.liquid_assets)-d(profile.emergency_reserve)-d(vehicle.price)
                available = d(profile.monthly_income)-d(profile.monthly_expenses)-d(profile.existing_monthly_payment)-d(profile.monthly_savings)
                deficit = max(Decimal(0),d(cost['monthly_running_cost'])+d(profile.minimum_buffer)-available)
                require(funds>=deficit*12 and funds>=0,'Independent cash/runway check failed')
                require(not profile.purchase_price_ceiling or vehicle.price<=profile.purchase_price_ceiling,'Price ceiling violated')
                expected = encode_scenario(user,profile,vehicle,cost)
                require(np.array_equal(expected,x[position]),'Features differ from inference encoding')
                counts['candidate_checks'] += 1
            for position,(row,record,(a,b),label) in enumerate(zip(choices,audit_rows,pairs,labels)):
                require(row['id'] not in seen_choices,'Duplicate choice ID')
                seen_choices.add(row['id'])
                require(row['id']==record['choice_id'],'Audit record misalignment')
                require(int(ids[a])==row['profile_id']==int(ids[b]),'Cross-user comparison')
                va,vb = catalog[int(indices[a])],catalog[int(indices[b])]
                require(va.id==row['a'] and vb.id==row['b'],'Vehicle identity mismatch')
                require((va.brand,va.model)!=(vb.brand,vb.model),'Same-model comparison')
                pair_key = (row['profile_id'],*sorted((va.id,vb.id)))
                require(pair_key not in seen_pairs,'Duplicate user comparison pair')
                seen_pairs.add(pair_key)
                weights = users[row['profile_id']]['channel_weights']
                start = len(FEATURE_NAMES)-2*len(CHANNELS)
                ua,ub = utility(x[a,start:start+len(CHANNELS)],weights),utility(x[b,start:start+len(CHANNELS)],weights)
                require(math.isclose(ua,record['utility_a'],abs_tol=1e-7) and math.isclose(ub,record['utility_b'],abs_tol=1e-7),'Utility audit mismatch')
                probability = probability_a(ua,ub,record['temperature'])
                require(math.isclose(probability,record['probability_a'],abs_tol=1e-7),'Probability audit mismatch')
                require(0<=record['draw']<1,'Invalid choice draw')
                require(row['label']==int(label)==int(record['draw']<record['probability_a']),'Choice label mismatch')
                require(bool(row['reason']),'Missing choice reason')
                model_counts[role].update((model_key(va),model_key(vb)))
                spec_counts.update((va.id,vb.id))
                usage[row['profile_id']] += 1
            require(set(usage)==set(users),'Profile with no choice')
            require(all(n==config['pairs_per_user'] for n in usage.values()),'Wrong choices per user')
            counts[role+'_profiles'] += len(users); counts[role+'_choices'] += len(choices)
    require(len(seen_users)==manifest['profiles'],'Total profile count mismatch')
    require(len(seen_choices)==manifest['comparisons'],'Total comparison count mismatch')
    for role, values in manifest['partitions'].items():
        require(counts[role+'_profiles']==values['profiles'] and counts[role+'_choices']==values['comparisons'],'Partition count mismatch')
    coverage = coverage_report(catalog,model_counts,spec_counts,config.get('minimum_model_comparisons',{}),
                               config.get('minimum_spec_comparisons',0))
    require(coverage['status']=='passed','Saved data does not meet coverage minima')
    if (directory/'coverage_report.json').exists():
        require(coverage==json.loads((directory/'coverage_report.json').read_text(encoding='utf-8')),'Saved coverage report mismatch')
    result = {'status':'passed','profiles':len(seen_users),'comparisons':len(seen_choices),
              'duplicate_users':0,'financial_group_leakage':0,'financial_violations':0,'seating_violations':0,
              'feature_mismatches':0,'label_mismatches':0,'counts':dict(counts),
              'models_by_split':{role:sum(n>0 for n in counter.values()) for role,counter in model_counts.items()},
              'catalog_models':coverage['catalog_models'],'used_specifications':len(spec_counts),
              'catalog_specifications':len(catalog),'coverage_status':coverage['status']}
    write_json(directory/'validation_report.json',result)
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--data',type=Path,required=True)
    args = parser.parse_args()
    print(json.dumps(audit(args.data),ensure_ascii=False),flush=True)


if __name__=='__main__':
    main()
