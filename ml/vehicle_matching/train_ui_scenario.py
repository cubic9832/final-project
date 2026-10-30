"""Audit, train and evaluate the current UI contract with frozen holdout data."""
import argparse
import json
import math
from pathlib import Path
import numpy as np
import torch
from torch import nn
from vehicle_matching.catalog import ROOT, read_catalog
from vehicle_matching.finance import Profile, assess
from vehicle_matching.recommendation_policy import seating_status
from vehicle_matching.preference_model import preference_network
from vehicle_matching.ui_scenario_features import FEATURE_NAMES, encode_ui_scenario, choice_utility
from vehicle_matching.ui_scenario_model import UiScenarioRanker
from vehicle_matching.train_behavioral_choices import fit, evaluate, load_shard
from tools.data.households.generate_scenario_population import file_hash, write_json


def read_rows(path):
    return [json.loads(line) for line in path.read_text(encoding='utf-8').splitlines()]


def audit(data, manifest, catalog, traits):
    from decimal import Decimal
    groups=set();count=0;profile_count=0;correct=0;expected=0.;loss=0.
    for name,digest in manifest['files_sha256'].items():
        if file_hash(data/name)!=digest:raise ValueError(f'Dataset hash mismatch: {name}')
    for shard in manifest['shards']:
        for role in ('train','validation','test'):
            users={row['id']:row for row in read_rows(data/shard['directory']/f'{role}_profiles.jsonl')}
            for user in users.values():
                if user['group'] in groups or user['split']!=role:raise ValueError('Duplicate financial group or split leakage')
                groups.add(user['group']);profile_count+=1
            with np.load(data/shard['directory']/f'{role}_choices.npz',allow_pickle=False) as rows:
                rows = {name: rows[name] for name in rows.files}
                if not np.isfinite(rows['features']).all():raise ValueError('Nonfinite training features')
                for x,user_id,index in zip(rows['features'],rows['profile_ids'],rows['vehicle_indices']):
                    user=users[int(user_id)];car=catalog[int(index)];p=Profile(**user['profile']);cost=assess(p,car)
                    if not cost['eligible'] or seating_status(p,car)!='match':raise ValueError('Ineligible training candidate')
                    cash=Decimal(str(p.liquid_assets))-Decimal(str(car.price))
                    available=Decimal(str(p.monthly_income))-Decimal(str(p.monthly_expenses))-Decimal(str(p.existing_monthly_payment))
                    deficit=max(Decimal(0),Decimal(str(cost['monthly_running_cost']))-available)
                    if cash<0 or cash<12*deficit:raise ValueError('Independent cash/runway audit failed')
                    if not np.array_equal(x,encode_ui_scenario(user,car,traits[car.id],cost)):raise ValueError('Training/serving encoding mismatch')
                choices=read_rows(data/shard['directory']/f'{role}_choices.jsonl')
                if len(choices)!=len(rows['labels']):raise ValueError('Missing choice records')
                for (a,b),label,choice in zip(rows['comparisons'],rows['labels'],choices):
                    label = float(label)
                    if rows['profile_ids'][a]!=rows['profile_ids'][b] or choice['user_id']!=int(rows['profile_ids'][a]):raise ValueError('Cross-user pair')
                    delta=max(-60,min(60,(choice_utility(rows['features'][a])-choice_utility(rows['features'][b]))/.25))
                    probability=1/(1+math.exp(-delta))
                    if abs(probability-choice['probability_a'])>1e-10 or label!=int(choice['draw']<probability):raise ValueError('Choice probability mismatch')
                    count+=1
                    if role=='test':
                        q=min(1-1e-12,max(1e-12,probability));expected+=max(q,1-q)
                        correct+=int((q>=.5)==bool(label));loss-=label*math.log(q)+(1-label)*math.log1p(-q)
        print(json.dumps({'stage':'audit-shard','shard':shard['directory'],'profiles':profile_count,'comparisons':count}),flush=True)
    if count!=manifest['comparisons'] or profile_count!=manifest['profiles']:raise ValueError('Dataset count mismatch')
    n=manifest['partitions']['test']['comparisons']
    report={'status':'passed','profiles':profile_count,'comparisons':count,'financial_group_leakage':False,
            'generator_test':{'accuracy':correct/n,'expected_accuracy':expected/n,'log_loss':loss/n}}
    write_json(data/'validation_report.json',report);return report


def train(data, output, epochs=30):
    data,output=Path(data),Path(output)
    if output.exists():raise FileExistsError(output)
    torch.set_num_threads(4);torch.manual_seed(20261030);torch.use_deterministic_algorithms(True)
    manifest=json.loads((data/'manifest.json').read_text(encoding='utf-8'))
    if manifest['feature_names']!=list(FEATURE_NAMES):raise ValueError('Dataset feature contract mismatch')
    catalog=read_catalog(data/'catalog.json');traits=json.loads((data/'vehicle_traits.json').read_text(encoding='utf-8'))['vehicles']
    print(json.dumps({'stage':'full-data-audit'}),flush=True)
    validation=audit(data,manifest,catalog,traits)
    x=np.concatenate([load_shard(data,shard,'train')[0] for shard in manifest['shards']])
    mean=x.astype(np.float64).mean(axis=0).astype(np.float32);scale=x.astype(np.float64).std(axis=0).astype(np.float32)
    scale[scale<1e-6]=1
    stats=(mean,scale,x.min(axis=0),x.max(axis=0))
    del x
    net=preference_network(len(FEATURE_NAMES))
    print(json.dumps({'stage':'mlp-fit','features':len(FEATURE_NAMES),'epochs':epochs}),flush=True)
    history,epoch=fit(data,manifest,net,stats,epochs=epochs,batch_size=2048,seed=20261030)
    provenance={'dataset_version':manifest['version'],'dataset_manifest_sha256':file_hash(data/'manifest.json'),
                'validation_report_sha256':file_hash(data/'validation_report.json'),'data_dir':str(data.resolve()),
                'selected_epoch':epoch,'epochs':epochs,'selection':'lowest validation log loss; holdout evaluated after selection',
                'seed':20261030,'source_sha256':{str(path.relative_to(ROOT)):file_hash(path) for path in
                    (Path(__file__),ROOT/'ml/vehicle_matching/ui_scenario_features.py',ROOT/'ml/vehicle_matching/ui_scenario_model.py')}}
    model=UiScenarioRanker(net,stats,traits);model.save(output,provenance,data/'catalog.json',data/'vehicle_traits.json')
    saved=UiScenarioRanker.load(output)
    # Rebuild a held-out user's features through the production inference entry point.
    shard=manifest['shards'][0];user=read_rows(data/shard['directory']/'validation_profiles.jsonl')[0]
    with np.load(data/shard['directory']/'validation_choices.npz',allow_pickle=False) as rows:
        mask=rows['profile_ids']==user['id'];values=rows['features'][mask];cars=[catalog[int(i)] for i in rows['vehicle_indices'][mask]]
    if not np.array_equal(saved.score_features(values),saved.score_candidates(user,cars)):raise ValueError('Saved inference mismatch')
    results={'mlp':evaluate(saved.net,data,manifest,'test',*stats[:2]),'generator':validation['generator_test']}
    print(json.dumps({'stage':'mlp-test',**results['mlp']}),flush=True)
    torch.manual_seed(20261030);linear=nn.Linear(len(FEATURE_NAMES),1)
    linear_history,linear_epoch=fit(data,manifest,linear,stats,epochs=epochs,batch_size=2048,seed=20261030)
    results['linear']=evaluate(linear,data,manifest,'test',*stats[:2])
    torch.save(linear.state_dict(),output/'linear_baseline.pt')
    results['coin_flip']={'accuracy':.5,'log_loss':math.log(2)}
    quality=results['mlp']['accuracy']>.6 and results['mlp']['log_loss']<math.log(2)
    write_json(output/'training_report.json',{'training':provenance,'validation':validation,'partitions':manifest['partitions'],
        'results':results,'history':history,'linear_history':linear_history,'linear_selected_epoch':linear_epoch,
        'saved_inference':'passed','quality_gate':'passed' if quality else 'failed',
        'limitation':'Synthetic generated choices; these metrics do not measure real customer satisfaction.'})
    if not quality:raise ValueError('Training quality gate failed; do not deploy')
    print(json.dumps({'stage':'complete','quality_gate':'passed','results':results}),flush=True)


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--data',required=True,type=Path);parser.add_argument('--output',required=True,type=Path);parser.add_argument('--epochs',type=int,default=30)
    args=parser.parse_args();train(args.data,args.output,args.epochs)
