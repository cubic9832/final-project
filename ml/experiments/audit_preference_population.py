"""Independently re-read saved population CSV and pair arrays before deployment."""
import argparse
import csv
import hashlib
import json
from collections import Counter
from pathlib import Path

import numpy as np

from vehicle_matching.catalog import read_catalog
from vehicle_matching.finance import Profile, assess
from vehicle_matching.train_preference_population import independent_eligible


def audit(directory):
    directory=Path(directory)
    report=json.loads((directory/'generation_report.json').read_text(encoding='utf-8'))
    vehicles=read_catalog(directory/'catalog.json')
    by_id={vehicle.id:vehicle for vehicle in vehicles}
    records=[json.loads(line) for line in (directory/'profiles.jsonl').read_text(encoding='utf-8').splitlines()]
    arrays=np.load(directory/'candidate_pairs.npz')
    profiles=arrays['profile_ids'];splits=arrays['splits'];pairs=arrays['pairs']
    assert len(records)==report['profiles']
    assert np.all(arrays['targets'][pairs[:,0]] > arrays['targets'][pairs[:,1]])
    assert np.all(profiles[pairs[:,0]] == profiles[pairs[:,1]])
    assert np.all(splits[pairs[:,0]] == splits[pairs[:,1]])
    assert np.isfinite(arrays['features']).all() and np.isfinite(arrays['targets']).all()
    held_out={tuple(key) for key in report['held_out_models']}
    for index in np.unique(arrays['vehicle_indices'][splits!=2]):
        vehicle=vehicles[int(index)]
        assert (vehicle.brand,vehicle.model) not in held_out
    groups={};counts=Counter();selected=Counter()
    with (directory/'profiles.csv').open(encoding='utf-8-sig',newline='') as stream:
        for row,record in zip(csv.DictReader(stream),records,strict=True):
            assert groups.setdefault(record['group'],record['split'])==record['split']
            profile=Profile(**record['profile'])
            assert profile.monthly_savings==profile.emergency_reserve==profile.months==profile.annual_rate==0
            if row['선택차량번호']=='NO-CHOICE':
                assert int(row['전체재무적격사양수'])==0
                counts['no_choice']+=1
            else:
                vehicle=by_id[row['선택차량번호']]
                cost=assess(profile,vehicle)
                assert independent_eligible(profile,vehicle,cost)
                assert int(row['선택차량가격_원'])==vehicle.price
                assert int(row['구매후예금_원'])==profile.liquid_assets-vehicle.price
                assert int(row['월유지비_원'])==cost['monthly_running_cost']
                assert int(row['월예금소진액_원'])==cost['monthly_asset_drawdown']
                selected[vehicle.brand+'::'+vehicle.model]+=1
                counts['selected']+=1
            counts[record['split']]+=1
    distribution={}
    for name,code in (('train',0),('validation',1),('test',2)):
        mask=splits==code
        distribution[name]={'all_profiles':counts[name],'profiles_with_training_candidates':len(np.unique(profiles[mask])),
                            'candidate_rows':int(mask.sum()),'pairs':int((splits[pairs[:,0]]==code).sum())}
    result={'passed':True,'profiles':len(records),'financial_groups':len(groups),'counts':dict(counts),
            'split_counts':distribution,'financial_violations':0,'group_leakage':0,'cross_profile_pairs':0,
            'held_out_model_leakage':0,'selected_models':dict(selected),
            'profiles_sha256':hashlib.sha256((directory/'profiles.csv').read_bytes()).hexdigest(),
            'arrays_sha256':hashlib.sha256((directory/'candidate_pairs.npz').read_bytes()).hexdigest()}
    assert result['profiles_sha256']==report['profiles_sha256']
    assert result['arrays_sha256']==report['arrays_sha256']
    (directory/'validation_report.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
    return result


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('directory',type=Path);args=parser.parse_args()
    result=audit(args.directory)
    print(json.dumps({key:value for key,value in result.items() if key!='selected_models'},ensure_ascii=False,indent=2))
