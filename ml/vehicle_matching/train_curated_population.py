"""Train directly from the final classified arrays, without retired raw inputs."""
import argparse
import json
import shutil
from pathlib import Path

import numpy as np

from vehicle_matching.catalog import catalog_fingerprint
from vehicle_matching.partition_preference_population import digest
from vehicle_matching.train_preference_population import fit_population


def load_partitions(directory):
    parts=[];offset=0;pairs=[]
    for code,role in enumerate(('train','validation','test')):
        with np.load(directory/f'{role}_pairs.npz') as saved:
            part={key:saved[key].copy() for key in ('features','targets','pairs','splits','profile_ids')}
        if not len(part['pairs']) or not np.all(part['splits']==code):
            raise ValueError(f'Invalid {role} partition')
        if not np.all(part['profile_ids'][part['pairs'][:,0]]==part['profile_ids'][part['pairs'][:,1]]):
            raise ValueError('A comparison crosses profiles')
        pairs.append(part['pairs']+offset);offset+=len(part['features']);parts.append(part)
    groups=[set(part['profile_ids'].tolist()) for part in parts]
    if any(groups[a]&groups[b] for a in range(3) for b in range(a)):
        raise ValueError('Profiles cross partitions')
    return tuple(np.concatenate([part[key] for part in parts]) for key in ('features','targets'))+(np.concatenate(pairs),np.concatenate([part['splits'] for part in parts]))


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--data-dir',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--epochs',type=int,default=12)
    args=parser.parse_args()
    if args.output.exists():raise ValueError('Use a new output directory')
    report=json.loads((args.data_dir/'refinement_report.json').read_text(encoding='utf-8'))
    for name,expected in report['output_hashes'].items():
        if digest(args.data_dir/name)!=expected:raise ValueError(f'Data hash differs: {name}')
    x,y,pairs,splits=load_partitions(args.data_dir)
    provenance={'catalog_sha256':catalog_fingerprint(args.data_dir/'catalog.json'),
                'data_dir':str(args.data_dir.resolve()),'policy':report['policy'],
                'split_counts':report['comparison_partitions'],'seed':report['seed']}
    model,history=fit_population(x,y,pairs,splits,report['seed'],args.epochs,args.output,provenance)
    shutil.copyfile(args.data_dir/'catalog.json',args.output/'catalog.json')
    (args.output/'training_report.json').write_text(json.dumps({'history':history,'data':provenance},ensure_ascii=False,indent=2),encoding='utf-8')


if __name__=='__main__':main()
