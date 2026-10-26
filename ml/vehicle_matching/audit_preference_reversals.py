"""Decompose calibrated-ML reversals against the explicit-rule baseline."""
import argparse
import csv
import json
from collections import Counter
from dataclasses import asdict
from itertools import combinations
from pathlib import Path

import numpy as np

from vehicle_matching.api import load_service
from vehicle_matching.catalog import ROOT
from vehicle_matching.experiment_score_transforms import CachedScores, case_values
from vehicle_matching.finance import assess
from vehicle_matching.partition_preference_population import digest
from vehicle_matching.preferences import integrated_score
from vehicle_matching.score_transforms import transform_scores
from vehicle_matching.service import CandidateService
from vehicle_matching.train_preference_population import independent_eligible

EPSILON = 1e-8
PREFERENCES = ('fuel','space','seating')


def classify_reversal(deltas, losses):
    """Evidence categories for review, not a customer-satisfaction judgment."""
    explicit = {key:value for key,value in deltas.items() if key != 'model'}
    dominated = all(value <= EPSILON for value in explicit.values()) and any(value < -EPSILON for value in explicit.values())
    if dominated:
        return '명시평가항목상열세_ML로역전'
    if losses:
        if deltas.get('cost',0) > EPSILON:
            return '선호하락_비용평가이점있음_ML로역전'
        return '선호하락_비용평가이점없음_ML로역전'
    return '선호점수유지_비용등의규칙순위역전'


def ordered_models(cars, scores):
    seen = set(); result = []
    for i in sorted(range(len(cars)),key=lambda i:(-scores[i]['total'],cars[i].id)):
        key = (cars[i].brand,cars[i].model)
        if key not in seen:
            result.append(i); seen.add(key)
    return result


def decompose(first, second):
    a = {item['key']:item for item in first['components']}
    b = {item['key']:item for item in second['components']}
    assert a.keys() == b.keys()
    assert all(a[key]['weight']==b[key]['weight'] for key in a)
    deltas = {key:b[key]['contribution']-a[key]['contribution'] for key in a}
    losses = [{'condition':key,'weight':a[key]['weight'],'before_score':a[key]['score'],
               'after_score':b[key]['score'],'lost_full_match':a[key]['score']>=100-EPSILON and b[key]['score']<100-EPSILON,
               'specifications_verified':a[key].get('verified',True) and b[key].get('verified',True)}
              for key in PREFERENCES if key in a and b[key]['score'] < a[key]['score']-EPSILON]
    assert abs(sum(deltas.values())-(second['total']-first['total'])) < 1e-7
    return deltas,losses


def audit_case(service, record, calibration, cohort):
    profile,cars,raw,targets = case_values(service,record)
    values = transform_scores(raw,'calibrated_sigmoid',**calibration)
    costs = [assess(profile,car,service.ranker.assumptions) for car in cars]
    baseline = [integrated_score(profile,car,cost,.5) for car,cost in zip(cars,costs)]
    calibrated = [integrated_score(profile,car,cost,float(score)) for car,cost,score in zip(cars,costs,values)]
    before = ordered_models(cars,baseline); after = ordered_models(cars,calibrated)
    result = CandidateService(CachedScores(service.ranker,cars,values),service.vehicles).recommend(profile,k=9)
    assert [row['vehicle']['id'] for row in result['recommendations']]==[cars[i].id for i in after[:9]]
    for i in after[:9]:
        assert independent_eligible(profile,cars[i],costs[i])
    model_key = lambda i:(cars[i].brand,cars[i].model)
    before_models = [model_key(i) for i in before]; after_models = [model_key(i) for i in after]
    before_rank = {key:rank for rank,key in enumerate(before_models)}
    after_rank = {key:rank for rank,key in enumerate(after_models)}
    before_car = {model_key(i):i for i in before}; after_car = {model_key(i):i for i in after}
    raw_order = sorted(range(len(cars)),key=lambda i:(-float(raw[i]),cars[i].id))
    raw_rank = {index:rank+1 for rank,index in enumerate(raw_order)}
    base_record = {'cohort':cohort,'case_id':record['id'],'group':record['group'],'origin':record['origin']}
    case = {**base_record,'vehicle_id_top3_changed':[cars[i].id for i in before[:3]]!=[cars[i].id for i in after[:3]],
            'model_order_top3_changed':before_models[:3]!=after_models[:3],
            'model_members_top3_changed':set(before_models[:3])!=set(after_models[:3]),
            'before_top3':' / '.join(cars[i].model for i in before[:3]),
            'after_top3':' / '.join(cars[i].model for i in after[:3])}
    union = sorted(set(before_models[:3]+after_models[:3]))
    inversions = []
    for left,right in combinations(union,2):
        if (before_rank[left]-before_rank[right])*(after_rank[left]-after_rank[right]) >= 0:
            continue
        demoted,promoted = (left,right) if before_rank[left]<before_rank[right] else (right,left)
        a,b = before_car[demoted],after_car[promoted]
        deltas,losses = decompose(calibrated[a],calibrated[b])
        explicit_delta = sum(value for key,value in deltas.items() if key!='model')
        assert explicit_delta<=EPSILON and sum(deltas.values())>=-EPSILON
        full_loss = [loss for loss in losses if loss['lost_full_match']]
        high_loss = [loss for loss in full_loss if loss['weight']>=4]
        detail = {**base_record,'demoted_id':cars[a].id,'demoted_model':cars[a].model,'promoted_id':cars[b].id,
                  'promoted_model':cars[b].model,'before_demoted_rank':before_rank[demoted]+1,
                  'after_demoted_rank':after_rank[demoted]+1,'before_promoted_rank':before_rank[promoted]+1,
                  'after_promoted_rank':after_rank[promoted]+1,
                  'category':classify_reversal(deltas,losses),'preference_score_decreased':bool(losses),
                  'full_match_lost':bool(full_loss),'high_importance_full_match_lost':bool(high_loss),
                  'lost_conditions':'|'.join(loss['condition'] for loss in losses),
                  'full_match_lost_conditions':'|'.join(loss['condition'] for loss in full_loss),
                  'purchase_saving_won':int(cars[a].price-cars[b].price),
                  'monthly_running_saving_won':int(costs[a]['monthly_running_cost']-costs[b]['monthly_running_cost']),
                  'ml_original_demoted':float(raw[a]),'ml_original_promoted':float(raw[b]),
                  'ml_original_demoted_rank':raw_rank[a],'ml_original_promoted_rank':raw_rank[b],
                  'rule_utility_demoted':float(targets[a]),'rule_utility_promoted':float(targets[b]),
                  'rule_margin_100point':float(-explicit_delta),
                  'ml_advantage_100point':float(deltas['model']),
                  'final_margin_100point':float(sum(deltas.values())),
                  **{key+'_contribution_delta':float(deltas.get(key,0)) for key in ('cost','fuel','space','seating','model')},
                  'baseline_tie':abs(explicit_delta)<=EPSILON,
                  'new_personalization_evidence':False}
        purchase_change = (f"구매 가격 {detail['purchase_saving_won']:,}원 절감" if detail['purchase_saving_won']>=0
                           else f"구매 가격 {-detail['purchase_saving_won']:,}원 증가")
        running_change = (f"월 유지비 {detail['monthly_running_saving_won']:,}원 절감" if detail['monthly_running_saving_won']>=0
                          else f"월 유지비 {-detail['monthly_running_saving_won']:,}원 증가")
        detailed = {**detail,'profile':asdict(profile),'preference_losses':losses,
                    'demoted_vehicle':asdict(cars[a]),'promoted_vehicle':asdict(cars[b]),
                    'demoted_cost':costs[a],'promoted_cost':costs[b],
                    'demoted_score':calibrated[a],'promoted_score':calibrated[b],
                    'explanation':f"{cars[b].model} 선택 시 {purchase_change}, {running_change}입니다. "
                                  f"최종 100점 척도의 비ML 기여 합계는 {cars[a].model} 쪽이 {detail['rule_margin_100point']:.6f}점 높지만, ML 기여 차이 {detail['ml_advantage_100point']:.6f}점으로 순서가 바뀌었습니다. "
                                  '이 차이는 합성 규칙 근사의 결과이며 새로운 취향의 근거가 아닙니다.'}
        inversions.append((detail,detailed))
    case['reversal_pairs'] = len(inversions)
    case['preference_decrease_pairs'] = sum(pair[0]['preference_score_decreased'] for pair in inversions)
    case['full_match_lost_pairs'] = sum(pair[0]['full_match_lost'] for pair in inversions)
    case['high_importance_full_match_lost_pairs'] = sum(pair[0]['high_importance_full_match_lost'] for pair in inversions)
    return case,inversions


def write_csv(path, rows):
    with path.open('w',encoding='utf-8-sig',newline='') as stream:
        if rows:
            writer = csv.DictWriter(stream,fieldnames=list(rows[0]));writer.writeheader();writer.writerows(rows)


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--experiment',type=Path,default=ROOT/'ml/outputs/reports/score-transforms-20261026')
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args();args.output.mkdir(parents=True,exist_ok=False)
    previous=json.loads((args.experiment/'report.json').read_text(encoding='utf-8'))
    model_dir=Path(previous['model_dir'])
    service=load_service(model_dir)
    frozen={name:digest(model_dir/name) for name in ('model.pt','metadata.json','catalog.json')}
    assert frozen==previous['frozen_model_hashes']
    manifest=json.loads((args.experiment/'sample_manifest.json').read_text(encoding='utf-8'))
    calibration={key:previous['calibration'][key] for key in ('center','temperature')}
    source=ROOT/'data/households/synthetic/curated-current-v2-20261026/test_profiles.jsonl'
    assert digest(source)==previous['evaluation_profiles_sha256']
    wanted={row['id'] for cohort in ('primary','secondary') for row in manifest[cohort]}
    records={}
    with source.open(encoding='utf-8') as stream:
        for line in stream:
            row=json.loads(line)
            if row['id'] in wanted:records[row['id']]=row
    cases=[];pairs=[];details=[]
    for cohort in ('primary','secondary'):
        for number,row in enumerate(manifest[cohort]):
            case,inversions=audit_case(service,records[row['id']],calibration,cohort)
            cases.append(case);pairs.extend(pair for pair,detail in inversions);details.extend(detail for pair,detail in inversions)
            if (number+1)%100==0:print(json.dumps({'cohort':cohort,'completed':number+1}),flush=True)
    assert all(digest(model_dir/name)==value for name,value in frozen.items())
    assert digest(source)==previous['evaluation_profiles_sha256']
    report={'model_hashes':frozen,'baseline':'same explicit rule score with ML contribution constant at 0.5',
            'operational_policy_changed':False,'weights_changed':False,'deployed':False,
            'financial_violations':0,'score_decomposition_violations':0,
            'comparison_unit':'inverted distinct-model pairs within union of before/after top3; pairs may overlap within one case',
            'high_importance_definition':'weight >= 4; audit category only, not a filter',
            'review_note':'Economic advantage and lost preference are evidence; no automatic rationality or satisfaction verdict',
            'cohorts':{}}
    for cohort in ('primary','secondary','all'):
        selected=[row for row in cases if cohort=='all' or row['cohort']==cohort]
        selected_pairs=[row for row in pairs if cohort=='all' or row['cohort']==cohort]
        report['cohorts'][cohort]={
            'profiles':len(selected),
            **{field:sum(row[field] for row in selected) for field in ('vehicle_id_top3_changed','model_order_top3_changed','model_members_top3_changed')},
            'cases_with_preference_decrease':sum(row['preference_decrease_pairs']>0 for row in selected),
            'cases_with_full_match_lost':sum(row['full_match_lost_pairs']>0 for row in selected),
            'cases_with_high_importance_full_match_lost':sum(row['high_importance_full_match_lost_pairs']>0 for row in selected),
            'reversal_pairs':len(selected_pairs),'pair_categories':dict(Counter(row['category'] for row in selected_pairs)),
            'full_match_lost_by_condition':dict(Counter(condition for row in selected_pairs for condition in row['full_match_lost_conditions'].split('|') if condition)),
            'rule_margin_quantiles':np.quantile([row['rule_margin_100point'] for row in selected_pairs],[0,.5,.9,1]).tolist() if selected_pairs else []}
    write_csv(args.output/'cases.csv',cases);write_csv(args.output/'reversal_pairs.csv',pairs)
    (args.output/'details.json').write_text(json.dumps(details,ensure_ascii=False,indent=2),encoding='utf-8')
    (args.output/'report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(report['cohorts'],ensure_ascii=False,indent=2),flush=True)


if __name__=='__main__':main()
