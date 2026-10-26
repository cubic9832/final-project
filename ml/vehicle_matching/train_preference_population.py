"""Generate 100k independent preference-first cases and train pairwise candidates.

Run from ml: python -m vehicle_matching.train_preference_population --data-dir ... --output ...
"""
import argparse
import csv
import hashlib
import json
import math
import random
import subprocess
from collections import Counter, defaultdict
from dataclasses import asdict
from decimal import Decimal
from pathlib import Path

import numpy as np
import torch
from torch import nn

from vehicle_matching.catalog import ROOT, FUELS, read_catalog, save_catalog, catalog_fingerprint
from vehicle_matching.finance import Profile, Assumptions, assess
from vehicle_matching.model import PairRanker
from vehicle_matching.preference_model import PreferenceRanker, encode_preference, preference_network
from vehicle_matching.preferences import integrated_score
from vehicle_matching.service import CandidateService


def teacher(profile, vehicle, cost):
    components = [item for item in integrated_score(profile, vehicle, cost, .5)['components'] if item['key'] != 'model']
    return sum(item['score']*item['weight'] for item in components)/sum(item['weight'] for item in components)/100


def independent_eligible(profile, vehicle, cost):
    d = lambda value: Decimal(str(value))
    cash = d(profile.liquid_assets)-d(profile.emergency_reserve)-d(vehicle.price)
    available = d(profile.monthly_income)-d(profile.monthly_expenses)-d(profile.existing_monthly_payment)-d(profile.monthly_savings)
    shortage = max(Decimal(0), d(cost['monthly_running_cost'])+d(profile.minimum_buffer)-available)
    return cash >= 0 and cash >= shortage*12 and (not profile.purchase_price_ceiling or vehicle.price <= profile.purchase_price_ceiling)


def financial_group(rng, group):
    # Profile inputs are generated without consulting or choosing a vehicle.
    income = round(min(60000000, max(1500000, rng.lognormvariate(math.log(5500000), .65)))/1000)*1000
    segment = group % 10
    expense_ratio = rng.uniform(1.0, 1.35) if segment == 0 else rng.uniform(.35, .85)
    expenses = round(income*expense_ratio/1000)*1000
    payment = round(income*rng.uniform(0, .18)/1000)*1000 if rng.random() < .6 else 0
    if segment == 1:
        expenses = income-payment  # exact zero monthly capacity, independently of cars
    cash = round(math.exp(rng.uniform(math.log(1000000), math.log(1000000000))))
    return dict(monthly_income=income, monthly_expenses=expenses, existing_monthly_payment=payment,
                liquid_assets=cash, down_payment=0, emergency_reserve=0, monthly_savings=0,
                annual_distance=15000, months=0, annual_rate=0, minimum_buffer=0,
                financing_mode='recommendation', purpose='commute', purpose_importance=1)


def generate(directory, vehicles, seed, count=100000):
    if count % 4:
        raise ValueError('Count must contain whole four-preference financial groups')
    directory.mkdir(parents=True, exist_ok=False)
    rng = random.Random(seed)
    keys = sorted({(v.brand, v.model) for v in vehicles})
    unseen = {key for i, key in enumerate(keys) if i % 5 == 0}
    groups = list(range(count//4))
    rng.shuffle(groups)
    splits = {group: 'train' if i < len(groups)*.7 else 'validation' if i < len(groups)*.85 else 'test' for i, group in enumerate(groups)}
    features, targets, row_profiles, row_vehicles, row_splits, pairs = [], [], [], [], [], []
    audits = Counter()
    signatures = set()
    records = []
    fields = ['사례번호', '재무그룹번호', '데이터구분', '월소득_원', '월생활지출_원', '기존월상환액_원',
              '구매유지예금_원', '선호연료', '선호크기', '최소탑승인원', '가성비중요도', '크기중요도',
              '연료중요도', '인원중요도', '연간주행거리_km', '전체재무적격사양수', '비교모델수', '선택차량번호',
              '선택브랜드', '선택모델', '선택트림', '선택차량가격_원', '월유지비_원', '월예금소진액_원',
              '구매후예금_원', '예상유지기간_개월', '선택확률_만분율', '생성규칙버전']
    with (directory/'profiles.csv').open('w', newline='', encoding='utf-8-sig') as stream:
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        for group in range(count//4):
            financial = financial_group(rng, group)
            base = Profile(**financial)
            eligible = [(i, assess(base, vehicle)) for i, vehicle in enumerate(vehicles)]
            for index, cost in eligible:
                if cost['eligible'] != independent_eligible(base, vehicles[index], cost):
                    raise AssertionError('Independent Decimal eligibility disagrees')
            eligible = [(i, cost) for i, cost in eligible if cost['eligible']]
            split = splits[group]
            pool = defaultdict(list)
            for index, cost in eligible:
                v = vehicles[index]
                if split != 'test' and (v.brand, v.model) in unseen:
                    continue
                pool[v.brand, v.model].append((index, cost))
            for pref in range(4):
                while True:
                    values = dict(financial, preferred_fuel=rng.choice((*FUELS, None)), preferred_size=rng.choice(('any','small','medium','large')),
                                  minimum_seats=rng.choice((0,2,4,5,6,7,9)), cost_importance=rng.choice((1,3,5)),
                                  space_importance=rng.choice((1,3,5)), fuel_importance=rng.choice((1,3,5)), seating_importance=rng.choice((1,3,5)))
                    signature = tuple(sorted(values.items()))
                    if signature not in signatures:
                        break
                profile = Profile(**values)
                signatures.add(signature)
                sampled = [rng.choice(pool[key]) for key in rng.sample(sorted(pool), min(16, len(pool)))]
                case_id = len(records)
                start = len(features)
                utilities = []
                for index, cost in sampled:
                    utility = teacher(profile, vehicles[index], cost)
                    features.append(encode_preference(profile, vehicles[index], cost=cost))
                    targets.append(utility)
                    row_profiles.append(case_id)
                    row_vehicles.append(index)
                    row_splits.append({'train':0,'validation':1,'test':2}[split])
                    utilities.append(utility)
                # Positive vs negative pairs always belong to the same user case.
                candidate_pairs = [(a,b) for a in range(len(sampled)) for b in range(a) if abs(utilities[a]-utilities[b]) >= .01]
                for a,b in rng.sample(candidate_pairs, min(8, len(candidate_pairs))):
                    pairs.append((start+a,start+b) if utilities[a] > utilities[b] else (start+b,start+a))
                chosen = None
                probability = 0
                selection_pool = sampled or eligible
                if selection_pool:
                    selection_utilities = utilities if sampled else [teacher(profile,vehicles[index],cost) for index,cost in selection_pool]
                    probabilities = np.exp((np.asarray(selection_utilities)-max(selection_utilities))/.06)
                    probabilities /= probabilities.sum()
                    chosen = rng.choices(range(len(selection_pool)), weights=probabilities, k=1)[0]
                    probability = round(float(probabilities[chosen])*10000)
                    index, cost = selection_pool[chosen]
                    vehicle = vehicles[index]
                    if not independent_eligible(profile, vehicle, cost):
                        raise AssertionError('Selected vehicle violates financial limits')
                    audits['asset_supported_cases' if cost['funding_source']=='assets' else 'income_supported_cases'] += 1
                else:
                    audits['no_choice_cases'] += 1
                row = [f'N-{case_id:06}', f'G-{group:06}', {'train':'학습','validation':'검증','test':'평가'}[split],
                       profile.monthly_income, profile.monthly_expenses, profile.existing_monthly_payment, profile.liquid_assets,
                       profile.preferred_fuel or '상관없음', profile.preferred_size, profile.minimum_seats, profile.cost_importance,
                       profile.space_importance, profile.fuel_importance, profile.seating_importance,15000,len(eligible),len(sampled)]
                if chosen is not None:
                    row += [vehicle.id,vehicle.brand,vehicle.model,vehicle.trim,int(vehicle.price),int(cost['monthly_running_cost']),
                            int(cost['monthly_asset_drawdown']),int(profile.liquid_assets-vehicle.price),
                            cost['asset_runway_months'] if cost['asset_runway_months'] is not None else '월소득으로충당',probability,'preference-population-v1']
                else:
                    row += ['NO-CHOICE','해당없음','추천없음','해당없음',0,0,0,profile.liquid_assets,'해당없음',0,'preference-population-v1']
                writer.writerow(dict(zip(fields,row)))
                records.append({'id':case_id,'group':group,'split':split,'profile':asdict(profile)})
                audits[split+'_profiles'] += 1
            if (group+1) % 1000 == 0:
                print(json.dumps({'generated_profiles':len(records),'candidate_rows':len(features)}), flush=True)
    x = np.asarray(features,dtype=np.float32)
    y = np.asarray(targets,dtype=np.float32)
    pairs = np.asarray(pairs,dtype=np.int64).reshape(-1,2)
    split_array = np.asarray(row_splits,dtype=np.int8)
    np.savez_compressed(directory/'candidate_pairs.npz',features=x,targets=y,pairs=pairs,
                        profile_ids=np.asarray(row_profiles,dtype=np.int32), vehicle_indices=np.asarray(row_vehicles,dtype=np.int16), splits=split_array)
    with (directory/'profiles.jsonl').open('w',encoding='utf-8') as stream:
        for record in records:
            stream.write(json.dumps(record,ensure_ascii=False)+'\n')
    save_catalog(directory/'catalog.json',vehicles)
    summary = {'version':'preference-population-v1','seed':seed,'profiles':len(records),'financial_groups':count//4,
               'candidate_rows':len(x),'preference_pairs':len(pairs),'counts':dict(audits),
               'held_out_models':[list(key) for key in sorted(unseen)],'violations':0,'duplicate_inputs':0,
               'split_unit':'financial_group','candidate_models_per_case':16,'selection_temperature':.06,
               'coverage_rule':'no forced vehicle balancing; one sampled configuration per distinct model',
               'teacher':'current cost/fuel/size/seating weighted score excluding ML; purpose not evaluated',
               'inputs':'independently generated first; no legacy row copying or financial repair',
               'profiles_sha256':hashlib.sha256((directory/'profiles.csv').read_bytes()).hexdigest(),
               'arrays_sha256':hashlib.sha256((directory/'candidate_pairs.npz').read_bytes()).hexdigest()}
    (directory/'generation_report.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2),encoding='utf-8')
    return x,y,pairs,split_array,records,summary


def fit_population(x,y,pairs,splits,seed,epochs,output,provenance):
    torch.manual_seed(seed)
    torch.set_num_threads(2)
    train_rows = splits == 0
    mean, scale = x[train_rows].mean(axis=0), x[train_rows].std(axis=0)
    scale[scale < 1e-6] = 1
    xt = torch.from_numpy(((x-mean)/scale).astype(np.float32))
    yt = torch.from_numpy(y)
    training = torch.from_numpy(pairs[splits[pairs[:,0]] == 0])
    validation = torch.from_numpy(pairs[splits[pairs[:,0]] == 1][:50000])
    net = preference_network()
    optimizer = torch.optim.Adam(net.parameters(), lr=.001)
    generator = torch.Generator().manual_seed(seed)
    best, history = -math.inf, []
    for epoch in range(epochs):
        net.train()
        total_loss=0
        for batch in torch.randperm(len(training),generator=generator).split(2048):
            a,b = training[batch].T
            pos,neg = net(xt[a]).flatten(),net(xt[b]).flatten()
            loss = nn.functional.softplus(-(pos-neg)).mean()+.5*((pos.sigmoid()-yt[a]).square().mean()+(neg.sigmoid()-yt[b]).square().mean())
            optimizer.zero_grad();loss.backward();optimizer.step()
            total_loss += loss.item()*len(batch)
        net.eval()
        with torch.no_grad():
            a,b=validation.T
            pos,neg=net(xt[a]).flatten(),net(xt[b]).flatten()
            accuracy=float((pos>neg).float().mean())
            mae=float((torch.cat((pos.sigmoid(),neg.sigmoid()))-torch.cat((yt[a],yt[b]))).abs().mean())
        history.append({'epoch':epoch+1,'loss':total_loss/len(training),'validation_pair_accuracy':accuracy,'validation_mae':mae})
        print(json.dumps(history[-1]),flush=True)
        if accuracy > best:
            best=accuracy
            ranker=PreferenceRanker(net,mean,scale,x[train_rows].min(axis=0),x[train_rows].max(axis=0))
            ranker.save(output,{**provenance,'selected_epoch':epoch+1,'validation_pair_accuracy':accuracy})
    return PreferenceRanker.load(output),history


def compare_models(new,old,records,vehicles,limit=300):
    results = {name:defaultdict(list) for name in ('new','old')}
    audit = Counter()
    groups=set()
    profiles=[]
    for record in records:
        if record['split']=='test' and record['group'] not in groups:
            profiles.append(Profile(**record['profile']));groups.add(record['group'])
        if len(profiles)==limit:break
    for profile in profiles:
        eligible=[(v,assess(profile,v)) for v in vehicles]
        eligible=[(v,c) for v,c in eligible if c['eligible']]
        if not eligible:
            audit['no_candidate_profiles']+=1;continue
        cars=[v for v,c in eligible]
        targets=[teacher(profile,v,c) for v,c in eligible]
        def distinct_order(scores):
            order=[];seen=set()
            for i in sorted(range(len(cars)),key=lambda i:(-scores[i],cars[i].id)):
                key=(cars[i].brand,cars[i].model)
                if key not in seen:order.append(i);seen.add(key)
                if len(order)==3:break
            return order
        ideal=distinct_order(targets)
        def dcg(order):return sum((2**targets[i]-1)/math.log2(j+2) for j,i in enumerate(order))
        denominator=dcg(ideal)
        for name,model in (('new',new),('old',old)):
            scores=model.ranking_scores(profile,cars) if hasattr(model,'ranking_scores') else model.predict(profile,cars)[0]
            order=distinct_order(scores)
            results[name]['standalone_ndcg_at_3'].append(dcg(order)/denominator if denominator else 1)
            rec=CandidateService(model,vehicles).recommend(profile,k=9)['recommendations']
            for row in rec:
                vehicle=next(v for v in vehicles if v.id==row['vehicle']['id'])
                if not independent_eligible(profile,vehicle,row['cost']):raise AssertionError('Service financial violation')
            by_id={v.id:i for i,v in enumerate(cars)}
            final_order=[by_id[row['vehicle']['id']] for row in rec[:3]]
            results[name]['final_ndcg_at_3'].append(dcg(final_order)/denominator if denominator else 1)
            results[name]['fuel_match_at_3'].extend([float(cars[i].fuel==profile.preferred_fuel) for i in final_order] if profile.preferred_fuel else [])
            audit[name+'_recommendations_checked']+=len(rec)
    return {'evaluation_profiles':len(profiles),'financial_violations':0,'audit':dict(audit),
            'metrics':{name:{key:float(np.mean(values)) if values else None for key,values in stats.items()} for name,stats in results.items()},
            'meaning':'Agreement with current synthetic teacher, not consumer satisfaction; test never used for epoch selection'}


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--data-dir',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--source-model',type=Path,required=True)
    parser.add_argument('--seed',type=int,default=20261026)
    parser.add_argument('--count',type=int,default=100000)
    parser.add_argument('--epochs',type=int,default=12)
    args=parser.parse_args()
    if subprocess.check_output(['git','branch','--show-current'],cwd=ROOT,text=True).strip()!='ml/test':raise ValueError('Run on ml/test only')
    if args.output.exists():raise ValueError('Model output already exists')
    from vehicle_matching.api import load_service
    source=load_service(args.source_model)
    x,y,pairs,splits,records,summary=generate(args.data_dir,source.vehicles,args.seed,args.count)
    provenance={'seed':args.seed,'data_dir':str(args.data_dir.resolve()),'source_model':str(args.source_model.resolve()),
                'profiles':len(records),'candidate_rows':len(x),'preference_pairs':len(pairs),
                'profiles_sha256':summary['profiles_sha256'],'target':'current explicit preference teacher, excluding ML',
                'catalog_sha256':catalog_fingerprint(args.data_dir/'catalog.json')}
    model,history=fit_population(x,y,pairs,splits,args.seed,args.epochs,args.output,provenance)
    save_catalog(args.output/'catalog.json',source.vehicles)
    report={'generation':summary,'history':history,'comparison':compare_models(model,source.ranker,records,source.vehicles)}
    (args.output/'report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(report['comparison']),flush=True)


if __name__=='__main__':main()
