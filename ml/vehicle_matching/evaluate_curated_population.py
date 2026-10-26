"""Compare rankers on the same held-out mix of new and legacy inputs."""
import argparse
import json
import random
from collections import defaultdict
from pathlib import Path

from vehicle_matching.api import load_service
from vehicle_matching.train_preference_population import compare_models


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--data-dir',type=Path,required=True)
    parser.add_argument('--model-dir',type=Path,required=True);parser.add_argument('--baseline',type=Path,required=True)
    args=parser.parse_args();by_origin=defaultdict(list)
    with (args.data_dir/'test_profiles.jsonl').open(encoding='utf-8') as stream:
        for line in stream:
            record=json.loads(line);by_origin[record['origin']].append(record)
    rng=random.Random(20261026);sample=[];seen=set();origin_counts={}
    for origin,records in sorted(by_origin.items()):
        rng.shuffle(records);count=0
        for record in records:
            if record['group'] in seen:continue
            sample.append(record);seen.add(record['group']);count+=1
            if count==150:break
        origin_counts[origin]=count
    new=load_service(args.model_dir);old=load_service(args.baseline)
    result=compare_models(new.ranker,old.ranker,sample,new.vehicles,limit=len(sample))
    result['sample_origin_counts']=origin_counts
    (args.data_dir/'balanced_evaluation_report.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(result,ensure_ascii=False),flush=True)


if __name__=='__main__':main()
