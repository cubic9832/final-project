"""Build a screened training set, preserving originals and resampling independent new inputs."""
import argparse
import csv
import hashlib
import json
import math
import random
import subprocess
from collections import Counter
from dataclasses import asdict, replace
from pathlib import Path

from tools.data.households.quality_choice_policy import QualityPolicy
from tools.data.households.relabel_preference_choices import FEATURES, PREFERENCES, TRAINING_FIELDS, EXTRA_FIELDS, output_row
from tools.data.households.complete_preference_choices import context_from_row
from tools.data.households.audit_complete_choices import independent_cost
from tools.data.households.extend_training_preferences import ROOT, write_csv
from vehicle_matching.catalog import read_catalog

SOURCE = ROOT/'data/households/synthetic/preference-relabelled-v1'
OUTPUT = ROOT/'data/households/synthetic/preference-quality-v1'
EVIDENCE = ROOT/'data/vehicles/quality-imported-length-evidence.json'
FIELDS = ('사례출처','원본프로필번호','보정전월소득_원','월소득보정액_원','품질추가월여유_원',
          '선호우선단계','비교가능모델수','평가유형','선택차량원본연료','비용계산연료','전장참조출처')
SIZE_VALUES = ('작음','중간','큼')
PURPOSE_VALUES = ('출퇴근','가족이동','여가','업무')
FUELS = ('가솔린','하이브리드','디젤','LPG','전기','상관없음')


def holdout(row):
    return (int(row[PREFERENCES[0]])+SIZE_VALUES.index(row[PREFERENCES[1]])+PURPOSE_VALUES.index(row[FEATURES[7]]))%5 == 0


def load_quality_catalog(source=SOURCE):
    evidence = json.loads(EVIDENCE.read_text(encoding='utf-8'))
    lookup = {(v['brand'],v['model']):v for v in evidence['vehicles']}
    result = []
    for vehicle in read_catalog(source/'catalog.json'):
        item = lookup.get((vehicle.brand,vehicle.model))
        if item and vehicle.length_mm is None:
            vehicle = replace(vehicle,length_mm=item['length_mm'],space_source_url=item['source_url'])
        result.append(vehicle)
    return result


def small_repair(policy, original, context):
    row = dict(original)
    pool,reason = policy.pool(row,context)
    if pool is not None:
        return row,pool,0,'원래입력통과'
    income = int(row[FEATURES[0]])
    limit = min(300000,income//10)
    high = limit
    row[FEATURES[0]] = str(income+high)
    upper,_ = policy.pool(row,context)
    if upper is None:
        return None,None,0,reason
    low = 0
    # Find a small sufficient correction; validate the final bounded result explicitly.
    while high-low>1000:
        middle = (low+high)//2
        row[FEATURES[0]] = str(income+middle)
        candidate,_ = policy.pool(row,context)
        if candidate is not None:
            high = middle
        else:
            low = middle
    delta = min(limit,math.ceil(high/1000)*1000)
    row[FEATURES[0]] = str(income+delta)
    pool,_ = policy.pool(row,context)
    if pool is None:
        row[FEATURES[0]] = str(income+limit)
        pool,_ = policy.pool(row,context)
        delta = limit
    return row,pool,delta,'소액보정통과'


def new_group(index, finance_rng, preference_rng):
    income = round(min(15000000,max(2500000,finance_rng.lognormvariate(math.log(5500000),.5)))/10000)*10000
    housing = round(income*finance_rng.uniform(.10,.22)/1000)*1000
    living = round(income*finance_rng.uniform(.15,.30)/1000)*1000
    payment = round(income*finance_rng.uniform(0,.12)/1000)*1000
    cash = round(income*finance_rng.uniform(2,36)/10000)*10000
    savings = round(income*finance_rng.uniform(.05,.20)/1000)*1000
    reserve = min(cash,(housing+living)*3)
    context = {'savings':savings,'reserve':reserve,'funds':cash-reserve,
               'buffer':round(income*finance_rng.uniform(0,.05)/1000)*1000,'ceiling':0}
    debt = payment*finance_rng.randint(12,120)
    distance = finance_rng.randrange(3000,30001,1000)
    split = '학습' if index%10<7 else '검증' if index%10==7 else '평가'
    people = []
    for variant in range(3):
        purpose = preference_rng.choice(PURPOSE_VALUES)
        seats = preference_rng.choice((3,4,5,6)) if purpose=='가족이동' else preference_rng.choice((1,2,4))
        size = '큼' if seats>=6 else preference_rng.choice(('중간','큼')) if seats==5 else preference_rng.choice(SIZE_VALUES)
        person = dict(zip(FEATURES,(str(income),str(cash),str(housing),str(living),str(debt),str(payment),str(distance),purpose)))
        person.update(dict(zip(PREFERENCES,(str(preference_rng.randint(1,5)),size,preference_rng.choice(FUELS),str(seats)))))
        person.update({'프로필_식별자':f'NEW-Q-{index:07}-P{variant}', '재무조건그룹번호':f'NEW-Q-{index:07}',
                       '데이터_구분':split,'선택차량_라벨코드':'UNASSIGNED','선택차량_브랜드':'해당없음',
                       '선택차량_모델':'차량선택전','선택상태':'입력생성','선호값_출처':'차량선택전합성생성'})
        people.append(person)
    return people,context


def emit_result(policy,row,context,pool,labels,seed,origin,original_income,original_id):
    selected = policy.select(row,context,pool,seed)
    result = output_row(row,context,selected,labels)
    vehicle = selected['vehicle']
    upfront,payment,running = independent_cost(result,vehicle)
    available = int(row[FEATURES[0]])-int(row[FEATURES[2]])-int(row[FEATURES[3]])-int(row[FEATURES[5]])-context['savings']
    remaining = available-payment-running
    required = max(100000,(int(row[FEATURES[0]])+19)//20,(payment+running+9)//10)
    if remaining-context['buffer']<required or pool['eligible_models']<3 or selected['comparison_models']<2:
        raise AssertionError('Quality headroom or candidate count violation')
    capacity = vehicle.seats if vehicle.seats is not None else min(vehicle.seat_options) if vehicle.seat_options else 0
    if capacity<int(row[PREFERENCES[3]]) or context['funds']+context['reserve']>int(row[FEATURES[1]]):
        raise AssertionError('Seating or cash violation')
    if selected['tier']==2 and selected['semantic_fuel']!=row[PREFERENCES[2]] and row[PREFERENCES[2]]!='상관없음':
        raise AssertionError('Both-match preference tier violated')
    result.update({'초기지급액_원':upfront,'월할부금_원':payment,'월유지비_원':running,
                   '차량비용차감후월잔여액_원':remaining,'선택차량연료':selected['semantic_fuel'],
                   '선택설명':'적격3개이상_선호동시충족우선_근접후보2개이상비교' if selected['tier']==2 else
                   '두선호동시충족적격후보없음_한선호우선절충_차이500mm이내',
                   '사례출처':origin,'원본프로필번호':original_id,'보정전월소득_원':original_income,
                   '월소득보정액_원':int(row[FEATURES[0]])-original_income,'품질추가월여유_원':required,
                   '선호우선단계':'크기연료동시충족' if selected['tier']==2 else '한선호절충',
                   '비교가능모델수':selected['comparison_models'],
                   '평가유형':'새선호조합평가' if row['데이터_구분']=='평가' and holdout(row) else
                   '새재무상황평가' if row['데이터_구분']=='평가' else '해당없음',
                   '선택차량원본연료':vehicle.original_fuel or vehicle.fuel,
                   '비용계산연료':vehicle.fuel,'전장참조출처':vehicle.space_source_url or '기존제원근거'})
    if any(v in ('',None) for v in result.values()):
        raise AssertionError('Incomplete quality row')
    return result


def build(output=OUTPUT,seed=20261022,target=206156):
    if subprocess.check_output(['git','branch','--show-current'],cwd=ROOT,text=True).strip()!='ml/test':
        raise ValueError('Run only on ml/test')
    output = Path(output).resolve()
    if output==SOURCE.resolve() or not output.is_relative_to((ROOT/'data/households/synthetic').resolve()):
        raise ValueError('Use separate synthetic output directory')
    source_path = SOURCE/'combined_training.csv'
    source_hash = hashlib.sha256(source_path.read_bytes()).hexdigest()
    main = subprocess.check_output(['git','rev-parse','main'],cwd=ROOT,text=True).strip()
    vehicles = load_quality_catalog()
    policy = QualityPolicy(vehicles)
    with (SOURCE/'vehicle_identity_map.csv').open(encoding='utf-8-sig',newline='') as f:
        labels = {r['차량사양번호']:r['선택차량_라벨코드'] for r in csv.DictReader(f)}
    output.mkdir(parents=True,exist_ok=True)
    schema = (*TRAINING_FIELDS,*EXTRA_FIELDS,*FIELDS)
    counts,models,rejected,samples = Counter(),Counter(),Counter(),[]
    ledger_fields = ('원본프로필번호','처리','이유','소득보정액_원')
    with (output/'combined_training.csv').open('w',encoding='utf-8-sig',newline='') as destination, \
         (output/'legacy_screening.csv').open('w',encoding='utf-8-sig',newline='') as ledger:
        writer = csv.DictWriter(destination,fieldnames=schema); writer.writeheader()
        log = csv.DictWriter(ledger,fieldnames=ledger_fields); log.writeheader()
        def append(result):
            if set(result)!=set(schema):
                raise AssertionError('Unexpected quality schema')
            writer.writerow(result)
            counts['rows']+=1
            counts[result['사례출처']]+=1
            models[result['선택차량_모델']]+=1
            counts['income_adjusted_rows']+=result['월소득보정액_원']>0
            counts['partial_preference_rows']+=result['선호우선단계']=='한선호절충'
            if len(samples)<30:
                samples.append(result)
        with source_path.open(encoding='utf-8-sig',newline='') as f:
            for original in csv.DictReader(f):
                if original['프로필_식별자'].startswith('NEW-'):
                    continue
                context = context_from_row(original)
                if original['데이터_구분']!='평가' and holdout(original):
                    repaired,pool,delta,reason = None,None,0,'보류선호조합_학습검증에서제외'
                else:
                    repaired,pool,delta,reason = small_repair(policy,original,context)
                if pool is None:
                    rejected[reason]+=1
                    status = '보존본에유지_신규사례로대체'
                else:
                    result = emit_result(policy,repaired,context,pool,labels,seed,'기존소액보정' if delta else '기존입력유지',
                                         int(original[FEATURES[0]]),original['프로필_식별자'])
                    append(result); status='학습본채택'
                log.writerow(dict(zip(ledger_fields,(original['프로필_식별자'],status,reason,delta))))
        print(f'Legacy screening complete: retained {counts["rows"]} rows',flush=True)
        finance_rng,preference_rng = random.Random(seed+100),random.Random(seed+200)
        index = 0
        while counts['rows']<target:
            people,context = new_group(index,finance_rng,preference_rng)
            counts['new_finance_groups_attempted']+=1
            for person in people:
                if counts['rows']>=target: break
                if person['데이터_구분']!='평가' and holdout(person):
                    counts['new_heldout_inputs_skipped']+=1; continue
                pool,reason = policy.pool(person,context)
                if pool is None:
                    counts['new_inputs_rejected']+=1; continue
                for repetition in range(4):
                    if counts['rows']>=target: break
                    row = {**person,'프로필_식별자':person['프로필_식별자']+f'-R{repetition}'}
                    result = emit_result(policy,row,context,pool,labels,seed,'신규독립생성',int(row[FEATURES[0]]),'해당없음')
                    append(result)
            index+=1
            if index%2000==0: print(f'Written {counts["rows"]} quality rows',flush=True)
            if index>target*3: raise RuntimeError('Cannot generate enough qualified independent profiles')
    if counts['rows']!=target: raise AssertionError('Unexpected target count')
    if hashlib.sha256(source_path.read_bytes()).hexdigest()!=source_hash: raise AssertionError('Source modified')
    if subprocess.check_output(['git','rev-parse','main'],cwd=ROOT,text=True).strip()!=main: raise AssertionError('Main changed')
    write_csv(output/'examples.csv',schema,samples)
    (output/'catalog.json').write_text(json.dumps([asdict(v) for v in policy.vehicles],ensure_ascii=False,indent=2),encoding='utf-8')
    (output/'vehicle_identity_map.csv').write_bytes((SOURCE/'vehicle_identity_map.csv').read_bytes())
    (output/'length_evidence.json').write_bytes(EVIDENCE.read_bytes())
    report = {'counts':counts,'legacy_rejection_reasons':rejected,'selected_models':models,
              'source_unchanged':True,'main_unchanged':True,'hard_violations':0}
    settings = {'seed':seed,'target_rows':target,'source_path':str(SOURCE),'source_sha256':source_hash,'main_ref':main,
                'legacy_income_correction_cap':'min(10 percent of original income, 300000 won)',
                'headroom':'max(100000 won,5 percent income,10 percent monthly car cost) ABOVE original minimum buffer',
                'candidate_counts':'at least 3 eligible model names and 2 near-best models in preferred tier',
                'preference_policy':'both size and fuel when available; otherwise exactly one preference with size gap no more than 500mm',
                'missing_spec_policy':'neutral 0.5 score; pending evidence, excluded only from verified training labels, not declared physically unsuitable',
                'new_generation':'Generate finance and preferences before checking candidate feasibility; reject/resample input, never modify it after choosing a label',
                'financing':'60 months, annual 6 percent; same energy and fixed assumptions as prior snapshots',
                'new_profile_repeats':4,'new_preferences_per_financial_group':3,
                'holdout':'same cost-size-purpose modulo-5 combination removed from all training/validation, including legacy rows',
                'imported_dimensions':'Manufacturer body references; overseas sources explicitly documented, not Korean trim-specific certification',
                'market_share_claim':False}
    for name,value in [('generation_config.json',settings),('generation_report.json',report)]:
        (output/name).write_text(json.dumps(value,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps({'counts':counts,'rejected':rejected},ensure_ascii=True))


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,default=OUTPUT)
    parser.add_argument('--target',type=int,default=206156)
    args=parser.parse_args(); build(args.output,target=args.target)
