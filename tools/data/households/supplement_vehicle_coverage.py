"""Supplement rare training labels by rejection sampling independent profiles."""
import csv
import hashlib
import json
import random
import shutil
import subprocess
from collections import Counter

from tools.data.households.build_quality_training import OUTPUT, new_group, emit_result, holdout
from tools.data.households.extend_training_preferences import ROOT, FEATURES, write_csv
from tools.data.households.quality_choice_policy import QualityPolicy
from vehicle_matching.catalog import read_catalog

DESTINATION = OUTPUT.parent/'preference-quality-v2'


def build(minimum=100, seed=20261023):
    if subprocess.check_output(['git','branch','--show-current'],cwd=ROOT,text=True).strip()!='ml/test':
        raise ValueError('Run only on ml/test')
    main = subprocess.check_output(['git','rev-parse','main'],cwd=ROOT,text=True).strip()
    path = OUTPUT/'combined_training.csv'
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    counts, names = Counter(), {}
    with path.open(encoding='utf-8-sig',newline='') as source:
        reader = csv.DictReader(source)
        fields = reader.fieldnames
        for row in reader:
            label = row['선택차량_라벨코드']
            names[label] = row['선택차량_모델']
            if row['데이터_구분']=='학습': counts[label]+=1
    before = {label:counts[label] for label in names}
    targets = {label for label in names if counts[label]<minimum}
    policy = QualityPolicy(read_catalog(OUTPUT/'catalog.json'))
    with (OUTPUT/'vehicle_identity_map.csv').open(encoding='utf-8-sig',newline='') as source:
        labels = {r['차량사양번호']:r['선택차량_라벨코드'] for r in csv.DictReader(source)}
    finance_rng, preference_rng = random.Random(seed), random.Random(seed+1)
    additions = []
    attempts = 0
    while any(counts[label]<minimum for label in targets):
        people, context = new_group(attempts,finance_rng,preference_rng)
        # Independent high-budget mixture, specified before candidate evaluation.
        # No preference or financial field depends on a selected vehicle.
        scale = finance_rng.choice((1,2,3,4))
        for person in people:
            for key in FEATURES[:6]: person[key] = str(int(person[key])*scale)
            person['데이터_구분']='학습'
            person['재무조건그룹번호']=f'NEW-COVER-{attempts:08}'
            person['프로필_식별자']=person['프로필_식별자'].replace('NEW-Q-', 'NEW-COVER-')
        context = {key:value*scale for key,value in context.items()}
        for person in people:
            if holdout(person): continue
            pool,_ = policy.pool(person,context)
            if pool is None: continue
            result = emit_result(policy,person,context,pool,labels,seed,'신규독립생성',int(person[FEATURES[0]]),'해당없음')
            label = result['선택차량_라벨코드']
            if label not in targets or counts[label]>=minimum: continue
            additions.append(result)
            counts[label]+=1
        attempts+=1
        if attempts%10000==0:
            print(f'Attempted {attempts}; added {len(additions)}; remaining '+str({names[k]:minimum-counts[k] for k in targets if counts[k]<minimum}),flush=True)
        if attempts>=1000000: raise RuntimeError('Coverage target not reached; no partial dataset published')
    DESTINATION.mkdir(exist_ok=True)
    for name in ('catalog.json','vehicle_identity_map.csv','length_evidence.json','legacy_screening.csv'):
        shutil.copyfile(OUTPUT/name,DESTINATION/name)
    with (DESTINATION/'combined_training.csv').open('w',encoding='utf-8-sig',newline='') as destination:
        writer = csv.DictWriter(destination,fieldnames=fields)
        writer.writeheader()
        with path.open(encoding='utf-8-sig',newline='') as source:
            writer.writerows(csv.DictReader(source))
        writer.writerows(additions)
    write_csv(DESTINATION/'supplement_training.csv',fields,additions)
    write_csv(DESTINATION/'examples.csv',fields,additions[:30])
    coverage = [{'차량라벨':label,'차량모델':names[label],'보완전학습행수':before[label],
                 '추가학습행수':counts[label]-before[label],'보완후학습행수':counts[label]} for label in sorted(names)]
    write_csv(DESTINATION/'label_coverage.csv',list(coverage[0]),coverage)
    assert hashlib.sha256(path.read_bytes()).hexdigest()==digest
    assert subprocess.check_output(['git','rev-parse','main'],cwd=ROOT,text=True).strip()==main
    report = {'seed':seed,'minimum_training_rows':minimum,'added_rows':len(additions),'attempted_financial_groups':attempts,
              'source_sha256':digest,'source_unchanged':True,'main_unchanged':True,'coverage':coverage,
              'policy':'Independent input generation and ordinary stochastic choice, then retain only rare labels. No forced labels or evaluation transfers.',
              'income_mixture':'Original generator multiplied by independently drawn 1,2,3,4; all six financial inputs and context scaled together before selection. Income up to 60 million won.',
              'limitation':'Class coverage supplement deliberately changes training class distribution; 100 rows is a starting floor, not a performance guarantee.'}
    (DESTINATION/'coverage_report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps({'added_rows':len(additions),'coverage':coverage},ensure_ascii=True),flush=True)


if __name__=='__main__': build()
