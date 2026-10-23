"""Keep financial inputs and regenerate labels/top3 under financial-hard soft-preference policy."""
import csv
import hashlib
import json
import random
import shutil
import subprocess
from collections import Counter

import numpy as np

from tools.data.households.extend_training_preferences import ROOT, write_csv
from tools.data.households.complete_preference_choices import context_from_row
from tools.data.households.relabel_preference_choices import output_row
from tools.data.households.financial_choice_policy import FinancialChoicePolicy, WEIGHTS, FEATURES, PREFERENCES
from vehicle_matching.catalog import read_catalog

SOURCE=ROOT/'data/households/synthetic/preference-quality-v3'
OUTPUT=SOURCE.parent/'preference-financial-v4'
TOP_FIELDS=('프로필_식별자','추천순위','차량사양번호','차량라벨','브랜드','모델','트림','차량가격_원',
            '월할부금_원','월유지비_원','차량비용차감후월잔여액_원','가중점수_만점10000')


def build(seed=20261025):
    if subprocess.check_output(['git','branch','--show-current'],cwd=ROOT,text=True).strip()!='ml/test': raise ValueError('ml/test only')
    main=subprocess.check_output(['git','rev-parse','main'],cwd=ROOT,text=True).strip()
    path=SOURCE/'combined_training.csv'
    digest=hashlib.sha256(path.read_bytes()).hexdigest()
    policy=FinancialChoicePolicy(read_catalog(SOURCE/'catalog.json'))
    with (SOURCE/'vehicle_identity_map.csv').open(encoding='utf-8-sig',newline='') as f:
        labels={r['차량사양번호']:r['선택차량_라벨코드'] for r in csv.DictReader(f)}
    OUTPUT.mkdir(exist_ok=True)
    counts=Counter(); splits={s:Counter() for s in ('학습','검증','평가')}; examples=[]
    with path.open(encoding='utf-8-sig',newline='') as f, \
         (OUTPUT/'combined_training.csv').open('w',encoding='utf-8-sig',newline='') as dst, \
         (OUTPUT/'recommendations_top3.csv').open('w',encoding='utf-8-sig',newline='') as top, \
         (OUTPUT/'change_log.csv').open('w',encoding='utf-8-sig',newline='') as log:
        reader=csv.DictReader(f); fields=(*reader.fieldnames,*WEIGHTS,'추천정책버전')
        writer=csv.DictWriter(dst,fieldnames=fields); writer.writeheader()
        top_writer=csv.DictWriter(top,fieldnames=TOP_FIELDS); top_writer.writeheader()
        log_writer=csv.DictWriter(log,fieldnames=('프로필_식별자','보완전차량사양','보완후차량사양','변경이유')); log_writer.writeheader()
        for old in reader:
            identity=old['프로필_식별자'].rsplit('-R',1)[0]
            rng=random.Random(hashlib.sha256(f'{seed}:{identity}:weights'.encode()).hexdigest())
            row={**old,**{key:rng.randint(1,5) for key in WEIGHTS},'추천정책버전':'financial-hard-preferences-soft-v2'}
            context=context_from_row(row); pool,reason=policy.pool(row,context)
            if pool is None: raise AssertionError('Existing previously eligible finance unexpectedly invalid: '+reason)
            selected=policy.select(row,context,pool,seed)
            result=output_row(row,context,selected,labels)
            v=selected['vehicle']
            result.update({'선택차량연료':selected['semantic_fuel'],'선택설명':'재무절대조건통과_모든선호가중평가_전체후보확률선택',
                           '품질추가월여유_원':0,'선호우선단계':'모든선호상대평가','비교가능모델수':pool['eligible_models'],
                           '선택차량원본연료':v.original_fuel or v.fuel,'비용계산연료':v.fuel,
                           '전장참조출처':v.space_source_url or ('기존제원근거' if v.length_mm else '제원미확인_중립점수')})
            chosen=policy.top_three(pool)
            for rank,index in enumerate(chosen,1):
                vehicle=policy.vehicles[index]
                top_writer.writerow(dict(zip(TOP_FIELDS,(row['프로필_식별자'],rank,vehicle.id,labels[vehicle.id],vehicle.brand,
                    vehicle.model,vehicle.trim,round(vehicle.price),int(pool['payment'][index]),int(pool['running'][index]),
                    int(pool['remaining'][index]),round(pool['scores'][index]*10000)))))
            counts['rows']+=1; counts['top3_rows']+=len(chosen)
            counts['fewer_than_three']+=len(chosen)<3
            counts['changed_labels']+=old['선택차량사양번호']!=v.id
            splits[row['데이터_구분']][labels[v.id]]+=1
            writer.writerow(result)
            if old['선택차량사양번호']!=v.id:
                log_writer.writerow(dict(zip(log_writer.fieldnames,(row['프로필_식별자'],old['선택차량사양번호'],v.id,'선호배제규칙을가중상대평가로변경'))))
            if len(examples)<30: examples.append(result)
            if counts['rows']%50000==0: print(f'Rebuilt {counts["rows"]}',flush=True)
    for name in ('catalog.json','vehicle_identity_map.csv','length_evidence.json','additional_provenance.csv'):
        shutil.copyfile(SOURCE/name,OUTPUT/name)
    write_csv(OUTPUT/'examples.csv',fields,examples)
    assert hashlib.sha256(path.read_bytes()).hexdigest()==digest
    assert subprocess.check_output(['git','rev-parse','main'],cwd=ROOT,text=True).strip()==main
    unseen={s:sorted(set(splits[s])-set(splits['학습'])) for s in ('검증','평가')}
    report={'seed':seed,'source_sha256':digest,'counts':counts,'split_rows':{s:sum(c.values()) for s,c in splits.items()},
            'label_counts':splits,'unseen_labels':unseen,'input_and_main_unchanged':True,
            'weights':'Four weights independently generated 1..5 before vehicle selection; same repeated input shares weights',
            'selection':'All financially eligible models; softmax temperature .06; deterministic weighted top3 in separate CSV',
            'financial_rules':'60 months 6 percent, purchase funds/price ceiling/monthly savings/emergency reserve/minimum buffer. No extra implicit buffer.',
            'soft_rules':'Size, fuel, seats and purpose are scores; missing specs neutral .5; no preference tier, no score/probability cutoff.'}
    (OUTPUT/'generation_report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps({k:v for k,v in report.items() if k!='label_counts'},ensure_ascii=True,indent=2))


if __name__=='__main__': build()
