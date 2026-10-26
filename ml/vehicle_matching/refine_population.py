"""Retain usable legacy inputs, rebuild current-policy comparisons, classify outputs."""
import argparse
import csv
import hashlib
import json
import math
import random
import shutil
import subprocess
from collections import Counter, defaultdict
from dataclasses import asdict
from decimal import Decimal
from pathlib import Path

import numpy as np

from vehicle_matching.catalog import ROOT, catalog_fingerprint
from vehicle_matching.finance import Profile, assess
from vehicle_matching.partition_preference_population import compact_pairs, digest
from vehicle_matching.preference_model import encode_preference
from vehicle_matching.train_preference_population import teacher, independent_eligible, fit_population, compare_models

SPLITS=('train','validation','test')
PRIORITY={'train':0,'validation':1,'test':2}
FUEL={'가솔린':'GASOLINE','휘발유':'GASOLINE','하이브리드':'HYBRID','디젤':'DIESEL','경유':'DIESEL','전기':'ELECTRIC','LPG':'LPG','상관없음':None}
SIZE={'작음':'small','중간':'medium','큼':'large','상관없음':'any','small':'small','medium':'medium','large':'large','any':'any'}
SPLIT_NAMES={'학습':'train','검증':'validation','평가':'test'}
FIELDS=['사례번호','재무그룹번호','데이터구분','입력출처','원본사례번호','월소득_원','월생활지출_원','기존월상환액_원',
        '구매유지예금_원','구매가격상한_원','선호연료','선호크기','최소탑승인원','가성비중요도','크기중요도','연료중요도',
        '인원중요도','연간주행거리_km','재무적격모델수','비교모델수','비교학습쌍수','선택차량번호','선택모델',
        '선택차량가격_원','월유지비_원','구매후예금_원','월예금소진액_원','선택확률_만분율','분류사유','기대최대추천대수']


def integer(value):
    number=Decimal(str(value))
    if not number.is_finite() or number<0 or number%1:raise ValueError('Non-negative integer required')
    return int(number)


def legacy_profile(row):
    income=integer(row['개인_평균월실수령소득_원'])
    cash=integer(row['개인_현금성자산_원'])
    funds=integer(row['구매투입가능자금_원'])
    # The legacy spendable amount already excludes protected funds. Do not
    # silently turn the protected reserve into spendable purchase cash.
    if funds>cash:raise ValueError('Spendable funds exceed assets')
    return Profile(monthly_income=income,monthly_expenses=integer(row['개인_평균월주거비_원'])+integer(row['개인_평균월기타생활소비_원']),
                   existing_monthly_payment=integer(row['기존월상환액_보정전_원']),liquid_assets=funds,
                   down_payment=0,emergency_reserve=0,monthly_savings=0,annual_distance=15000,months=0,annual_rate=0,
                   financing_mode='recommendation',purpose='commute',purpose_importance=1,
                   preferred_fuel=FUEL[row['선호연료']],preferred_size=SIZE[row['선호크기']],
                   minimum_seats=integer(row['최소탑승인원_명']),cost_importance=integer(row['가성비중요도_1부터5']),
                   space_importance=integer(row['공간중요도_1부터5']),fuel_importance=integer(row['연료중요도_1부터5']),
                   seating_importance=integer(row['탑승인원중요도_1부터5']),
                   purchase_price_ceiling=integer(row['구매가격상한_원_0이면미지정']))


def finance_key(profile):
    return tuple(getattr(profile,key) for key in ('monthly_income','monthly_expenses','existing_monthly_payment','liquid_assets','purchase_price_ceiling'))


def collect(source,legacy,coverage,provenance):
    records={};groups={};counts=Counter();rejections=Counter()
    excluded=set()
    with Path(coverage).open(encoding='utf-8-sig',newline='') as stream:
        excluded.update(row['프로필_식별자'] for row in csv.DictReader(stream))
    with Path(provenance).open(encoding='utf-8-sig',newline='') as stream:
        excluded.update(row['프로필_식별자'] for row in csv.DictReader(stream) if row['생성유형']=='차량별보강')
    def accept(profile,split,origin,original):
        values=asdict(profile);key=tuple(sorted(values.items()));financial=finance_key(profile)
        if financial not in groups or PRIORITY[split]>PRIORITY[groups[financial]]:groups[financial]=split
        if key in records:
            rejections[origin+':현재입력중복']+=1;return
        records[key]={'profile':values,'origin':origin,'original_id':original,'original_split':split}
    with Path(source).open(encoding='utf-8') as stream:
        for line in stream:
            row=json.loads(line);counts['new_source_rows']+=1
            accept(Profile(**row['profile']),row['split'],'신규10만행',f"N-{row['id']:06}")
    with Path(legacy).open(encoding='utf-8-sig',newline='') as stream:
        for row in csv.DictReader(stream):
            counts['legacy_source_rows']+=1
            if integer(row['월소득보정액_원'])>0:rejections['legacy:소득보정사례']+=1;continue
            if row['프로필_식별자'] in excluded:rejections['legacy:차량수량보강사례']+=1;continue
            try:profile=legacy_profile(row);split=SPLIT_NAMES[row['데이터_구분']]
            except (ValueError,KeyError,ArithmeticError):rejections['legacy:필수입력오류']+=1;continue
            accept(profile,split,'기존306429행',row['프로필_식별자'])
    for case,record in enumerate(records.values()):
        record['id']=case;record['split']=groups[finance_key(Profile(**record['profile']))]
        if record['split']!=record['original_split']:counts['stricter_split_reassignments']+=1
    return list(records.values()),dict(counts),dict(rejections)


def build(output,records,vehicles,held_models,seed,financial_cap=2000):
    output.mkdir(parents=True,exist_ok=False)
    x=[];y=[];pairs=[];row_ids=[];row_vehicles=[];row_splits=[];retained=[]
    groups=defaultdict(list)
    for record in records:groups[finance_key(Profile(**record['profile']))].append(record)
    counts=Counter();reasons=Counter();finance_saved=Counter();seen_finance={}
    reference=Profile(**records[0]['profile'])
    prices=np.asarray([car.price for car in vehicles],dtype=np.float64)
    running=np.asarray([assess(reference,car)['monthly_running_cost'] for car in vehicles])
    def evaluated(profile,items):
        result=[]
        for i,_ in items:
            cost=assess(profile,vehicles[i])
            if not cost['eligible'] or not independent_eligible(profile,vehicles[i],cost):
                raise AssertionError('Independent eligibility differs')
            result.append((i,cost))
        return result
    writers={};streams=[];json_streams={}
    try:
        for role,filename in (('train','training.csv'),('validation','validation.csv'),('test','evaluation.csv'),('financial','financial_validation.csv')):
            stream=(output/filename).open('w',encoding='utf-8-sig',newline='');streams.append(stream)
            writers[role]=csv.DictWriter(stream,fieldnames=FIELDS);writers[role].writeheader()
            stream=(output/f'{role}_profiles.jsonl').open('w',encoding='utf-8');streams.append(stream);json_streams[role]=stream
        for group_index,(financial,cases) in enumerate(groups.items()):
            base=Profile(**cases[0]['profile'])
            if (base.annual_distance,base.emergency_reserve,base.monthly_savings,base.minimum_buffer,base.financing_mode)!=(15000,0,0,0,'recommendation'):
                raise ValueError('Financial prefilter requires current normalized inputs')
            net=base.monthly_income-base.monthly_expenses-base.existing_monthly_payment
            remaining=base.liquid_assets-prices
            mask=(remaining>=0)&(remaining>=12*np.maximum(0,running-net))
            if base.purchase_price_ceiling:mask&=prices<=base.purchase_price_ceiling
            pool=[(int(i),None) for i in np.flatnonzero(mask)]
            all_keys={(vehicles[i].brand,vehicles[i].model) for i,c in pool}
            split=cases[0]['split'];assert all(record['split']==split for record in cases)
            seen_finance[financial]=split
            available=defaultdict(list)
            for i,cost in pool:
                car=vehicles[i]
                if split!='test' and (car.brand,car.model) in held_models:continue
                available[car.brand,car.model].append((i,cost))
            for record in cases:
                record['group']=group_index
                p=Profile(**record['profile'])
                rng=random.Random(seed+int(hashlib.sha256(json.dumps(record['profile'],sort_keys=True).encode()).hexdigest()[:12],16))
                sampled=evaluated(p,[rng.choice(available[key]) for key in rng.sample(sorted(available),min(16,len(available)))])
                scores=[teacher(p,vehicles[i],cost) for i,cost in sampled]
                possibilities=[(a,b) for a in range(len(sampled)) for b in range(a) if abs(scores[a]-scores[b])>=.01]
                chosen_pairs=rng.sample(possibilities,min(8,len(possibilities)))
                reason='비교가능' if chosen_pairs else '재무적격차량없음' if not all_keys else '재무적격모델1개' if len(all_keys)==1 else '분할정책상후보부족' if len(sampled)<2 else '후보점수차이부족'
                role=split if chosen_pairs else 'financial'
                if role=='financial':
                    reasons[reason]+=1
                    cap_key=(reason,split)
                    if finance_saved[cap_key]>=financial_cap:
                        counts['discarded_redundant_financial_cases']+=1;continue
                    finance_saved[cap_key]+=1
                else:
                    start=len(x)
                    for (i,cost),score in zip(sampled,scores):
                        x.append(encode_preference(p,vehicles[i],cost=cost));y.append(score)
                        row_ids.append(record['id']);row_vehicles.append(i);row_splits.append(PRIORITY[split])
                    for a,b in chosen_pairs:pairs.append((start+a,start+b) if scores[a]>scores[b] else (start+b,start+a))
                    retained.append(record)
                selection_pool=sampled or evaluated(p,pool)
                selected=None;probability=0
                if selection_pool:
                    utility=scores if sampled else [teacher(p,vehicles[i],cost) for i,cost in selection_pool]
                    probabilities=np.exp((np.asarray(utility)-max(utility))/.06);probabilities/=probabilities.sum()
                    choice=rng.choices(range(len(selection_pool)),weights=probabilities,k=1)[0]
                    i,cost=selection_pool[choice];selected=vehicles[i];probability=round(float(probabilities[choice])*10000)
                row=[f"C-{record['id']:07}",f'F-{group_index:07}',{'train':'학습','validation':'검증','test':'평가'}[split],record['origin'],record['original_id'],
                     p.monthly_income,p.monthly_expenses,p.existing_monthly_payment,p.liquid_assets,p.purchase_price_ceiling,p.preferred_fuel or '상관없음',
                     p.preferred_size,p.minimum_seats,p.cost_importance,p.space_importance,p.fuel_importance,p.seating_importance,15000,len(all_keys),len(sampled),len(chosen_pairs),
                     selected.id if selected else 'NO-CHOICE',selected.model if selected else '추천없음',selected.price if selected else 0,
                     cost['monthly_running_cost'] if selected else 0,p.liquid_assets-selected.price if selected else p.liquid_assets,
                     cost['monthly_asset_drawdown'] if selected else 0,probability,reason,min(9,len(all_keys))]
                writers[role].writerow({key:int(value) if key.endswith('_원') else value for key,value in zip(FIELDS,row)})
                json_streams[role].write(json.dumps(record,ensure_ascii=False)+'\n')
                counts[role]+=1;counts[role+':'+record['origin']]+=1
            if (group_index+1)%5000==0:print(json.dumps({'financial_groups_processed':group_index+1,'counts':dict(counts)}),flush=True)
    finally:
        for stream in streams:stream.close()
    arrays={'features':np.asarray(x,dtype=np.float32),'targets':np.asarray(y,dtype=np.float32),
            'pairs':np.asarray(pairs,dtype=np.int64).reshape(-1,2),'profile_ids':np.asarray(row_ids,dtype=np.int32),
            'vehicle_indices':np.asarray(row_vehicles,dtype=np.int16),'splits':np.asarray(row_splits,dtype=np.int8)}
    result={};parts=[]
    for code,role in enumerate(SPLITS):
        part=compact_pairs(arrays,code);np.savez_compressed(output/f'{role}_pairs.npz',**part)
        result[role]={'profiles':counts[role],'candidates':len(part['features']),'pairs':len(part['pairs'])};parts.append(part)
        assert len(np.unique(part['profile_ids']))==counts[role]
    offsets=np.cumsum([0]+[len(part['features']) for part in parts])
    combined={key:np.concatenate([part[key] for part in parts]) for key in ('features','targets','profile_ids','vehicle_indices','splits')}
    combined['pairs']=np.concatenate([part['pairs']+offsets[i] for i,part in enumerate(parts)])
    assert np.all(combined['profile_ids'][combined['pairs'][:,0]]==combined['profile_ids'][combined['pairs'][:,1]])
    return combined,retained,{'counts':dict(counts),'financial_reasons':dict(reasons),'comparison_partitions':result,'group_split_leakage':0}


def verify_saved(output,vehicles,report):
    ids=set();groups={};signatures=set();counts=Counter();cars={car.id:car for car in vehicles};cache={}
    held={tuple(key) for key in report.get('held_out_models',[])}
    for role,filename in (('train','training.csv'),('validation','validation.csv'),('test','evaluation.csv'),('financial','financial_validation.csv')):
        with (output/filename).open(encoding='utf-8-sig',newline='') as stream:
            for row in csv.DictReader(stream):
                assert row['사례번호'] not in ids;ids.add(row['사례번호'])
                assert groups.setdefault(row['재무그룹번호'],row['데이터구분'])==row['데이터구분']
                if role!='financial':assert int(row['비교학습쌍수'])>0 and row['선택차량번호']!='NO-CHOICE'
                counts[role]+=1
        with (output/f'{role}_profiles.jsonl').open(encoding='utf-8') as stream:
            for line in stream:
                record=json.loads(line);profile=Profile(**record['profile'])
                signature=json.dumps(record['profile'],sort_keys=True)
                assert signature not in signatures;signatures.add(signature)
                assert groups[f"F-{record['group']:07}"]=={'train':'학습','validation':'검증','test':'평가'}[record['split']]
        if role!='financial':
            with np.load(output/f'{role}_pairs.npz') as data:
                assert np.isfinite(data['features']).all()
                assert np.all(data['targets'][data['pairs'][:,0]]>data['targets'][data['pairs'][:,1]])
                assert np.all(data['profile_ids'][data['pairs'][:,0]]==data['profile_ids'][data['pairs'][:,1]])
                if role!='test':assert not any((vehicles[int(i)].brand,vehicles[int(i)].model) in held for i in np.unique(data['vehicle_indices']))
        with (output/filename).open(encoding='utf-8-sig',newline='') as rows, (output/f'{role}_profiles.jsonl').open(encoding='utf-8') as profiles:
            for row,line in zip(csv.DictReader(rows),profiles,strict=True):
                p=Profile(**json.loads(line)['profile']);vehicle_id=row['선택차량번호']
                if vehicle_id=='NO-CHOICE':continue
                car=cars[vehicle_id];key=(finance_key(p),car.id)
                if key not in cache:
                    cost=assess(p,car);cache[key]=cost['eligible'] and independent_eligible(p,car,cost)
                assert cache[key], 'Saved selected vehicle violates finances'
    assert all(counts[role]==report['counts'][role] for role in ('train','validation','test','financial'))
    return {'passed':True,'counts':dict(counts),'duplicate_case_ids':0,'duplicate_inputs':0,'split_leakage':0,'invalid_comparison_pairs':0,'selected_financial_violations':0,'held_model_leakage':0}


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--output',type=Path,required=True);parser.add_argument('--model-output',type=Path,required=True)
    parser.add_argument('--source-model',type=Path,required=True);parser.add_argument('--epochs',type=int,default=12);args=parser.parse_args()
    if subprocess.check_output(['git','branch','--show-current'],cwd=ROOT,text=True).strip()!='ml/test':raise ValueError('Run on ml/test only')
    if args.output.exists() or args.model_output.exists():raise ValueError('Choose unused output locations')
    root=ROOT/'data/households/synthetic'
    sources={'new':root/'preference-population-100k-20261026-v2/profiles.jsonl',
             'legacy':root/'preference-financial-v4/combined_training.csv',
             'coverage':root/'preference-quality-v2/supplement_training.csv',
             'provenance':root/'preference-quality-v3/additional_provenance.csv'}
    hashes={name:{'path':str(path),'sha256':digest(path)} for name,path in sources.items()}
    generation=json.loads((root/'preference-population-100k-20261026-v2/generation_report.json').read_text(encoding='utf-8'))
    from vehicle_matching.api import load_service
    service=load_service(args.source_model)
    records,source_counts,rejections=collect(**{name:str(path) for name,path in sources.items() if name!='new'},source=str(sources['new']))
    print(json.dumps({'unique_inputs':len(records),'source_counts':source_counts,'rejections':rejections},ensure_ascii=False),flush=True)
    arrays,retained,report=build(args.output,records,service.vehicles,{tuple(key) for key in generation['held_out_models']},20261026)
    shutil.copyfile(args.source_model/'catalog.json',args.output/'catalog.json')
    report.update({'source_counts':source_counts,'rejections':rejections,'source_hashes':hashes,'unique_valid_inputs':len(records),
                   'source_git_commit':subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),
                   'policy':'cash-preference-weighted-v9','seed':20261026,'held_out_models':generation['held_out_models']})
    validation=verify_saved(args.output,service.vehicles,report)
    (args.output/'validation_report.json').write_text(json.dumps(validation,ensure_ascii=False,indent=2),encoding='utf-8')
    provenance={'catalog_sha256':catalog_fingerprint(args.output/'catalog.json'),
                'data_dir':str(args.output.resolve()),'policy':report['policy'],'split_counts':report['comparison_partitions'],'seed':20261026}
    model,history=fit_population(arrays['features'],arrays['targets'],arrays['pairs'],arrays['splits'],20261026,args.epochs,args.model_output,provenance)
    shutil.copyfile(args.output/'catalog.json',args.model_output/'catalog.json')
    comparison=compare_models(model,service.ranker,retained,service.vehicles)
    report['training_history']=history;report['model_comparison']=comparison
    assert all(digest(sources[name])==value['sha256'] for name,value in hashes.items())
    report['output_hashes']={path.name:digest(path) for path in args.output.iterdir() if path.is_file()}
    (args.output/'refinement_report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    (args.model_output/'report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps({'partitions':report['comparison_partitions'],'comparison':comparison},ensure_ascii=False),flush=True)


if __name__=='__main__':main()
