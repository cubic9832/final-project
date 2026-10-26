"""Measure ranking information lost by inference score conversion."""
import csv,json,math,random
from collections import defaultdict
from pathlib import Path
import numpy as np
import torch
from vehicle_matching.api import load_service
from vehicle_matching.finance import Profile,assess
from vehicle_matching.preference_model import encode_preference
from vehicle_matching.train_preference_population import teacher

def main():
    root=Path('../data/households/synthetic/curated-current-v2-20261026')
    output=Path('outputs/reports/score-conversion-20261026');output.mkdir(parents=True,exist_ok=True)
    origins=defaultdict(list)
    for line in (root/'test_profiles.jsonl').open(encoding='utf-8'):
        r=json.loads(line);origins[r['origin']].append(r)
    rng=random.Random(20261026);sample=[];seen=set()
    for origin,records in sorted(origins.items()):
        rng.shuffle(records);count=0
        for r in records:
            if r['group'] in seen:continue
            sample.append(r);seen.add(r['group']);count+=1
            if count==150:break
    stats=defaultdict(lambda:defaultdict(list));examples=[]
    for name,folder in [('previous','20261026-100k-v1'),('combined','20261026-refined-v1')]:
        service=load_service(Path('outputs/models/candidate-preferences')/folder);model=service.ranker
        for r in sample:
            p=Profile(**r['profile']);eligible=[(v,assess(p,v)) for v in service.vehicles]
            eligible=[(v,c) for v,c in eligible if c['eligible']];cars=[v for v,c in eligible]
            targets=[teacher(p,v,c) for v,c in eligible]
            x=np.stack([encode_preference(p,v,model.assumptions,cost=c) for v,c in eligible])
            with torch.no_grad():
                raw=model.net(torch.from_numpy(((x-model.mean)/model.scale).astype(np.float32))).flatten()
                values={'raw':raw.numpy(),'sigmoid32':raw.sigmoid().numpy(),'sigmoid64':raw.double().sigmoid().numpy()}
            def order(scores):
                result=[];seen_models=set()
                for i in sorted(range(len(cars)),key=lambda i:(-float(scores[i]),cars[i].id)):
                    key=(cars[i].brand,cars[i].model)
                    if key not in seen_models:result.append(i);seen_models.add(key)
                    if len(result)==3:break
                return result
            def dcg(indices):return sum((2**targets[i]-1)/math.log2(j+2) for j,i in enumerate(indices))
            ideal=dcg(order(targets));raw_order=order(values['raw'])
            for mode,scores in values.items():
                ranked=order(scores);selected=[float(scores[i]) for i in ranked]
                measurements={'ndcg3':dcg(ranked)/ideal if ideal else 1,'top3_tie':float(len(set(selected))<len(selected)),
                              'changed_top3':float(ranked!=raw_order),'top_score_candidate_tie':float(sum(scores==max(scores))>1)}
                for origin in ('all',r['origin']):
                    for metric,value in measurements.items():stats[name+'|'+origin][mode+'|'+metric].append(value)
            if len(examples)<80 and name=='combined' and order(values['sigmoid32'])!=raw_order:
                for i in list(dict.fromkeys(raw_order+order(values['sigmoid32']))):
                    examples.append({'case':r['id'],'origin':r['origin'],'vehicle':cars[i].model,'vehicle_id':cars[i].id,
                                     'raw':float(values['raw'][i]),'sigmoid32':float(values['sigmoid32'][i]),
                                     'sigmoid64':float(values['sigmoid64'][i]),'teacher':targets[i]})
    report={key:{metric:float(np.mean(v)) for metric,v in metrics.items()} for key,metrics in stats.items()}
    (output/'report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    if examples:
        with (output/'examples.csv').open('w',encoding='utf-8-sig',newline='') as stream:
            writer=csv.DictWriter(stream,fieldnames=list(examples[0]));writer.writeheader();writer.writerows(examples)
    print(json.dumps(report,ensure_ascii=False,indent=2))

if __name__=='__main__':main()
