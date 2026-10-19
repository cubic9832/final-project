from tools.data.households.paths import SYNTHETIC_ROOT

"""Separate imported-owner dataset, sharing existing schemas and financial rules."""
import hashlib
import json
import random
from collections import Counter
from pathlib import Path

ROOT=SYNTHETIC_ROOT / 'imported-owners'
PARENT=ROOT.parent
from tools.data.households.generate_owner_population import generate_population,summarize_owners
from tools.data.households.refine_owner_purchases import refine_population


def load_json(path):return json.loads(path.read_text(encoding='utf-8'))


def snapshot_domestic():
    return {str(p):hashlib.sha256(p.read_bytes()).hexdigest() for folder in ['owner-funded','owner-population','ownership','generated']
            for p in (PARENT/folder).rglob('*') if p.is_file()}


def inventory_from_catalog(catalog):
    result=[]
    for model in catalog['models']:
        for trim,powertrain,fuel,price,source,year in model['variants']:
            result.append({'brand':model['brand'],'model':model['model'],'canonical_model':model['model'],
                           'label_code':model['code'],'body':model['body'],'segment':model['segment'],
                           'trim':trim,'powertrain':powertrain,'fuel':fuel,'price_won':price,'model_year':year,
                           'source_url':catalog['sources'][source],'source_page':1 if source=='bmw' else None,
                           'verified_options':[],'configuration_id':f'IMP-C{len(result)+1:03d}',
                           'source_level':'secondary' if source=='tesla' else 'manufacturer',
                           'source_period_note':catalog['price_period_notes'][source]})
    return result


def create_dataset(settings,catalog,inventory):
    population_config=load_json(PARENT/'owner_population_config.json')
    population_config.update({'count':settings['candidate_count'],'seed':settings['seed'],
                              'groups':settings['group_overrides'],'version':settings['version']})
    people,_=generate_population(population_config,catalog['models'])
    finance_config=load_json(PARENT/'purchase_refinement_config.json')
    finance_config['version']=settings['version']
    selected=[];audit=[];counts=Counter();rejected=Counter()
    for i,p in enumerate(people):
        code=p['보유차량_라벨코드']
        if counts[code]>=settings['owners_per_model']:continue
        finance_config['seed']=settings['seed']+i
        variants=[v for v in inventory if v['label_code']==code]
        try:
            row_list,audit_list=refine_population([p],variants,finance_config)
        except ValueError as error:
            if 'No consistent purchase' not in str(error):raise
            rejected['no_consistent_purchase']+=1;continue
        row=row_list[0];details=audit_list[0]
        pid=f"P{settings['profile_id_start']+len(selected):06d}"
        row['프로필_식별자']=pid;details['프로필_식별자']=pid
        row['난수_시드']=settings['seed']
        row['라벨_근거']='가격자금보정_가상수입차보유자분포'
        selected.append(row);audit.append(details);counts[code]+=1
    if any(counts[m['code']]!=settings['owners_per_model'] for m in catalog['models']):
        raise ValueError('Insufficient feasible candidates: '+str(counts))
    split_indices=list(range(len(selected)));random.Random(settings['seed']+100).shuffle(split_indices)
    for j,idx in enumerate(split_indices):selected[idx]['데이터_구분']='학습' if j<len(selected)*.7 else '검증' if j<len(selected)*.85 else '평가'
    return selected,audit,dict(rejected)


def validate(rows,audit,catalog,inventory):
    template=list(load_json(PARENT/'owner-funded/learning-rows.json')[0])
    audit_template=list(load_json(PARENT/'owner-funded/purchase-audit.json')[0])
    source={v['configuration_id']:v for v in inventory}
    for row,a in zip(rows,audit):
        assert list(row)==template and list(a)==audit_template
        assert 20<=row['나이_세']<=59
        assert row['프로필_식별자']==a['프로필_식별자']
        assert row['보유차량_모델']==a['구매_모델']
        assert a['총구매비용_가정_원']==a['기본가격_원']+a['옵션가격_원']+a['등록비_가정_원']
        assert a['총구매비용_가정_원']==a['본인구매자금_원']+a['가족지원금_가정_원']+a['차량할부원금_원']
        assert a['구매직전_현금_원']-a['본인구매자금_원']==row['개인_현금성자산_원']
        assert a['기본가격_원']==source[a['차량사양_식별자']]['price_won']
        assert row['개인_대출잔액_원']==a['기존대출잔액_보정후_원']+a['차량할부원금_원']
        assert row['개인_평균월대출상환액_원']==a['기존월상환액_보정후_원']+a['차량_월상환액_원']
        assert row['개인_순자산_차량제외_원']==row['개인_총자산_차량제외_원']-row['개인_대출잔액_원']
        assert row['개인_월잔여액_원']==row['개인_평균월실수령소득_원']-row['개인_평균월소비합계_원']-row['개인_평균월대출상환액_원']-row['개인_평균월저축액_원']
        if row['경력_구분']=='사회초년생':assert a['옵션포함가격_원']<=40000000
    assert len({r['프로필_식별자'] for r in rows})==len(rows)
    return {'status':'passed','profiles':len(rows),'models':len(catalog['models']),'configurations':len(inventory),
            'model_counts':dict(Counter(r['보유차량_모델'] for r in rows)),
            'splits':dict(Counter(r['데이터_구분'] for r in rows)),
            'price_range_won':[min(a['옵션포함가격_원'] for a in audit),max(a['옵션포함가격_원'] for a in audit)],
            'early_career_owners':sum(r['경력_구분']=='사회초년생' for r in rows)}


def main():
    before=snapshot_domestic();settings=load_json(ROOT/'generation_config.json');catalog=load_json(ROOT/'catalog.json')
    inventory=inventory_from_catalog(catalog)
    rows,audit,rejected=create_dataset(settings,catalog,inventory)
    assert (rows,audit,rejected)==create_dataset(settings,catalog,inventory)
    report=validate(rows,audit,catalog,inventory)
    report.update({'deterministic_regeneration':'passed','rejected_candidates':rejected,
                   'domestic_input_hashes':before})
    for name,value in [('learning-rows.json',rows),('purchase-audit.json',audit),('configuration-catalog.json',inventory),
                       ('owner-group-summary.json',summarize_owners(rows,catalog['models'])),('validation-report.json',report)]:
        (ROOT/name).write_text(json.dumps(value,ensure_ascii=False,indent=2),encoding='utf-8')
    assert before==snapshot_domestic(),'Existing domestic files changed'
    print(json.dumps({k:v for k,v in report.items() if k!='domestic_input_hashes'},ensure_ascii=False))


if __name__=='__main__':main()
