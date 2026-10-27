"""Version existing independent inputs; recompute body-aware labels and pairs."""
import argparse
import csv
import hashlib
import json
import random
from collections import Counter
from dataclasses import asdict
from pathlib import Path

import numpy as np

from vehicle_matching.body_types import BODY_TYPES, apply_body_types
from vehicle_matching.catalog import ROOT, read_catalog, save_catalog, catalog_fingerprint
from vehicle_matching.finance import Profile, assess
from vehicle_matching.partition_preference_population import digest, compact_pairs
from vehicle_matching.preference_model import FEATURE_NAMES, LEGACY_FEATURE_NAMES, encode_body
from vehicle_matching.train_preference_population import teacher

LABELS = dict(SEDAN='세단', SUV='SUV', HATCHBACK='해치백', WAGON='왜건', MPV='미니밴·승합', BOX='박스카', PICKUP='픽업트럭', any='상관없음')

def extend(source, output, seed=20261026):
    output.mkdir(parents=True, exist_ok=False)
    cars = apply_body_types(read_catalog(source/'catalog.json'))
    save_catalog(output/'catalog.json', cars)
    report = {'version': 'body-preference-v1', 'seed': seed, 'source': str(source),
              'policy': 'cash-preference-body-v10', 'features': list(FEATURE_NAMES),
              'registry_sha256': digest(ROOT/'data/vehicles/body-type-registry-v1.json'),
              'source_hashes': {}, 'comparison_partitions': {}, 'counts': {}, 'group_split_leakage': 0}
    financial_extra = []
    all_groups = []
    for code, (role, csv_name) in enumerate((('train','training.csv'), ('validation','validation.csv'), ('test','evaluation.csv'), ('financial','financial_validation.csv'))):
        records = {}
        for line in (source/f'{role}_profiles.jsonl').open(encoding='utf-8'):
            record = json.loads(line)
            # Stable per-input randomization independent of vehicle/selection and split.
            key = json.dumps(record['profile'], sort_keys=True, separators=(',',':'))
            rng = random.Random(seed + int(hashlib.sha256(key.encode()).hexdigest()[:16],16))
            record['profile'].update(preferred_body_type=rng.choice(('any', *BODY_TYPES)), body_importance=rng.choice((1,3,5)))
            records[record['id']] = record
        selected = {}; rejected = set(); pair_counts = Counter()
        if role != 'financial':
            with np.load(source/f'{role}_pairs.npz') as saved:
                data = {key: saved[key].copy() for key in saved.files}
            if data['features'].shape[1] != len(LEGACY_FEATURE_NAMES):
                raise ValueError('Expected unchanged legacy feature matrix')
            additions = np.empty((len(data['features']), len(FEATURE_NAMES)-len(LEGACY_FEATURE_NAMES)),dtype=np.float32)
            ids, starts, counts = np.unique(data['profile_ids'],return_index=True,return_counts=True)
            pairs = []
            for n,(pid,start,count) in enumerate(zip(ids,starts,counts)):
                if not np.all(data['profile_ids'][start:start+count] == pid):
                    raise ValueError('Candidate rows must be contiguous within an input')
                record = records[int(pid)]; p = Profile(**record['profile'])
                weight = p.cost_importance + (p.space_importance if p.preferred_size != 'any' else 0) + (p.fuel_importance if p.preferred_fuel else 0) + (p.seating_importance if p.minimum_seats else 0)
                for row in range(start,start+count):
                    car = cars[int(data['vehicle_indices'][row])]
                    additions[row] = encode_body(p,car)
                    if p.preferred_body_type != 'any':
                        data['targets'][row] = (float(data['targets'][row])*weight + (car.body_type == p.preferred_body_type)*p.body_importance)/(weight+p.body_importance)
                    if n < 3 and abs(float(data['targets'][row])-teacher(p,car,assess(p,car))) > 1e-6:
                        raise AssertionError('Migrated target differs from current scoring policy')
                scores = data['targets'][start:start+count]
                possibilities = [(start+a,start+b) if scores[a]>scores[b] else (start+b,start+a)
                                 for a in range(count) for b in range(a) if abs(scores[a]-scores[b]) >= .01]
                rng = random.Random(seed+int(pid))
                chosen = rng.sample(possibilities,min(8,len(possibilities)))
                pairs.extend(chosen); pair_counts[int(pid)] = len(chosen)
                if not chosen:
                    rejected.add(int(pid)); financial_extra.append(record)
                else:
                    probs = np.exp((scores-scores.max())/.06); probs /= probs.sum()
                    offset = rng.choices(range(count),weights=probs,k=1)[0]
                    car = cars[int(data['vehicle_indices'][start+offset])]
                    selected[int(pid)] = (car, assess(p,car), round(float(probs[offset])*10000))
            data['features'] = np.concatenate((data['features'],additions),axis=1)
            data['pairs'] = np.asarray(pairs,dtype=np.int64).reshape(-1,2)
            data = compact_pairs(data,code)
            np.savez_compressed(output/f'{role}_pairs.npz',**data)
            report['comparison_partitions'][role] = {'profiles':len(ids)-len(rejected),'candidates':len(data['features']),'pairs':len(data['pairs'])}
            all_groups.append({r['group'] for pid,r in records.items() if pid not in rejected})
        with (source/csv_name).open(encoding='utf-8-sig',newline='') as src, (output/csv_name).open('w',encoding='utf-8-sig',newline='') as dst, (output/f'{role}_profiles.jsonl').open('w',encoding='utf-8') as jout:
            reader = csv.DictReader(src)
            fields = list(reader.fieldnames)+['선호차체형태','차체형태중요도','선택차량차체형태','생성규칙버전']
            writer = csv.DictWriter(dst,fieldnames=fields); writer.writeheader()
            count = 0
            for row in reader:
                pid = int(row['사례번호'].removeprefix('C-'))
                if pid in rejected:
                    continue
                record = records[pid]; p = Profile(**record['profile'])
                row.update(선호차체형태=LABELS[p.preferred_body_type],차체형태중요도=p.body_importance,생성규칙버전='body-preference-v1')
                if pid in selected:
                    car,cost,prob = selected[pid]
                    assert cost['eligible']
                    row.update(선택차량번호=car.id,선택모델=car.model,선택차량가격_원=int(car.price),월유지비_원=int(cost['monthly_running_cost']),구매후예금_원=int(p.liquid_assets-car.price),월예금소진액_원=int(cost['monthly_asset_drawdown']),선택확률_만분율=prob,비교학습쌍수=pair_counts[pid])
                chosen_car = next((v for v in cars if v.id == row['선택차량번호']),None)
                row['선택차량차체형태'] = LABELS[chosen_car.body_type] if chosen_car else '해당없음'
                writer.writerow(row); jout.write(json.dumps(record,ensure_ascii=False)+'\n'); count+=1
            report['counts'][role]=count
        report['source_hashes'][csv_name]=digest(source/csv_name)
        print(json.dumps({'completed':role,'profiles':count,'moved_to_financial':len(rejected)}),flush=True)
    # These inputs have no sufficiently separated comparison after re-evaluation.
    # Preserve them as a separate financial-only JSONL, never train with empty labels.
    with (output/'body_tie_financial_profiles.jsonl').open('w',encoding='utf-8') as stream:
        for record in financial_extra:
            stream.write(json.dumps({**record,'reason':'차체반영후비교점수차이부족'},ensure_ascii=False)+'\n')
    report['moved_tie_financial_profiles']=len(financial_extra)
    assert not any(all_groups[a]&all_groups[b] for a in range(3) for b in range(a))
    for name in ('financial_boundary_cases.csv',):
        (output/name).write_bytes((source/name).read_bytes())
    rules=(source/'rules.txt').read_text(encoding='utf-8')
    rules+='\n\n[차체 형태 확장 규칙 body-preference-v1]\n'
    rules+='차량 차체는 data/vehicles/body-type-registry-v1.json의 브랜드·모델 정확 일치로만 연결한다. 미등록 모델을 SUV 등으로 추정하지 않는다. 제조사 출처 URL을 함께 보존한다. 경차는 크기/법정 규격이므로 차체 형태로 쓰지 않는다.\n'
    rules+='형태: 세단/SUV/해치백/왜건/미니밴·승합/박스카/픽업. 쿠페형 SUV는 SUV, 국내 EV4는 세단, G70 슈팅브레이크·3시리즈 투어링은 왜건, 레이는 박스카. 픽업은 현재 카탈로그 0건이며 임의 차량을 만들지 않는다.\n'
    rules+='기존 재무/선호/분할은 보존. 차체 선호는 any와 7형태에서 균등, 중요도는 1/3/5에서 독립 생성. 입력 해시+시드로 재현하며 선택 차량·가격·순위를 참조하지 않는다.\n'
    rules+='일치 100점, 불일치 0점, 미확인 50점 및 미확인 표시. any는 평가 제외. 재무 적격은 그대로 절대 조건이며 형태는 가중치 선호로만 사용.\n'
    rules+='기존 후보 집합 안에서 정답 점수를 재계산하고 0.01 이상 차이의 비교를 최대 8쌍 재추출한다. 비교 불가능 사례는 body_tie_financial_profiles.jsonl에 분리. 다른 재무 그룹 간 비교 금지.\n'
    rules+='선택 차량은 재평가된 후보의 효용으로 온도 0.06 확률 선택. 기존 financial 검증 CSV는 비교 학습에 쓰지 않으며 기존 선택 예시를 보존하고 차체 속성만 추가한다.\n'
    rules+='학습 입력은 기존 29개+차체 일치/지정/중요도 및 차량/선호 형태 원핫 17개=46개. 기존 29입력 체크포인트를 새 입력을 학습했다고 해석하지 않는다. 신규 모델 재학습 전 서비스의 차체 선호는 명시적 규칙으로만 반영한다.\n'
    (output/'rules.txt').write_text(rules,encoding='utf-8')
    report['output_hashes']={p.name:digest(p) for p in output.iterdir() if p.is_file()}
    (output/'refinement_report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    (output/'README.md').write_text('차체 선호 확장 데이터\n\n원본 및 기존 체크포인트는 보존. training/validation/evaluation CSV와 train/validation/test_pairs.npz가 대응한다. 재학습용 46입력. financial 및 body_tie 파일은 학습 제외. 자세한 생성·출처·분할 규칙은 rules.txt 참조.\n',encoding='utf-8')
    return report

if __name__ == '__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--source',type=Path,required=True);parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args();extend(args.source,args.output)
