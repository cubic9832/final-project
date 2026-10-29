"""Compare score transforms using fixed weights and disjoint calibration/evaluation."""
import argparse
import csv
import json
import math
import random
from collections import Counter, defaultdict
from dataclasses import asdict
from pathlib import Path

import numpy as np

from vehicle_matching.api import load_service
from vehicle_matching.catalog import ROOT
from vehicle_matching.finance import Profile, assess
from vehicle_matching.partition_preference_population import digest
from vehicle_matching.score_transforms import fit_sigmoid, transform_scores
from vehicle_matching.service import CandidateService
from vehicle_matching.train_preference_population import independent_eligible, teacher

METHODS = ('legacy_sigmoid','minmax','calibrated_sigmoid','softmax')


def select_samples(data_dir):
    origins = defaultdict(list)
    records = []
    with (data_dir/'test_profiles.jsonl').open(encoding='utf-8') as stream:
        for line in stream:
            row = json.loads(line)
            origins[row['origin']].append(row)
            records.append(row)
    # Exactly reproduce the previously reported balanced 300-case sample.
    rng = random.Random(20261026)
    used = set()
    core = []
    for origin, rows in sorted(origins.items()):
        rng.shuffle(rows)
        selected = 0
        for row in rows:
            if row['group'] in used:
                continue
            core.append(row); used.add(row['group']); selected += 1
            if selected == 150:
                break
    # Exclude the earlier first-300-groups evaluation as well.
    historical = set()
    for row in records:
        historical.add(row['group'])
        if len(historical) == 300:
            break
    used.update(historical)
    cohorts = {'primary':core}
    rng = random.Random(20261027)
    for cohort in ('calibration','secondary'):
        selected_rows = []
        for origin, rows in sorted(origins.items()):
            shuffled = list(rows); rng.shuffle(shuffled)
            selected = 0
            for row in shuffled:
                if row['group'] in used:
                    continue
                selected_rows.append(row); used.add(row['group']); selected += 1
                if selected == 150:
                    break
            if selected != 150:
                raise ValueError('Insufficient independent groups')
        cohorts[cohort] = selected_rows
    groups = {name:{r['group'] for r in rows} for name, rows in cohorts.items()}
    assert not (groups['primary'] & groups['calibration'] or groups['primary'] & groups['secondary'] or groups['calibration'] & groups['secondary'])
    return cohorts


def case_values(service, record):
    profile = Profile(**record['profile'])
    eligible = [(v,assess(profile,v,service.ranker.assumptions)) for v in service.vehicles]
    eligible = [(v,c) for v,c in eligible if c['eligible']]
    cars = [v for v,c in eligible]
    raw = np.asarray(service.ranker.ranking_scores(profile,cars))
    targets = np.asarray([teacher(profile,v,c) for v,c in eligible])
    return profile, cars, raw, targets


def distinct_order(cars, scores):
    order = []; seen = set()
    for i in sorted(range(len(cars)), key=lambda i:(-float(scores[i]),cars[i].id)):
        key = (cars[i].brand,cars[i].model)
        if key not in seen:
            order.append(i); seen.add(key)
        if len(order) == 3:
            break
    return order


def ndcg(order, targets, ideal):
    dcg = lambda indices: sum((2**targets[i]-1)/math.log2(j+2) for j,i in enumerate(indices))
    denominator = dcg(ideal)
    return dcg(order)/denominator if denominator else 1.0


class CachedScores:
    def __init__(self, model, cars, scores):
        self.assumptions = model.assumptions
        self.scores = {v.id:float(s) for v,s in zip(cars,scores)}

    def predict(self, profile, cars):
        return [self.scores[v.id] for v in cars], [False]*len(cars)


def evaluate(service, records, calibration, cohort, output):
    measurements = defaultdict(lambda:defaultdict(list))
    examples = []; per_case = []; score_rows = []
    params = {key:calibration[key] for key in ('center','temperature')}
    for number, record in enumerate(records):
        profile,cars,raw,targets = case_values(service,record)
        ideal = distinct_order(cars,targets)
        by_id = {car.id:i for i,car in enumerate(cars)}
        scores = {method:transform_scores(raw,method,**params) for method in (*METHODS,'neutral')}
        results = {}
        for method, values in scores.items():
            adapted = CandidateService(CachedScores(service.ranker,cars,values),service.vehicles)
            result = adapted.recommend(profile,k=9)['recommendations']
            expected = min(9,len({(v.brand,v.model) for v in cars}))
            assert len(result) == expected
            for row in result:
                assert independent_eligible(profile,cars[by_id[row['vehicle']['id']]],row['cost'])
            results[method] = result
        ids = lambda result:[row['vehicle']['id'] for row in result[:3]]
        legacy_ids = ids(results['legacy_sigmoid']); neutral_ids = ids(results['neutral'])
        for method in METHODS:
            values = scores[method]; chosen_ids = ids(results[method]); chosen = [by_id[i] for i in chosen_ids]
            ml_order = distinct_order(cars,values)
            # Remove the lowest raw-scoring candidate outside all top-three lists.
            protected = {by_id[i] for i in chosen_ids+legacy_ids+neutral_ids}
            removable = [i for i in np.argsort(raw) if i not in protected]
            sensitivity = 0.0
            if removable:
                removed = int(removable[0]); keep = np.arange(len(raw)) != removed
                changed = transform_scores(raw[keep],method,**params)
                sensitivity = float(np.max(np.abs(changed-values[keep])))
            metrics = {'candidate_fraction_exact_zero_or_one':float(np.mean((values==0)|(values==1))),
                       'candidate_fraction_near_endpoint_1e6':float(np.mean((values<=1e-6)|(values>=1-1e-6))),
                       'ml_top3_tie':float(len(set(float(values[i]) for i in ml_order))<len(ml_order)),
                       'top3_changed_from_legacy':float(chosen_ids!=legacy_ids),
                       'top3_members_changed_from_legacy':float(set(chosen_ids)!=set(legacy_ids)),
                       'top3_changed_from_neutral_ml':float(chosen_ids!=neutral_ids),
                       'final_rule_ndcg3':float(ndcg(chosen,targets,ideal)),
                       'ml_ndcg3':float(ndcg(ml_order,targets,ideal)),
                       'max_score_shift_removing_low_candidate':sensitivity,
                       'raw_final_score_spread':float(np.ptp(values))}
            if len(targets)>=2:
                top_targets=sorted(targets,reverse=True)
                metrics['top_candidate_rule_gap']=float(top_targets[0]-top_targets[1])
            for origin in ('all',record['origin']):
                for key,value in metrics.items():
                    measurements[method+'|'+origin][key].append(value)
            per_case.append({'cohort':cohort,'case_id':record['id'],'group':record['group'],
                             'origin':record['origin'],'method':method,**metrics,
                             'top3_ids':'|'.join(chosen_ids)})
            # Save distributions without presenting softmax as purchase probabilities.
            for i,value in enumerate(values):
                score_rows.append({'case_id':record['id'],'method':method,'vehicle_id':cars[i].id,'raw':float(raw[i]),'score':float(value)})
            if method!='legacy_sigmoid' and chosen_ids!=legacy_ids and sum(e['method']==method and e['origin']==record['origin'] for e in examples)<2:
                vehicles=[]
                for vehicle_id in dict.fromkeys(legacy_ids+chosen_ids):
                    i=by_id[vehicle_id];car=cars[i]
                    current=next((r for r in results[method] if r['vehicle']['id']==vehicle_id),None)
                    previous=next((r for r in results['legacy_sigmoid'] if r['vehicle']['id']==vehicle_id),None)
                    vehicles.append({'id':vehicle_id,'brand':car.brand,'model':car.model,'trim':car.trim,
                                     'price':car.price,'fuel':car.fuel,'seats':car.seats,'length_mm':car.length_mm,
                                     'raw':float(raw[i]),'old_ml_score':float(scores['legacy_sigmoid'][i]),'new_ml_score':float(values[i]),
                                     'rule_utility':float(targets[i]),'previous_rank':legacy_ids.index(vehicle_id)+1 if vehicle_id in legacy_ids else None,
                                     'new_rank':chosen_ids.index(vehicle_id)+1 if vehicle_id in chosen_ids else None,
                                     'new_integrated':current['integratedScore'] if current else None,
                                     'old_integrated':previous['integratedScore'] if previous else None,
                                     'financially_eligible':True})
                examples.append({'cohort':cohort,'case_id':record['id'],'origin':record['origin'],'method':method,
                                 'profile':asdict(profile),'vehicles':vehicles})
        if (number+1)%100 == 0:
            print(json.dumps({'cohort':cohort,'completed':number+1}),flush=True)
    for name,rows in [('cases',per_case),('scores',score_rows)]:
        with (output/f'{cohort}_{name}.csv').open('w',encoding='utf-8-sig',newline='') as stream:
            writer=csv.DictWriter(stream,fieldnames=list(rows[0]));writer.writeheader();writer.writerows(rows)
    summary = {}
    for group,metrics in measurements.items():
        summary[group] = {key:float(np.mean(values)) for key,values in metrics.items()}
        summary[group]['profiles'] = len(metrics['final_rule_ndcg3'])
        method,origin=group.split('|')
        distribution=np.asarray([row['score'] for row in score_rows if row['method']==method])
        if origin=='all':
            summary[group]['score_quantiles'] = np.quantile(distribution,[0,.01,.25,.5,.75,.99,1]).tolist()
    return {'metrics':summary,'financial_violations':0,'recommendation_count_violations':0},examples


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--data-dir',type=Path,default=ROOT/'data/households/synthetic/curated-current-v2-20261026')
    parser.add_argument('--model-dir',type=Path,default=ROOT/'ml/outputs/models/candidate-preferences/20261026-refined-v1')
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    args.output.mkdir(parents=True,exist_ok=False)
    frozen={name:digest(args.model_dir/name) for name in ('model.pt','metadata.json','catalog.json')}
    data_frozen={path.name:digest(path) for path in args.data_dir.glob('*_pairs.npz')}
    service=load_service(args.model_dir);cohorts=select_samples(args.data_dir)
    manifest={name:[{'id':r['id'],'group':r['group'],'origin':r['origin']} for r in rows] for name,rows in cohorts.items()}
    (args.output/'sample_manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')
    raw=[];targets=[];weights=[]
    for record in cohorts['calibration']:
        p,cars,z,y=case_values(service,record)
        raw.extend(z);targets.extend(y);weights.extend([1/len(z)]*len(z))
    calibration=fit_sigmoid(raw,targets,weights)
    calibration.update({'profiles':300,'candidate_rows':len(raw),'partition':'reserved test financial groups, excluded from both evaluation cohorts',
                        'not_used_for_weights_or_epoch_selection':True,'not_real_world_probability':True,
                        'softmax_temperature':'same fixed calibrated sigmoid T; not tuned for softmax'})
    (args.output/'calibration.json').write_text(json.dumps(calibration,ensure_ascii=False,indent=2),encoding='utf-8')
    report={'model_dir':str(args.model_dir),'frozen_model_hashes':frozen,'frozen_array_hashes':data_frozen,
            'weights_changed':False,'data_changed':False,'deployed':False,'ml_weight':1,'calibration':calibration,
            'sample_overlap':0,'metrics_meaning':'agreement with current rule utility; not customer satisfaction',
            'endpoint_note':'Min-max deliberately maps endpoints to 0/1; endpoint rate alone is not lost discrimination',
            'previously_used_test_groups_excluded_from_calibration_and_secondary':True}
    examples=[]
    for cohort in ('primary','secondary'):
        report[cohort],changed=evaluate(service,cohorts[cohort],calibration,cohort,args.output)
        examples.extend(changed)
    assert all(digest(args.model_dir/name)==value for name,value in frozen.items())
    assert all(digest(args.data_dir/name)==value for name,value in data_frozen.items())
    (args.output/'changed_examples.json').write_text(json.dumps(examples,ensure_ascii=False,indent=2),encoding='utf-8')
    (args.output/'report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps({cohort:{method:report[cohort]['metrics'][method+'|all'] for method in METHODS} for cohort in ('primary','secondary')},ensure_ascii=False),flush=True)


if __name__ == '__main__':
    main()
