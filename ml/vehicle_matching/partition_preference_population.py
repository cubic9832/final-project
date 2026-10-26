"""Partition existing ML cases by actual comparison use, preserving original splits."""
import argparse
import csv
import hashlib
import json
import shutil
import subprocess
from collections import Counter
from contextlib import ExitStack
from pathlib import Path

import numpy as np

from vehicle_matching.catalog import ROOT, read_catalog
from vehicle_matching.finance import Profile, assess

SPLITS = ('train', 'validation', 'test')
FILES = {'train': 'training.csv', 'validation': 'validation.csv', 'test': 'evaluation.csv',
         'financial': 'financial_validation.csv'}


def digest(path):
    result=hashlib.sha256()
    with Path(path).open('rb') as stream:
        for chunk in iter(lambda:stream.read(1024*1024),b''):result.update(chunk)
    return result.hexdigest()


def compact_pairs(data, code):
    """Keep exactly the original within-split pairs and their referenced rows."""
    original=data['pairs'][data['splits'][data['pairs'][:,0]]==code]
    indices=np.unique(original.reshape(-1))
    remap=np.full(len(data['features']),-1,dtype=np.int64)
    remap[indices]=np.arange(len(indices))
    pairs=remap[original]
    assert np.all(pairs>=0)
    assert np.array_equal(indices[pairs],original)
    return {'features':data['features'][indices], 'targets':data['targets'][indices], 'pairs':pairs,
            'profile_ids':data['profile_ids'][indices], 'vehicle_indices':data['vehicle_indices'][indices],
            'splits':data['splits'][indices], 'source_candidate_indices':indices}


def partition(source,destination,boundary_report=None):
    source=Path(source).resolve();destination=Path(destination).resolve()
    if source==destination or source in destination.parents:raise ValueError('Choose a separate output directory')
    if destination.exists():raise ValueError('Output already exists; original files are never overwritten')
    source_names=('profiles.csv','profiles.jsonl','candidate_pairs.npz','catalog.json','generation_report.json','validation_report.json')
    source_hashes={name:digest(source/name) for name in source_names}
    generation=json.loads((source/'generation_report.json').read_text(encoding='utf-8'))
    assert source_hashes['profiles.csv']==generation['profiles_sha256']
    assert source_hashes['candidate_pairs.npz']==generation['arrays_sha256']
    arrays=np.load(source/'candidate_pairs.npz',allow_pickle=False)
    records=[json.loads(line) for line in (source/'profiles.jsonl').read_text(encoding='utf-8').splitlines()]
    pairs=arrays['pairs'];profile_ids=arrays['profile_ids'];split_codes=arrays['splits']
    assert np.all(profile_ids[pairs[:,0]]==profile_ids[pairs[:,1]])
    assert np.all(split_codes[pairs[:,0]]==split_codes[pairs[:,1]])
    pair_counts=Counter(profile_ids[pairs[:,0]].tolist())
    used_indices=np.unique(pairs.reshape(-1))
    used_candidates=Counter(profile_ids[used_indices].tolist())
    candidate_counts=Counter(profile_ids.tolist())
    cars=read_catalog(source/'catalog.json')
    destination.mkdir(parents=True)
    counts=Counter();reasons=Counter();financial_counts={};group_splits={};case_ids=set()
    source_rows={}
    with ExitStack() as stack:
        inputs=stack.enter_context((source/'profiles.csv').open(encoding='utf-8-sig',newline=''))
        reader=csv.DictReader(inputs);fields=reader.fieldnames
        writers={};json_streams={}
        for role,filename in FILES.items():
            stream=stack.enter_context((destination/filename).open('w',encoding='utf-8-sig',newline=''))
            extra=['비교학습쌍수','실제비교후보수']
            if role=='financial':extra+=['분리사유','기대재무적격모델수','기대최대추천대수']
            writers[role]=csv.DictWriter(stream,fieldnames=fields+extra)
            writers[role].writeheader()
            json_streams[role]=stack.enter_context((destination/f'{role}_profiles.jsonl').open('w',encoding='utf-8'))
        for row,record in zip(reader,records,strict=True):
            case=record['id'];split=record['split'];group=record['group']
            assert row['사례번호']==f'N-{case:06}'
            assert row['사례번호'] not in case_ids
            assert group_splits.setdefault(group,split)==split
            case_ids.add(row['사례번호'])
            source_rows[row['사례번호']]={key:row[key] for key in fields}
            role=split if pair_counts[case] else 'financial'
            row['비교학습쌍수']=pair_counts[case];row['실제비교후보수']=used_candidates[case]
            if role=='financial':
                if group not in financial_counts:
                    profile=Profile(**record['profile'])
                    financial_counts[group]=len({(car.brand,car.model) for car in cars if assess(profile,car)['eligible']})
                eligible=financial_counts[group]
                if eligible==0:reason='재무적격차량없음'
                elif eligible==1:reason='재무적격모델1개'
                elif candidate_counts[case]==0:reason='평가전용모델제외후후보없음'
                elif candidate_counts[case]==1:reason='평가전용모델제외후후보1개'
                else:reason='후보간효용차이0.01미만'
                row.update({'분리사유':reason,'기대재무적격모델수':eligible,'기대최대추천대수':min(9,eligible)})
                reasons[reason]+=1
            else:
                assert row['선택차량번호']!='NO-CHOICE' and row['비교학습쌍수']>0
                assert row['데이터구분']=={'train':'학습','validation':'검증','test':'평가'}[role]
            writers[role].writerow(row)
            json_streams[role].write(json.dumps(record,ensure_ascii=False)+'\n')
            counts[role]+=1
            if len(case_ids)%20000==0:print(json.dumps({'partitioned':len(case_ids)}),flush=True)
    distributions={}
    for code,role in enumerate(SPLITS):
        compact=compact_pairs(arrays,code)
        np.savez_compressed(destination/f'{role}_pairs.npz',**compact)
        assert len(np.unique(compact['profile_ids']))==counts[role]
        distributions[role]={'profiles':counts[role],'candidate_rows':len(compact['features']),'comparison_pairs':len(compact['pairs'])}
    # Re-read all outputs, verify one-to-one coverage and unchanged original cells.
    restored=set()
    for role,filename in FILES.items():
        with (destination/filename).open(encoding='utf-8-sig',newline='') as stream:
            for row in csv.DictReader(stream):
                case=row['사례번호'];assert case not in restored;restored.add(case)
                assert {key:row[key] for key in fields}==source_rows[case]
                if role!='financial':assert int(row['비교학습쌍수'])>0
    assert restored==case_ids and len(case_ids)==generation['profiles']
    assert sum(item['comparison_pairs'] for item in distributions.values())==len(pairs)
    shutil.copyfile(source/'catalog.json',destination/'catalog.json')
    boundary_count=0
    if boundary_report:
        boundary=json.loads(Path(boundary_report).read_text(encoding='utf-8'))['financial_boundary_cases']
        with (destination/'financial_boundary_cases.csv').open('w',encoding='utf-8-sig',newline='') as stream:
            writer=csv.DictWriter(stream,fieldnames=['월소득_원','월생활지출_원','구매유지예금_원','기대추천대수','출처'])
            writer.writeheader()
            for item in boundary:
                writer.writerow({'월소득_원':item['income'],'월생활지출_원':item['expenses'],
                                 '구매유지예금_원':item['cash'],'기대추천대수':item['recommendations'],
                                 '출처':'기존 holdout_report.json의 경계 검증 사례'})
        boundary_count=len(boundary)
    assert source_hashes=={name:digest(source/name) for name in source_names}
    report={'source':str(source),'source_hashes':source_hashes,'total_source_profiles':len(case_ids),
            'partition_counts':dict(counts),'comparison_partitions':distributions,
            'financial_reasons':dict(reasons),'copied_boundary_cases':boundary_count,
            'comparison_pairs_preserved':len(pairs),'original_cell_changes':0,'duplicate_case_ids':0,
            'missing_cases':0,'source_split_changes':0,'source_files_changed':0,
            'meaning':'File organization only; current model is not retrained or replaced',
            'output_hashes':{path.name:digest(path) for path in sorted(destination.iterdir()) if path.is_file()}}
    (destination/'partition_report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    return report


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('source',type=Path);parser.add_argument('destination',type=Path)
    parser.add_argument('--boundary-report',type=Path);args=parser.parse_args()
    if subprocess.check_output(['git','branch','--show-current'],cwd=ROOT,text=True).strip()!='ml/test':raise ValueError('Run only on ml/test')
    result=partition(args.source,args.destination,args.boundary_report)
    print(json.dumps({key:value for key,value in result.items() if key not in ('source_hashes','output_hashes')},ensure_ascii=False,indent=2))
