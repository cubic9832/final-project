"""Independently audit finance, source preservation and exact weighted top3."""
import csv
import hashlib
import json
from collections import Counter

import numpy as np

from tools.data.households.rebuild_financial_choices import SOURCE,OUTPUT
from tools.data.households.financial_choice_policy import FinancialChoicePolicy,WEIGHTS,FEATURES,PREFERENCES,FUEL_LABELS
from tools.data.households.audit_complete_choices import independent_cost
from tools.data.households.complete_preference_choices import context_from_row
from tools.data.households.build_quality_training import holdout
from vehicle_matching.catalog import read_catalog
from vehicle_matching.finance import Profile,assess
from vehicle_matching.preferences import integrated_score


def audit():
    path=OUTPUT/'combined_training.csv'; digest=hashlib.sha256(path.read_bytes()).hexdigest()
    policy=FinancialChoicePolicy(read_catalog(OUTPUT/'catalog.json'))
    by_id={v.id:v for v in policy.vehicles}
    with (OUTPUT/'vehicle_identity_map.csv').open(encoding='utf-8-sig',newline='') as f:
        labels={r['차량사양번호']:r['선택차량_라벨코드'] for r in csv.DictReader(f)}
    counts=Counter(); groups={}; inputs={}; ids=set()
    context_fields=('월저축액_원','비상자금_원','구매투입가능자금_원','최소월여유자금_원','구매가격상한_원_0이면미지정')
    with path.open(encoding='utf-8-sig',newline='') as current, \
         (SOURCE/'combined_training.csv').open(encoding='utf-8-sig',newline='') as previous, \
         (OUTPUT/'recommendations_top3.csv').open(encoding='utf-8-sig',newline='') as candidates:
        old=csv.DictReader(previous); top=csv.DictReader(candidates)
        for row in csv.DictReader(current):
            baseline=next(old)
            identity=row['프로필_식별자']; split=row['데이터_구분']
            assert identity==baseline['프로필_식별자'] and identity not in ids
            ids.add(identity)
            assert all(row[k]==baseline[k] for k in (*FEATURES,*PREFERENCES,*context_fields,'데이터_구분','재무조건그룹번호'))
            assert all(value not in ('',None) for value in row.values())
            assert all(1<=int(row[k])<=5 for k in WEIGHTS)
            context=context_from_row(row); pool,reason=policy.pool(row,context)
            assert pool is not None,reason
            expected=policy.top_three(pool)
            assert len(expected)==min(3,pool['eligible_models'])
            v=by_id[row['선택차량사양번호']]
            assert labels[v.id]==row['선택차량_라벨코드'] and v.model==row['선택차량_모델'] and v.trim==row['선택트림']
            upfront,payment,running=independent_cost(row,v)
            remaining=int(row[FEATURES[0]])-int(row[FEATURES[2]])-int(row[FEATURES[3]])-int(row[FEATURES[5]])-context['savings']-payment-running
            assert (upfront,payment,running,remaining)==tuple(int(row[k]) for k in ('초기지급액_원','월할부금_원','월유지비_원','차량비용차감후월잔여액_원'))
            assert remaining>=context['buffer'] and (not context['ceiling'] or v.price<=context['ceiling'])
            financial=[r for r in expected]
            models=set()
            for rank,index in enumerate(financial,1):
                recommendation=next(top); vehicle=policy.vehicles[index]
                assert recommendation['프로필_식별자']==identity and int(recommendation['추천순위'])==rank
                assert recommendation['차량사양번호']==vehicle.id
                _,pay,run=independent_cost(row,vehicle)
                rem=int(row[FEATURES[0]])-int(row[FEATURES[2]])-int(row[FEATURES[3]])-int(row[FEATURES[5]])-context['savings']-pay-run
                assert rem>=context['buffer']
                assert (pay,run,rem)==tuple(int(recommendation[k]) for k in ('월할부금_원','월유지비_원','차량비용차감후월잔여액_원'))
                assert (vehicle.brand,vehicle.model) not in models; models.add((vehicle.brand,vehicle.model))
                assert int(recommendation['가중점수_만점10000'])==round(float(pool['scores'][index])*10000)
                counts['top3_rows']+=1
            if counts['rows']<1000:
                # Cross-check the vectorized teacher against the actual serving scorer.
                profile=Profile(monthly_income=int(row[FEATURES[0]]),monthly_expenses=int(row[FEATURES[2]])+int(row[FEATURES[3]]),
                    existing_monthly_payment=int(row[FEATURES[5]]),liquid_assets=int(row[FEATURES[1]]),
                    down_payment=min(context['funds'],v.price),emergency_reserve=context['reserve'],monthly_savings=context['savings'],
                    annual_distance=int(row[FEATURES[6]]),months=60,annual_rate=.06,minimum_buffer=context['buffer'],
                    purpose={'출퇴근':'commute','가족이동':'family','여가':'leisure','업무':'business'}[row[FEATURES[7]]],
                    preferred_fuel=next((key for key,value in FUEL_LABELS.items() if value==row[PREFERENCES[2]]),None),
                    preferred_size={'작음':'small','중간':'medium','큼':'large'}[row[PREFERENCES[1]]],minimum_seats=int(row[PREFERENCES[3]]),
                    cost_importance=int(row[PREFERENCES[0]]),space_importance=int(row[WEIGHTS[0]]),fuel_importance=int(row[WEIGHTS[1]]),
                    seating_importance=int(row[WEIGHTS[2]]),purpose_importance=int(row[WEIGHTS[3]]))
                scalar=integrated_score(profile,v,assess(profile,v),.5)['total']/100
                index=next(i for i,item in enumerate(policy.vehicles) if item.id==v.id)
                assert abs(scalar-pool['scores'][index])<1e-5,(scalar,pool['scores'][index])
                counts['serve_score_crosschecks']+=1
            group=row['재무조건그룹번호']; signature=tuple(row[k] for k in (*FEATURES,*PREFERENCES,*WEIGHTS,*context_fields))
            assert group not in groups or groups[group]==split; groups[group]=split
            assert signature not in inputs or inputs[signature]==split; inputs[signature]=split
            assert split=='평가' or not holdout(row)
            counts['rows']+=1
            if counts['rows']%50000==0: print(f'Audited {counts["rows"]}',flush=True)
        assert next(old,None) is None and next(top,None) is None
    assert hashlib.sha256(path.read_bytes()).hexdigest()==digest
    result={'counts':counts,'financial_violations':0,'missing_cells':0,'incorrect_top3':0,'cross_split_leakage':0,
            'original_finance_preferences_splits_preserved':True,'recommendation_count_rule':'min(3,financially eligible distinct models)',
            'source_snapshot':'preference-quality-v3','dataset_sha256':digest}
    (OUTPUT/'validation_report.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(result,ensure_ascii=True,indent=2))


if __name__=='__main__': audit()
