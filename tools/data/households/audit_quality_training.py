"""Verify quality training outputs, holdouts, old-input preservation and choice alignment."""
import csv
import hashlib
import json
from collections import Counter

import numpy as np

from tools.data.households.build_quality_training import OUTPUT,SOURCE,holdout
from tools.data.households.quality_choice_policy import QualityPolicy
from tools.data.households.audit_complete_choices import independent_cost
from tools.data.households.complete_preference_choices import context_from_row
from tools.data.households.extend_training_preferences import FEATURES,PREFERENCES,FUEL_LABELS,write_csv
from vehicle_matching.catalog import read_catalog
from vehicle_matching.preferences import SIZE_BANDS


def audit(base=OUTPUT):
    path=base/'combined_training.csv'
    digest=hashlib.sha256(path.read_bytes()).hexdigest()
    policy=QualityPolicy(read_catalog(base/'catalog.json'))
    by_id={v.id:v for v in policy.vehicles}
    with (base/'vehicle_identity_map.csv').open(encoding='utf-8-sig',newline='') as f:
        labels={r['차량사양번호']:r['선택차량_라벨코드'] for r in csv.DictReader(f)}
    indexes={v.id:i for i,v in enumerate(policy.vehicles)}
    preserved={}
    with (SOURCE/'combined_training.csv').open(encoding='utf-8-sig',newline='') as f:
        for row in csv.DictReader(f):
            if not row['프로필_식별자'].startswith('NEW-'):
                preserved[row['프로필_식별자']]={k:row[k] for k in (*FEATURES,*PREFERENCES,'데이터_구분')}
    imported={'테슬라','메르세데스-벤츠','BMW','렉서스','볼보'}
    stats,models,origins,splits,examples=Counter(),Counter(),Counter(),Counter(),[]
    ids,groups,combinations,repeats,input_splits=set(),{},{},{},{}
    extra_margins=[]
    with path.open(encoding='utf-8-sig',newline='') as f:
        for row in csv.DictReader(f):
            stats['rows']+=1
            identity=row['프로필_식별자']
            if identity in ids or any(value=='' for value in row.values()):
                raise AssertionError('Duplicate or missing value')
            ids.add(identity)
            vehicle=by_id[row['선택차량사양번호']]
            if vehicle.model!=row['선택차량_모델'] or vehicle.brand!=row['선택차량_브랜드'] or vehicle.trim!=row['선택트림']:
                raise AssertionError('Vehicle metadata mismatch')
            if labels[vehicle.id]!=row['선택차량_라벨코드'] or round(vehicle.price)!=int(row['선택차량가격_원']) or vehicle.length_mm!=int(row['선택차량전장_mm_0이면미확인']):
                raise AssertionError('Label, price or length mismatch')
            context=context_from_row(row)
            upfront,payment,running=independent_cost(row,vehicle)
            available=int(row[FEATURES[0]])-int(row[FEATURES[2]])-int(row[FEATURES[3]])-int(row[FEATURES[5]])-context['savings']
            remaining=available-payment-running
            required=max(100000,(int(row[FEATURES[0]])+19)//20,(payment+running+9)//10)
            if (upfront,payment,running,remaining)!=(int(row['초기지급액_원']),int(row['월할부금_원']),int(row['월유지비_원']),int(row['차량비용차감후월잔여액_원'])):
                raise AssertionError('Independent finance discrepancy')
            if remaining-context['buffer']<required:
                raise AssertionError('Insufficient quality headroom')
            extra_margins.append(remaining-context['buffer'])
            if context['funds']+context['reserve']>int(row[FEATURES[1]]) or (context['ceiling'] and vehicle.price>context['ceiling']):
                raise AssertionError('Cash or price cap violation')
            capacity=vehicle.seats if vehicle.seats is not None else min(vehicle.seat_options) if vehicle.seat_options else 0
            if capacity<int(row[PREFERENCES[3]]): raise AssertionError('Insufficient seats')
            pool,reason=policy.pool(row,context)
            if pool is None or not np.isfinite(pool['scores'][indexes[vehicle.id]]):
                raise AssertionError(f'Preference tier violation: {reason}')
            if pool['eligible_models']<3 or len(pool['shortlist'])<2: raise AssertionError('Insufficient candidates')
            fuel='하이브리드' if vehicle.original_fuel=='PHEV' else FUEL_LABELS[vehicle.fuel]
            if row['선택차량연료']!=fuel: raise AssertionError('Preference fuel metadata mismatch')
            low,high=SIZE_BANDS[{'작음':'small','중간':'medium','큼':'large'}[row[PREFERENCES[1]]]]
            fuel_bad=row[PREFERENCES[2]]!='상관없음' and row[PREFERENCES[2]]!=fuel
            size_bad=not low<=vehicle.length_mm<=high
            gap=max(low-vehicle.length_mm,vehicle.length_mm-high,0)
            if fuel_bad and size_bad or gap>500 or pool['tier']==2 and (fuel_bad or size_bad):
                raise AssertionError('Avoidable or severe preference mismatch')
            stats['explicit_fuel_rows']+=row[PREFERENCES[2]]!='상관없음'
            stats['fuel_mismatch']+=fuel_bad
            stats['size_mismatch']+=size_bad
            stats['both_preferences_match']+=not fuel_bad and not size_bad
            stats['imported_selected_rows']+=vehicle.brand in imported
            stats['income_adjusted_rows']+=int(row['월소득보정액_원'])>0
            models[vehicle.model]+=1
            origins[row['사례출처']]+=1
            splits[row['데이터_구분']]+=1
            if row['사례출처']!='신규독립생성':
                old=preserved[row['원본프로필번호']]
                if any(row[k]!=old[k] for k in (*FEATURES[1:],*PREFERENCES,'데이터_구분')): raise AssertionError('Legacy input changed')
                delta=int(row[FEATURES[0]])-int(old[FEATURES[0]])
                if delta<0 or delta>min(300000,int(old[FEATURES[0]])//10): raise AssertionError('Large legacy correction')
            elif int(row['월소득보정액_원']): raise AssertionError('New profile repaired after generation')
            finance=tuple(row[k] for k in FEATURES[:6])
            group=row['재무조건그룹번호']
            split=row['데이터_구분']
            if group in groups and groups[group]!=(finance,split): raise AssertionError('Group leakage')
            groups[group]=(finance,split)
            signature=hashlib.sha256(json.dumps([row[k] for k in (*FEATURES,*PREFERENCES,
                '월저축액_원','비상자금_원','구매투입가능자금_원','최소월여유자금_원',
                '구매가격상한_원_0이면미지정')],ensure_ascii=False).encode()).digest()
            if signature in input_splits and input_splits[signature]!=split:
                raise AssertionError('Identical input appears in multiple splits')
            input_splits[signature]=split
            combination=tuple(row[k] for k in (PREFERENCES[0],PREFERENCES[1],FEATURES[7]))
            combinations.setdefault(split,set()).add(combination)
            if split!='평가' and holdout(row): raise AssertionError('Heldout combination leaked')
            if row['사례출처']=='신규독립생성': repeats.setdefault(identity.rsplit('-R',1)[0],set()).add(vehicle.model)
            if len(examples)<15 and vehicle.brand in imported: examples.append(row)
            if stats['rows']%50000==0: print(f'Independently verified {stats["rows"]} quality rows',flush=True)
    if hashlib.sha256(path.read_bytes()).hexdigest()!=digest: raise AssertionError('Audit modified data')
    result={'checks':stats,'origins':origins,'splits':splits,'top_10_models':models.most_common(10),
            'selected_model_count':len(models),'top_model_share_percent':round(models.most_common(1)[0][1]/stats['rows']*100,2),
            'minimum_extra_buffer_won':min(extra_margins),'median_extra_buffer_won':round(float(np.median(extra_margins))),
            'both_mismatch_rows':0,'size_gap_over_500_mm_rows':0,'matching_alternative_ignored_rows':0,
            'hard_violations':0,'large_legacy_corrections':0,'missing_cells':0,'no_choice_rows':0,
            'heldout_combination_leakage':0,'group_leakage':0,'identical_input_split_leakage':0,
            'same_inputs_multiple_models_groups':sum(len(v)>1 for v in repeats.values()),'data_unchanged':True}
    (base/'validation_report.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
    if examples: write_csv(base/'imported_examples.csv',list(examples[0]),examples)
    print(json.dumps(result,ensure_ascii=True,indent=2))
    return result


if __name__=='__main__': audit()
