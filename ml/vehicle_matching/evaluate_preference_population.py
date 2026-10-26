"""Post-training holdout checks. Never used for checkpoint selection."""
import argparse
import json
import math
from pathlib import Path

import numpy as np
import torch

from vehicle_matching.api import load_service
from vehicle_matching.finance import Profile, assess
from vehicle_matching.train_preference_population import teacher, independent_eligible


def evaluate_population(directory,new_directory,old_directory):
    directory=Path(directory);new_directory=Path(new_directory)
    data=np.load(directory/'candidate_pairs.npz')
    new=load_service(new_directory);old=load_service(old_directory)
    pairs=data['pairs'];test_pairs=pairs[data['splits'][pairs[:,0]]==2]
    x=data['features']
    torch.set_num_threads(2)
    with torch.no_grad():
        a,b=test_pairs.T
        left=new.ranker.net(torch.from_numpy(((x[a]-new.ranker.mean)/new.ranker.scale).astype(np.float32))).flatten()
        right=new.ranker.net(torch.from_numpy(((x[b]-new.ranker.mean)/new.ranker.scale).astype(np.float32))).flatten()
        pair_accuracy=float((left>right).float().mean())
    generation=json.loads((directory/'generation_report.json').read_text(encoding='utf-8'))
    held={tuple(key) for key in generation['held_out_models']}
    held_cars=[v for v in new.vehicles if (v.brand,v.model) in held]
    records=[json.loads(line) for line in (directory/'profiles.jsonl').read_text(encoding='utf-8').splitlines()]
    evaluated=set();metrics={'new':[],'old':[]}
    for record in records:
        if record['split']!='test' or record['group'] in evaluated:continue
        evaluated.add(record['group'])
        profile=Profile(**record['profile'])
        candidates=[(v,assess(profile,v)) for v in held_cars]
        candidates=[(v,c) for v,c in candidates if c['eligible']]
        if candidates:
            vehicles=[v for v,c in candidates]
            targets=[teacher(profile,v,c) for v,c in candidates]
            def order(values):
                seen=set();result=[]
                for i in sorted(range(len(vehicles)),key=lambda i:(-values[i],vehicles[i].id)):
                    key=(vehicles[i].brand,vehicles[i].model)
                    if key not in seen:seen.add(key);result.append(i)
                    if len(result)==3:break
                return result
            def dcg(indices):return sum((2**targets[i]-1)/math.log2(j+2) for j,i in enumerate(indices))
            ideal=dcg(order(targets))
            for name,service in (('new',new),('old',old)):
                predictions,_=service.ranker.predict(profile,vehicles)
                metrics[name].append(dcg(order(predictions))/ideal if ideal else 1)
        if len(evaluated)==300:break
    boundaries=[]
    for income,expenses,cash in ((0,1000000,0),(0,1000000,100000000),(2000000,2000000,100000000),
                                  (2000000,2200000,100000000),(10000000,1000000,1000000)):
        profile=Profile(monthly_income=income,monthly_expenses=expenses,existing_monthly_payment=0,
                        liquid_assets=cash,down_payment=0,emergency_reserve=0,monthly_savings=0,
                        annual_distance=15000,months=0,annual_rate=0,financing_mode='recommendation')
        result=new.recommend(profile,k=9)
        for row in result['recommendations']:
            vehicle=next(v for v in new.vehicles if v.id==row['vehicle']['id'])
            assert independent_eligible(profile,vehicle,row['cost'])
            assert math.isfinite(row['integratedScore']['total'])
        if cash<=1000000:assert not result['recommendations']
        else:assert result['recommendations']
        boundaries.append({'income':income,'expenses':expenses,'cash':cash,'recommendations':len(result['recommendations'])})
    result={'test_comparison_pairs':len(test_pairs),'test_pair_accuracy':pair_accuracy,
            'unseen_vehicle_models':len(held),'unseen_evaluation_profiles':len(evaluated),
            'unseen_profiles_with_candidates':len(metrics['new']),
            'unseen_standalone_ndcg_at_3':{key:float(np.mean(values)) for key,values in metrics.items()},
            'financial_boundary_cases':boundaries,'financial_violations':0,
            'meaning':'Current synthetic teacher agreement, not observed user satisfaction'}
    (new_directory/'holdout_report.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
    return result


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('data');p.add_argument('new');p.add_argument('old');args=p.parse_args()
    print(json.dumps(evaluate_population(args.data,args.new,args.old),ensure_ascii=False,indent=2))
