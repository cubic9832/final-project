"""Train an isolated MLP baseline on the completed preference dataset."""
import csv
import argparse
import hashlib
import json
import subprocess
import time
from collections import Counter
from datetime import datetime
from pathlib import Path

import numpy as np
import torch

from legacy.recommender.models.mlp import MlpConfig, MlpRanker
from legacy.recommender.preprocessing import PreparedSplit
from tools.data.households.extend_training_preferences import FEATURES, PREFERENCES, ROOT
from tools.data.households.complete_preference_choices import context_from_row
from tools.data.households.quality_choice_policy import QualityPolicy
from vehicle_matching.catalog import read_catalog

DATA = ROOT/'data/households/synthetic/preference-financial-v4'
NUMERIC = (*FEATURES[:7],PREFERENCES[0],PREFERENCES[3], '월저축액_원','비상자금_원',
           '구매투입가능자금_원','최소월여유자금_원','구매가격상한_원_0이면미지정')
CATEGORIES = (FEATURES[7],PREFERENCES[1],PREFERENCES[2])
OPTIONAL_NUMERIC=('공간중요도_1부터5','연료중요도_1부터5','탑승인원중요도_1부터5','용도중요도_1부터5')


def prepare(rows):
    train = rows['학습']
    numeric_columns=NUMERIC+tuple(k for k in OPTIONAL_NUMERIC if all(k in row for row in train))
    labels = sorted({r['선택차량_라벨코드'] for r in train})
    vocab = [sorted({r[k] for r in train}) for k in CATEGORIES]
    values = np.log1p(np.array([[int(r[k]) for k in numeric_columns] for r in train]))
    mean, scale = values.mean(0), values.std(0)
    scale[scale<1e-8]=1
    metadata = {'numeric':numeric_columns,'categorical':CATEGORIES,'labels':labels,'vocabularies':vocab,
                'log1p_mean':mean.tolist(),'log1p_scale':scale.tolist()}
    return {split:transform(part,metadata) for split,part in rows.items()}, metadata


def transform(rows, metadata):
    values = np.log1p(np.array([[int(r[k]) for k in metadata['numeric']] for r in rows]))
    numeric = ((values-np.array(metadata['log1p_mean']))/np.array(metadata['log1p_scale'])).astype(np.float32)
    categorical = np.array([[{v:i+1 for i,v in enumerate(vocab)}.get(r[key],0)
                             for key,vocab in zip(metadata['categorical'],metadata['vocabularies'])] for r in rows],dtype=np.int64)
    lookup = {v:i for i,v in enumerate(metadata['labels'])}
    target = np.array([lookup[r['선택차량_라벨코드']] for r in rows],dtype=np.int64)
    return PreparedSplit(numeric,categorical,tuple(len(v)+1 for v in metadata['vocabularies']),len(lookup),target)


def metrics(probabilities, targets):
    order = np.argsort(-probabilities,axis=1)
    prediction = order[:,0]
    recalls = [float(np.mean(prediction[targets==c]==c)) for c in np.unique(targets)]
    return {'rows':len(targets),'top1':float(np.mean(prediction==targets)),
            'top3':float(np.mean(np.any(order[:,:3]==targets[:,None],axis=1))),
            'macro_recall':float(np.mean(recalls)),
            'log_loss':float(-np.log(np.maximum(probabilities[np.arange(len(targets)),targets],1e-12)).mean())}


def evaluate_constraints(rows, probabilities, labels, data=DATA, cohorts=None):
    financial_only=data.name=='preference-financial-v4'
    if financial_only:
        from tools.data.households.financial_choice_policy import FinancialChoicePolicy
        policy=FinancialChoicePolicy(read_catalog(data/'catalog.json'))
    else:
        policy = QualityPolicy(read_catalog(data/'catalog.json'))
    with (data/'vehicle_identity_map.csv').open(encoding='utf-8-sig',newline='') as source:
        mapping = {r['차량사양번호']:r['선택차량_라벨코드'] for r in csv.DictReader(source)}
    label_index = {v:i for i,v in enumerate(labels)}
    vehicle_labels = np.array([label_index.get(mapping[v.id],-1) for v in policy.vehicles])
    groups = [np.flatnonzero(vehicle_labels==i) for i in range(len(labels))]
    stats, raw_counts, filtered_counts = Counter(),Counter(),Counter()
    filtered_probabilities = []
    examples=[]
    cohort_counts={}
    for index,(row,probs) in enumerate(zip(rows,probabilities)):
        context = context_from_row(row)
        pool,reason = policy.pool(row,context)
        if pool is None: raise AssertionError(reason)
        scores=pool['scores'] if financial_only else policy.evaluate(row,context)[0]
        predicted = int(np.argmax(probs))
        raw_counts[labels[predicted]]+=1
        stats['raw_no_hard_valid_trim']+=not bool(np.any(np.isfinite(scores[groups[predicted]])))
        acceptable = np.array([np.any(np.isfinite(pool['scores'][g])) for g in groups])
        stats['raw_outside_preferred_quality_pool']+=not bool(acceptable[predicted])
        if cohorts is not None:
            counter=cohort_counts.setdefault(cohorts[index],Counter())
            counter['rows']+=1
            counter['raw_no_hard_valid_trim']+=not bool(np.any(np.isfinite(scores[groups[predicted]])))
            counter['raw_outside_preferred_quality_pool']+=not bool(acceptable[predicted])
        near = np.zeros(len(labels),dtype=bool)
        for model in pool['shortlist']:
            label = vehicle_labels[policy.starts[model]]
            if label>=0: near[label]=True
        masked = np.where(near,probs,0)
        if not masked.sum(): raise AssertionError('No modeled qualified near-best candidate')
        masked/=masked.sum()
        filtered_probabilities.append(masked)
        selected = int(np.argmax(masked))
        filtered_counts[labels[selected]]+=1
        stats['filtered_outside_preferred_quality_pool']+=not bool(acceptable[selected])
        if len(examples)<20 and not acceptable[predicted]:
            examples.append({'profile':row['프로필_식별자'],'target':row['선택차량_라벨코드'],
                             'raw_prediction':labels[predicted],'filtered_prediction':labels[selected]})
        if (index+1)%10000==0: print(f'Constraint evaluation {index+1}/{len(rows)}',flush=True)
    return np.array(filtered_probabilities), {'counts':stats,'raw_prediction_counts':raw_counts,
              'filtered_prediction_counts':filtered_counts,'examples':examples,'by_cohort':cohort_counts,
              'interpretation':('Only monetary eligibility is masked; all financially eligible models remain regardless of score, preferences or probability. Requires explicit trim selection before serving.' if financial_only else
                                'A model is hard-valid if at least one trim passes finance/seats/price. Quality mask also enforces generator preference tier and near-best shortlist; requires explicit trim selection before serving.')}


def run(data=DATA, baseline_run=None):
    if subprocess.check_output(['git','branch','--show-current'],cwd=ROOT,text=True).strip()!='ml/test':
        raise ValueError('Run only on ml/test')
    started=time.time()
    main = subprocess.check_output(['git','rev-parse','main'],cwd=ROOT,text=True).strip()
    data=Path(data).resolve()
    path=data/'combined_training.csv'
    digest=hashlib.sha256(path.read_bytes()).hexdigest()
    rows={s:[] for s in ('학습','검증','평가')}
    with path.open(encoding='utf-8-sig',newline='') as source:
        for row in csv.DictReader(source): rows[row['데이터_구분']].append(row)
    splits,metadata=prepare(rows)
    directory=ROOT/'ml/outputs/models'/data.name/datetime.now().strftime('%Y%m%dT%H%M%S')
    directory.mkdir(parents=True,exist_ok=False)
    torch.set_num_threads(4)
    config=MlpConfig(hidden=(128,64),dropout=.1,lr=.001,epochs=30,batch_size=512,seed=42)
    model=MlpRanker(config)
    print('Training MLP: '+str({s:len(r) for s,r in rows.items()}),flush=True)
    model.fit(splits['학습'],splits['검증'])
    model.save(directory)
    (directory/'preprocessor.json').write_text(json.dumps(metadata,ensure_ascii=False,indent=2),encoding='utf-8')
    print(f'Training complete; selected epoch {model.selected_epoch}',flush=True)
    report={'model':config.to_dict(),'selected_epoch':model.selected_epoch,'epochs':model.epoch_history,
            'dataset':str(path),'dataset_sha256':digest,'main_ref':main,'label_count':len(metadata['labels']),
            'input_columns':list(metadata['numeric'])+list(CATEGORIES),'metrics':{}}
    for split,prepared in splits.items():
        report['metrics'][split]=metrics(model.predict_proba(prepared),prepared.labels)
    probs=model.predict_proba(splits['평가'])
    np.savez_compressed(directory/'evaluation_predictions.npz',probabilities=probs,targets=splits['평가'].labels)
    provenance={}
    if (data/'additional_provenance.csv').is_file():
        with (data/'additional_provenance.csv').open(encoding='utf-8-sig',newline='') as source:
            provenance={r['프로필_식별자']:r['생성유형'] for r in csv.DictReader(source)}
    cohorts=[provenance.get(r['프로필_식별자'],'기존평가') for r in rows['평가']]
    filtered,constraints=evaluate_constraints(rows['평가'],probs,metadata['labels'],data,cohorts)
    report['constraints']=constraints
    report['filtered_evaluation']=metrics(filtered,splits['평가'].labels)
    frequencies=np.bincount(splits['학습'].labels,minlength=len(metadata['labels'])).astype(float)
    baseline=np.tile(frequencies/frequencies.sum(),(len(probs),1))
    report['frequency_baseline']=metrics(baseline,splits['평가'].labels)
    report['evaluation_subgroups']={}
    for kind in sorted({r['평가유형'] for r in rows['평가']}):
        mask=np.array([r['평가유형']==kind for r in rows['평가']])
        report['evaluation_subgroups'][kind]={'raw':metrics(probs[mask],splits['평가'].labels[mask]),
                                              'filtered':metrics(filtered[mask],splits['평가'].labels[mask])}
    per_label=[]
    prediction=probs.argmax(1)
    for i,label in enumerate(metadata['labels']):
        mask=splits['평가'].labels==i
        per_label.append({'label':label,'model':next(r['선택차량_모델'] for r in rows['학습'] if r['선택차량_라벨코드']==label),
                          'train_rows':int(frequencies[i]),'evaluation_rows':int(mask.sum()),
                          'raw_recall':float(np.mean(prediction[mask]==i)) if mask.any() else None,
                          'raw_predicted_rows':int(np.sum(prediction==i))})
    report['per_label']=per_label
    report['evaluation_cohorts']={}
    old_probabilities=None
    if baseline_run is not None:
        baseline_run=Path(baseline_run)
        old_metadata=json.loads((baseline_run/'preprocessor.json').read_text(encoding='utf-8'))
        if old_metadata['labels']!=metadata['labels']: raise ValueError('Baseline label order differs')
        old_model=MlpRanker.load(baseline_run)
        old_probabilities=old_model.predict_proba(transform(rows['평가'],old_metadata))
        report['baseline_run']=str(baseline_run)
    for cohort in sorted(set(cohorts)):
        mask=np.array([c==cohort for c in cohorts])
        target=splits['평가'].labels[mask]
        entry={'raw':metrics(probs[mask],target),'filtered':metrics(filtered[mask],target),
               'constraints':constraints['by_cohort'][cohort]}
        if old_probabilities is not None: entry['previous_model_raw']=metrics(old_probabilities[mask],target)
        report['evaluation_cohorts'][cohort]=entry
    report['evaluation_note']='Original evaluation informed data development. Coverage evaluation is deliberately oversampled; compare cohorts separately. Single seed baseline, no production deployment.'
    report['elapsed_seconds']=round(time.time()-started,1)
    assert hashlib.sha256(path.read_bytes()).hexdigest()==digest
    assert subprocess.check_output(['git','rev-parse','main'],cwd=ROOT,text=True).strip()==main
    report['data_and_main_unchanged']=True
    (directory/'report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    assert np.allclose(MlpRanker.load(directory).predict_proba(splits['검증']),model.predict_proba(splits['검증']))
    print(json.dumps({'directory':str(directory),'metrics':report['metrics'],'filtered':report['filtered_evaluation'],
                      'constraints':constraints['counts'],'seconds':report['elapsed_seconds']},ensure_ascii=True,indent=2),flush=True)


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--data-dir',type=Path,default=DATA)
    parser.add_argument('--baseline-run',type=Path)
    args=parser.parse_args()
    run(args.data_dir,args.baseline_run)
