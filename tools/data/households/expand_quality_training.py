"""Audit existing labels and add 100k independent natural and coverage cases."""
import csv
import hashlib
import json
import random
import shutil
import subprocess
from collections import Counter

import numpy as np

from tools.data.households.build_quality_training import new_group, emit_result, holdout
from tools.data.households.complete_preference_choices import context_from_row
from tools.data.households.extend_training_preferences import ROOT, FEATURES, write_csv
from tools.data.households.quality_choice_policy import QualityPolicy
from vehicle_matching.catalog import read_catalog
from tools.data.households.verify_vehicle_coverage import signature

SOURCE=ROOT/'data/households/synthetic/preference-quality-v2'
OUTPUT=SOURCE.parent/'preference-quality-v3'
FLOORS={'학습':600,'검증':60,'평가':100}


class CoveragePolicy(QualityPolicy):
    """Choose only within the unchanged near-best pool, favoring missing coverage."""
    def select(self,row,context,pool,seed):
        candidates=pool.get('coverage_shortlist')
        if candidates is None: return super().select(row,context,pool,seed)
        narrowed={**pool,'shortlist':candidates}
        selected=super().select(row,context,narrowed,seed)
        selected['comparison_models']=len(pool['shortlist'])
        return selected


def coverage_candidates(pool,policy,labels,counts,split):
    return np.array([m for m in pool['shortlist']
                     if labels[policy.vehicles[policy.starts[m]].id] in counts[split]
                     and counts[split][labels[policy.vehicles[policy.starts[m]].id]]<FLOORS[split]],dtype=int)


def build(seed=20261024):
    if subprocess.check_output(['git','branch','--show-current'],cwd=ROOT,text=True).strip()!='ml/test':
        raise ValueError('Run only on ml/test')
    main=subprocess.check_output(['git','rev-parse','main'],cwd=ROOT,text=True).strip()
    path=SOURCE/'combined_training.csv'
    digest=hashlib.sha256(path.read_bytes()).hexdigest()
    policy=CoveragePolicy(read_catalog(SOURCE/'catalog.json'))
    indexes={v.id:i for i,v in enumerate(policy.vehicles)}
    with (SOURCE/'vehicle_identity_map.csv').open(encoding='utf-8-sig',newline='') as source:
        labels={r['차량사양번호']:r['선택차량_라벨코드'] for r in csv.DictReader(source)}
    OUTPUT.mkdir(exist_ok=True)
    counts={s:Counter() for s in FLOORS}
    names={}
    changes=[]
    retained=0
    input_signatures=set()
    with path.open(encoding='utf-8-sig',newline='') as source, (OUTPUT/'combined_training.csv').open('w',encoding='utf-8-sig',newline='') as destination:
        reader=csv.DictReader(source)
        fields=reader.fieldnames
        writer=csv.DictWriter(destination,fieldnames=fields); writer.writeheader()
        for row in reader:
            context=context_from_row(row)
            pool,reason=policy.pool(row,context)
            if pool is None: raise AssertionError('Existing input cannot be repaired by label alone: '+reason)
            index=indexes[row['선택차량사양번호']]
            model=int(np.searchsorted(policy.starts,index,side='right')-1)
            if not np.isfinite(pool['scores'][index]) or model not in pool['shortlist']:
                before=row['선택차량사양번호']
                old_income=int(row['보정전월소득_원'])
                row=emit_result(policy,row,context,pool,labels,seed,row['사례출처'],old_income,row['원본프로필번호'])
                changes.append({'프로필_식별자':row['프로필_식별자'],'기존차량사양':before,
                                '수정차량사양':row['선택차량사양번호'],'수정사유':'품질또는근접후보조건위반'})
            writer.writerow(row)
            input_signatures.add(signature(row))
            names[row['선택차량_라벨코드']]=row['선택차량_모델']
            counts[row['데이터_구분']][row['선택차량_라벨코드']]+=1
            retained+=1
        for split in counts:
            for label in names: counts[split].setdefault(label,0)
        before={s:dict(c) for s,c in counts.items()}
        print(f'Existing checked {retained}; corrected {len(changes)}',flush=True)
        finance_rng,preference_rng=random.Random(seed),random.Random(seed+1)
        provenance=[]
        samples=[]
        additions=0
        attempts=0
        modes=Counter()
        with (OUTPUT/'additional_100000.csv').open('w',encoding='utf-8-sig',newline='') as extra:
            extra_writer=csv.DictWriter(extra,fieldnames=fields); extra_writer.writeheader()
            while additions<100000:
                # First 70k follow the existing ordinary input/choice distribution.
                mode='일반독립생성' if additions<70000 else '차량별보강'
                people,context=new_group(attempts,finance_rng,preference_rng)
                scale=1 if mode=='일반독립생성' else finance_rng.choice((1,2,3,4))
                for person in people:
                    for key in FEATURES[:6]: person[key]=str(int(person[key])*scale)
                    person['프로필_식별자']=person['프로필_식별자'].replace('NEW-Q-','NEW-EXPAND-')
                    person['재무조건그룹번호']=f'NEW-EXPAND-{attempts:07}'
                context={key:value*scale for key,value in context.items()}
                for person in people:
                    if additions>=100000: break
                    split=person['데이터_구분']
                    if split!='평가' and holdout(person): continue
                    pool,_=policy.pool(person,context)
                    if pool is None: continue
                    actual_mode=mode
                    if mode=='차량별보강':
                        candidates=coverage_candidates(pool,policy,labels,counts,split)
                        if len(candidates): pool['coverage_shortlist']=candidates
                        elif any(counts[s][label]<FLOORS[s] for s in counts for label in names): continue
                        else: actual_mode='추가재무다양성'
                    result=emit_result(policy,person,context,pool,labels,seed,'신규독립생성',int(person[FEATURES[0]]),'해당없음')
                    label=result['선택차량_라벨코드']
                    if label not in names: continue
                    key=signature({k:str(v) for k,v in result.items()})
                    if key in input_signatures: continue
                    input_signatures.add(key)
                    writer.writerow(result); extra_writer.writerow(result)
                    additions+=1; counts[split][label]+=1; modes[actual_mode]+=1
                    provenance.append({'프로필_식별자':result['프로필_식별자'],'데이터_구분':split,
                                       '생성유형':actual_mode,'재무배율':scale})
                    if len(samples)<15 or actual_mode=='차량별보강' and len(samples)<30: samples.append(result)
                attempts+=1
                if attempts%10000==0:
                    missing=sum(max(0,FLOORS[s]-counts[s][label]) for s in counts for label in names)
                    print(f'Groups {attempts}; added {additions}; coverage deficit {missing}',flush=True)
                if attempts>1000000: raise RuntimeError('Could not meet coverage floors')
    if any(counts[s][label]<FLOORS[s] for s in counts for label in names): raise AssertionError('Coverage floor missing')
    for name in ('catalog.json','vehicle_identity_map.csv','length_evidence.json','legacy_screening.csv'):
        shutil.copyfile(SOURCE/name,OUTPUT/name)
    write_csv(OUTPUT/'examples.csv',fields,samples)
    write_csv(OUTPUT/'change_log.csv',['프로필_식별자','기존차량사양','수정차량사양','수정사유'],changes)
    write_csv(OUTPUT/'additional_provenance.csv',list(provenance[0]),provenance)
    coverage=[{'차량라벨':label,'차량모델':names[label],**{s+'_보완전':before[s][label] for s in counts},
               **{s+'_보완후':counts[s][label] for s in counts}} for label in sorted(names)]
    write_csv(OUTPUT/'label_coverage.csv',list(coverage[0]),coverage)
    assert hashlib.sha256(path.read_bytes()).hexdigest()==digest
    assert subprocess.check_output(['git','rev-parse','main'],cwd=ROOT,text=True).strip()==main
    report={'seed':seed,'source_sha256':digest,'existing_rows':retained,'corrected_rows':len(changes),
            'added_rows':additions,'total_rows':retained+additions,'modes':modes,'coverage_floors':FLOORS,
            'splits':{s:sum(c.values()) for s,c in counts.items()},'coverage':coverage,'source_and_main_unchanged':True,
            'sampling':'70k ordinary, then coverage quotas within unchanged near-best candidate pool; after quotas, independent varied finance. Inputs precede selection, no label-driven input edits.',
            'evaluation_warning':'Coverage evaluation intentionally oversamples rare labels; report separately from original and new ordinary evaluation. Old evaluation informed development and is not a fresh blind benchmark.'}
    (OUTPUT/'generation_report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps({k:v for k,v in report.items() if k!='coverage'},ensure_ascii=True,indent=2),flush=True)


if __name__=='__main__': build()
