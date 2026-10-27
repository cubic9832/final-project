"""Rebuild grouped comparisons from audited live specifications; preserve held-out groups."""
import argparse
import json
import random
from collections import Counter
from dataclasses import fields, replace
from pathlib import Path
from urllib.request import urlopen

import numpy as np
from vehicle_matching.catalog import Vehicle, read_catalog, save_catalog, catalog_fingerprint
from vehicle_matching.finance import Profile, assess
from vehicle_matching.partition_preference_population import digest
from vehicle_matching.preference_model import encode_preference, PreferenceRanker
from vehicle_matching.preferences import preference_assessment
from vehicle_matching.recommendation_policy import POLICY, ranking_key, seating_status
from vehicle_matching.train_preference_population import fit_population


def teacher_keys(profile, cars, costs):
    """Policy first; measured economy breaks rule ties without old-model labels."""
    result=[]
    for car,cost in zip(cars,costs):
        economy=preference_assessment(profile,car,cost)['components'][0]['score']
        result.append(ranking_key(profile,car,0)[:-2]+(-economy,))
    return result


def rebuild(source, output, cars, seed):
    if output.exists(): raise ValueError('Choose a new data output directory')
    output.mkdir(parents=True)
    save_catalog(output/'catalog.json',cars)
    by_id={car.id:i for i,car in enumerate(cars)}
    old_cars=read_catalog(source/'catalog.json')
    audited=[i for i,car in enumerate(cars) if car.seats_status=='official-source-verified']
    report={'seed':seed,'policy':POLICY,'catalog_mode':'verified-runtime-snapshot',
            'source':str(source.resolve()),'source_hashes':{},'partitions':{},'group_split_leakage':0,
            'teacher':'Within each financially eligible, required-seat-safe pool: importance-group preference penalties; economy breaks ties. Ordinal targets; never old ML predictions.'}
    group_sets=[]
    for code,role in enumerate(('train','validation','test')):
        records={}
        with (source/f'{role}_profiles.jsonl').open(encoding='utf-8') as stream:
            for line in stream:
                record=json.loads(line);records[record['id']]=record
        group_sets.append({r['group'] for r in records.values()})
        with np.load(source/f'{role}_pairs.npz') as saved:
            profile_ids=saved['profile_ids'].copy();vehicle_indices=saved['vehicle_indices'].copy()
        ids,starts,counts=np.unique(profile_ids,return_index=True,return_counts=True)
        xs=[];ys=[];ps=[];vs=[];pairs=[];used=set();excluded=Counter()
        with (output/f'{role}_profiles.jsonl').open('w',encoding='utf-8') as profile_out:
            for n,(pid,start,count) in enumerate(zip(ids,starts,counts)):
                pid=int(pid);record=records[pid];profile=Profile(**record['profile'])
                profile=replace(profile,financing_mode='recommendation',down_payment=0,months=0,annual_rate=0,purpose='commute',purpose_importance=1)
                indices={by_id[old_cars[int(index)].id] for index in vehicle_indices[start:start+count] if old_cars[int(index)].id in by_id}
                # Deterministic exposure to corrections, independent of chosen vehicle and split.
                if audited:
                    indices.update((audited[pid%len(audited)],audited[(pid*7+1)%len(audited)]))
                original='V-354f355b55d99324'
                if original in by_id and by_id[original] in indices:
                    indices.add(by_id[original+'-11seat'])
                candidates=[];costs=[];kept=[]
                for index in sorted(indices):
                    car=cars[index];cost=assess(profile,car)
                    if not cost['eligible'] or seating_status(profile,car)!='match':continue
                    candidates.append(car);costs.append(cost);kept.append(index)
                if len(candidates)<2:
                    excluded['fewer-than-two-required-seat-safe-candidates']+=1;continue
                keys=teacher_keys(profile,candidates,costs)
                unique=sorted(set(keys));rank={key:(len(unique)-1-i)/max(1,len(unique)-1) for i,key in enumerate(unique)}
                targets=[.05+.9*rank[key] for key in keys]
                possibilities=[(a,b) if keys[a]<keys[b] else (b,a) for a in range(len(keys)) for b in range(a) if keys[a]!=keys[b]]
                if not possibilities:excluded['equal-policy-and-economy']+=1;continue
                rng=random.Random(seed+pid)
                selected=rng.sample(possibilities,min(8,len(possibilities)))
                # Always include an extreme comparison if not already selected.
                best=min(range(len(keys)),key=lambda i:keys[i]);worst=max(range(len(keys)),key=lambda i:keys[i])
                if (best,worst) not in selected:selected[0]=(best,worst)
                offset=len(xs)
                xs.extend(encode_preference(profile,car,cost=cost) for car,cost in zip(candidates,costs))
                ys.extend(targets);ps.extend([pid]*len(candidates));vs.extend(kept)
                pairs.extend((offset+a,offset+b) for a,b in selected)
                used.add(pid);profile_out.write(json.dumps(record,ensure_ascii=False)+'\n')
                if (n+1)%20000==0:print(json.dumps({'stage':'rebuild','partition':role,'processed':n+1,'total':len(ids),'pairs':len(pairs)}),flush=True)
        arrays={'features':np.asarray(xs,dtype=np.float32),'targets':np.asarray(ys,dtype=np.float32),
                'profile_ids':np.asarray(ps,dtype=np.int64),'vehicle_indices':np.asarray(vs,dtype=np.int32),
                'pairs':np.asarray(pairs,dtype=np.int64).reshape(-1,2),'splits':np.full(len(xs),code,dtype=np.int8)}
        assert np.all(arrays['profile_ids'][arrays['pairs'][:,0]]==arrays['profile_ids'][arrays['pairs'][:,1]])
        np.savez_compressed(output/f'{role}_pairs.npz',**arrays)
        report['partitions'][role]={'profiles':len(used),'candidates':len(xs),'pairs':len(pairs),'excluded':dict(excluded)}
        for filename in (f'{role}_profiles.jsonl',f'{role}_pairs.npz'):report['source_hashes'][filename]=digest(source/filename)
        print(json.dumps({'stage':'rebuilt','partition':role,**report['partitions'][role]}),flush=True)
    if any(group_sets[a]&group_sets[b] for a in range(3) for b in range(a)):raise ValueError('Financial groups cross splits')
    report['output_hashes']={path.name:digest(path) for path in output.iterdir() if path.is_file()}
    (output/'generation_report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    (output/'README.md').write_text('공식 정원 검수 후 재생성한 비교 학습 데이터. 원본 재무 그룹과 train/validation/test 분할을 유지한다. 최소 정원 미충족·미확인 후보는 학습 제외. 기존 후보 풀에 검증된 사양 2개를 결정적으로 추가하고 새 11인 구성도 연결한다. 정책 우선·비용 동률 해소 기준으로 정답과 쌍을 새로 생성했다. 실사용자 선택 자료가 아닌 합성 교사 데이터다.\n',encoding='utf-8')
    return report


def evaluate_pairs(model, data, role):
    import torch
    with np.load(data/f'{role}_pairs.npz') as saved:
        x=saved['features'];pairs=saved['pairs']
    scores=[]
    with torch.no_grad():
        for start in range(0,len(x),32768):
            batch=((x[start:start+32768]-model.mean)/model.scale).astype(np.float32)
            scores.extend(model.net(torch.from_numpy(batch)).flatten().numpy().tolist())
    scores=np.asarray(scores)
    return {'pairs':len(pairs),'accuracy':float(np.mean(scores[pairs[:,0]]>scores[pairs[:,1]]))}


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--source',type=Path,required=True);parser.add_argument('--data',type=Path,required=True);parser.add_argument('--output',type=Path,required=True);parser.add_argument('--old-model',type=Path,required=True);parser.add_argument('--epochs',type=int,default=12);args=parser.parse_args()
    if args.output.exists():raise ValueError('Choose a new checkpoint directory')
    with urlopen('http://127.0.0.1:8080/api/v1/vehicles/recommendation-catalog',timeout=20) as stream:raw=json.load(stream)['data']
    allowed={field.name for field in fields(Vehicle)}
    cars=[Vehicle(**{k:v for k,v in row.items() if k in allowed}) for row in raw]
    report=rebuild(args.source,args.data,cars,20261027)
    from vehicle_matching.train_curated_population import load_partitions
    x,y,pairs,splits=load_partitions(args.data)
    provenance={'catalog_sha256':catalog_fingerprint(args.data/'catalog.json'),'catalog_mode':'verified-runtime-snapshot','data_dir':str(args.data.resolve()),'seed':20261027,'policy':POLICY,'split_counts':report['partitions'],'source_model':str(args.old_model.resolve()),'generation_report_sha256':digest(args.data/'generation_report.json')}
    model,history=fit_population(x,y,pairs,splits,20261027,args.epochs,args.output,provenance)
    save_catalog(args.output/'catalog.json',cars)
    old=PreferenceRanker.load(args.old_model)
    heldout={'new':evaluate_pairs(model,args.data,'test'),'old':evaluate_pairs(old,args.data,'test'),'meaning':'Agreement with rebuilt synthetic policy teacher; test not used for epoch selection.'}
    result={'history':history,'data':provenance,'holdout':heldout}
    (args.output/'training_report.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps({'stage':'training-complete','holdout':heldout}),flush=True)

if __name__=='__main__':main()
