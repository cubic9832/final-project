"""Fit controlled-cohort policy scores, select on validation, test after reload."""
import argparse
import copy
import json
from pathlib import Path
import numpy as np
import torch
from tools.data.households.generate_preference_cohorts import audit_saved
from vehicle_matching.cohort_model import AXES, SCHEMA, CohortRanker, inputs, network
from vehicle_matching.lifestyle_model import digest


def load_rows(data):
    arrays = {role:[] for role in ('train','validation','test')}
    with (data/'comparisons.jsonl').open(encoding='utf-8') as stream:
        for line in stream:
            row = json.loads(line)
            axis = AXES.index(row['axis'])
            for profile in row['profiles']:
                for vehicle in profile['ranking']:
                    arrays[row['split']].append((axis,vehicle['policy_score'],1/len(profile['ranking'])))
    result = {}
    for role,rows in arrays.items():
        if not rows:
            raise ValueError('Empty cohort split: '+role)
        raw = np.asarray(rows,dtype=np.float32)
        x = np.zeros((len(raw),7),dtype=np.float32)
        x[np.arange(len(raw)),raw[:,0].astype(int)] = 1
        x[:,-1] = raw[:,1]
        result[role] = (torch.from_numpy(x),torch.from_numpy(raw[:,1]),torch.from_numpy(raw[:,2]))
    return result


def metrics(net,rows):
    with torch.inference_mode():
        x,y,w = rows
        prediction = net(x).flatten()
        return {'rows':len(y),'weighted_mae':float((abs(prediction-y)*w).sum()/w.sum()),
                'weighted_mse':float(((prediction-y)**2*w).sum()/w.sum())}


def ranking_metrics(net,data):
    totals = {}
    with torch.inference_mode(), (data/'comparisons.jsonl').open(encoding='utf-8') as stream:
        for line in stream:
            row = json.loads(line)
            if row['split']!='test':
                continue
            axis = AXES.index(row['axis'])
            stats = totals.setdefault(row['axis'],{'profiles':0,'top_set_agreement':0,'adjacent_order_correct':0,'adjacent_order_pairs':0})
            for profile in row['profiles']:
                ranking = profile['ranking']
                predicted = net(torch.from_numpy(inputs(axis,[r['policy_score'] for r in ranking]))).flatten().numpy()
                expected_top = {r['vehicle_id'] for r in ranking if r['rank']==1}
                actual_top = {r['vehicle_id'] for r,p in zip(ranking,predicted) if abs(float(p)-float(predicted.max()))<1e-6}
                stats['profiles']+=1
                stats['top_set_agreement']+=expected_top==actual_top
                for i in range(len(ranking)-1):
                    if ranking[i]['policy_score']>ranking[i+1]['policy_score']:
                        stats['adjacent_order_pairs']+=1
                        stats['adjacent_order_correct']+=bool(predicted[i]>predicted[i+1])
    for stats in totals.values():
        stats['top_set_agreement']/=stats['profiles']
        stats['adjacent_order_accuracy']=stats['adjacent_order_correct']/max(1,stats['adjacent_order_pairs'])
    return totals


def train(data,output,epochs=20):
    if output.exists():
        raise FileExistsError(output)
    audit = audit_saved(data)
    torch.set_num_threads(2)
    torch.manual_seed(20261028)
    rows = load_rows(data)
    net = network()
    optimizer = torch.optim.Adam(net.parameters(),lr=.003)
    history,best,state,selected = [],float('inf'),None,0
    x,y,w = rows['train']
    for epoch in range(epochs):
        net.train()
        for batch in torch.randperm(len(y)).split(4096):
            prediction = net(x[batch]).flatten()
            loss = (((prediction-y[batch])**2)*w[batch]).sum()/w[batch].sum()
            optimizer.zero_grad();loss.backward();optimizer.step()
        validation = metrics(net,rows['validation'])
        history.append({'epoch':epoch+1,'validation':validation})
        print(json.dumps(history[-1]),flush=True)
        if validation['weighted_mse']<best:
            best,state,selected = validation['weighted_mse'],copy.deepcopy(net.state_dict()),epoch+1
    net.load_state_dict(state)
    output.mkdir(parents=True)
    torch.save(net.state_dict(),output/'model.pt')
    (output/'catalog.json').write_bytes((data/'catalog.json').read_bytes())
    traits = json.loads((data/'vehicle_traits.json').read_text(encoding='utf-8'))
    (output/'vehicle_traits.json').write_text(json.dumps({'vehicles':traits},ensure_ascii=False),encoding='utf-8')
    metadata = {'schema':SCHEMA,'axes':AXES,'weights_sha256':digest(output/'model.pt'),
        'training':{'data_dir':str(data.resolve()),'selected_epoch':selected,'objective':'candidate-count-balanced MSE on controlled synthetic policy scores',
            'catalog_sha256':digest(output/'catalog.json'),'traits_sha256':digest(output/'vehicle_traits.json'),
            'dataset_files':{name:digest(data/name) for name in ('generation_report.json','comparisons.jsonl','rankings.csv')},
            'trainer_sha256':digest(Path(__file__))}}
    (output/'metadata.json').write_text(json.dumps(metadata,ensure_ascii=False,indent=2),encoding='utf-8')
    saved = CohortRanker.load(output)
    report = {'selected_epoch':selected,'history':history,'test':metrics(saved.net,rows['test']),
        'test_rankings':ranking_metrics(saved.net,data),'audit':audit,
        'scope':'Synthetic policy imitation on unseen financial groups; vehicles/trait grid are shared across splits. Not human preference accuracy.',
        'composition':'Independent learned feature scores combined by explicit importance; fuel/size use supplementary match rules, not learned cohort labels.'}
    (output/'training_report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps({'output':str(output),'test':report['test'],'rankings':report['test_rankings']}),flush=True)
    return report


if __name__=='__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--data',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--epochs',type=int,default=20)
    args = parser.parse_args()
    train(args.data,args.output,args.epochs)
