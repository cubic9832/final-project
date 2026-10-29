"""Train/evaluate the scenario contract using validation-only checkpoint selection."""
import argparse
import json
import math
from pathlib import Path
import sys
import time

import numpy as np
import torch
from torch import nn

from vehicle_matching.catalog import ROOT, read_catalog
from vehicle_matching.finance import Profile, assess
from vehicle_matching.preference_model import PreferenceRanker, preference_network
from vehicle_matching.scenario_features import CHANNELS, FEATURE_NAMES, encode_scenario
from vehicle_matching.scenario_model import ScenarioRanker
from vehicle_matching.train_behavioral_choices import evaluate, evaluate_rules, fit, load_shard
from tools.data.households.audit_scenario_population import audit, read_jsonl
from tools.data.households.generate_scenario_population import file_hash, write_json


def normalization(data,manifest):
    count = 0
    sums = np.zeros(len(FEATURE_NAMES),dtype=np.float64)
    squares = np.zeros_like(sums)
    minimum,maximum = np.full_like(sums,np.inf),np.full_like(sums,-np.inf)
    for shard in manifest['shards']:
        x,_,_ = load_shard(data,shard,'train')
        if not len(x):
            continue
        if x.shape[1]!=len(FEATURE_NAMES):
            raise ValueError('Scenario feature count mismatch')
        values = x.astype(np.float64)
        count += len(x); sums += values.sum(axis=0); squares += np.square(values).sum(axis=0)
        minimum = np.minimum(minimum,values.min(axis=0)); maximum = np.maximum(maximum,values.max(axis=0))
    if not count:
        raise ValueError('Empty training partition')
    mean = sums/count
    scale = np.sqrt(np.maximum(0,squares/count-mean**2)); scale[scale<1e-6] = 1
    return tuple(v.astype(np.float32) for v in (mean,scale,minimum,maximum))


def generator_baseline(data,manifest):
    count,loss,brier,correct,expected = 0,0.,0.,0.,0.
    for shard in manifest['shards']:
        directory = data/shard['directory']
        for choice,record in zip(read_jsonl(directory/'test_choices.jsonl'),read_jsonl(directory/'test_audit.jsonl')):
            p = min(1-1e-12,max(1e-12,record['probability_a'])); label = choice['label']
            loss -= label*math.log(p)+(1-label)*math.log1p(-p)
            brier += (p-label)**2; correct += int((p>=.5)==bool(label)); expected += max(p,1-p); count += 1
    return {'comparisons':count,'log_loss':loss/count,'brier_score':brier/count,'accuracy':correct/count,
            'expected_accuracy':expected/count,'evaluation_only':True}


def verify_saved_inference(ranker,data,manifest):
    catalog = read_catalog(data/'catalog.json')
    for shard in manifest['shards']:
        directory = data/shard['directory']
        users = read_jsonl(directory/'validation_profiles.jsonl')
        if not users:
            continue
        user = users[0]
        with np.load(directory/'validation_choices.npz',allow_pickle=False) as arrays:
            positions = np.flatnonzero(arrays['profile_ids']==user['id'])
            features = arrays['features'][positions]
            cars = [catalog[int(i)] for i in arrays['vehicle_indices'][positions]]
        direct = np.asarray(ranker.score_features(features))
        inferred = np.asarray(ranker.score_candidates(user,cars))
        if not np.array_equal(direct,inferred):
            raise ValueError('Saved model inference differs from training encoding')
        return {'status':'passed','profile_id':user['id'],'candidates':len(cars),
                'maximum_score_difference':float(np.max(np.abs(direct-inferred)))}
    raise ValueError('No validation user available for inference check')


def train(data,output,*,epochs=30,batch_size=2048,seed=20261029,threads=4,old_model=None):
    data,output = Path(data),Path(output)
    if min(epochs,batch_size,threads)<=0:
        raise ValueError('Positive epochs, batch size and threads required')
    if output.exists():
        raise FileExistsError(output)
    manifest = json.loads((data/'manifest.json').read_text(encoding='utf-8'))
    if manifest['version'] not in ('scenario-population-v1','scenario-population-v2','scenario-population-v3') or manifest['feature_names']!=list(FEATURE_NAMES):
        raise ValueError('Unsupported scenario dataset contract')
    print(json.dumps({'stage':'full-data-audit'}),flush=True)
    validation = audit(data)
    if not all(manifest['partitions'][role]['comparisons']>0 for role in ('train','validation','test')):
        raise ValueError('All partitions must contain comparisons')
    protected = {p.name:file_hash(p) for p in Path(old_model).iterdir() if p.is_file()} if old_model else {}
    started = time.monotonic()
    torch.set_num_threads(threads); torch.manual_seed(seed); torch.use_deterministic_algorithms(True)
    stats = normalization(data,manifest)
    net = preference_network(len(FEATURE_NAMES))
    print(json.dumps({'stage':'mlp-fit','features':len(FEATURE_NAMES),'epochs':epochs}),flush=True)
    history,epoch = fit(data,manifest,net,stats,epochs=epochs,batch_size=batch_size,seed=seed)
    provenance = {'dataset_version':manifest['version'],'data_dir':str(data.resolve()),
        'dataset_manifest_sha256':file_hash(data/'manifest.json'),'validation_report_sha256':file_hash(data/'validation_report.json'),
        'objective':'BCEWithLogits(score_A-score_B, sampled_choice_A)','selected_epoch':epoch,
        'selection':'lowest validation log_loss; test is evaluated after checkpoint selection',
        'epochs':epochs,'batch_size':batch_size,'seed':seed,'architecture':[len(FEATURE_NAMES),64,32,1],
        'initialization':'fresh weights; legacy 52-input weights are not compatible',
        'runtime':{'python':sys.version,'torch':torch.__version__,'numpy':np.__version__,'device':'cpu','threads':threads},
        'source_hashes':{str(p.relative_to(ROOT)):file_hash(p) for p in (
            Path(__file__),ROOT/'ml/vehicle_matching/scenario_model.py',ROOT/'ml/vehicle_matching/scenario_features.py',
            ROOT/'ml/vehicle_matching/train_behavioral_choices.py')}}
    ScenarioRanker(net,*stats).save(output,provenance,data/'catalog.json')
    saved = ScenarioRanker.load(output)
    inference = verify_saved_inference(saved,data,manifest)
    results = {'mlp':evaluate(saved.net,data,manifest,'test',saved.mean,saved.scale,batch_size)}
    print(json.dumps({'stage':'mlp-test',**results['mlp']}),flush=True)
    torch.manual_seed(seed)
    linear = nn.Linear(len(FEATURE_NAMES),1)
    print(json.dumps({'stage':'linear-fit','epochs':epochs}),flush=True)
    linear_history,linear_epoch = fit(data,manifest,linear,stats,epochs=epochs,batch_size=batch_size,seed=seed)
    results['linear'] = evaluate(linear,data,manifest,'test',*stats[:2],batch_size)
    torch.save({'state_dict':linear.state_dict(),'features':list(FEATURE_NAMES),'mean':stats[0].tolist(),
                'scale':stats[1].tolist(),'selected_epoch':linear_epoch},output/'linear_baseline.pt')
    results.update(evaluate_rules(data,manifest))
    results['generator_probability'] = generator_baseline(data,manifest)
    if old_model:
        old = PreferenceRanker.load(old_model)
        previous = evaluate(old.net,data,manifest,'test',old.mean,old.scale,batch_size)
        results['previous_52_feature_checkpoint'] = {'comparisons':previous['comparisons'],'accuracy':previous['accuracy'],
                                                    'probability_calibration':'not calibrated to this dataset'}
    results['coin_flip'] = {'comparisons':manifest['partitions']['test']['comparisons'],'expected_accuracy':.5,
                           'log_loss':math.log(2),'brier_score':.25}
    if old_model and protected!={p.name:file_hash(p) for p in Path(old_model).iterdir() if p.is_file()}:
        raise ValueError('Protected previous checkpoint changed during training')
    report = {'training':provenance,'data_validation':validation,'partitions':manifest['partitions'],
              'history':history,'linear_history':linear_history,'linear_selected_epoch':linear_epoch,'test':results,
              'saved_inference_verification':inference,'seconds_after_data_audit':round(time.monotonic()-started,2),
              'previous_checkpoint_protection':{'status':'passed' if old_model else 'not-requested','files_sha256':protected},
              'service_activation':'not performed'}
    write_json(output/'training_report.json',report)
    write_json(output/'inference_verification.json',inference)
    print(json.dumps({'stage':'training-complete','output':str(output.resolve()),'test':results}),flush=True)
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--data',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--epochs',type=int,default=30)
    parser.add_argument('--batch-size',type=int,default=2048)
    parser.add_argument('--seed',type=int,default=20261029)
    parser.add_argument('--threads',type=int,default=4)
    parser.add_argument('--old-model',type=Path)
    args = parser.parse_args()
    train(args.data,args.output,epochs=args.epochs,batch_size=args.batch_size,seed=args.seed,threads=args.threads,old_model=args.old_model)


if __name__=='__main__':
    main()
