from tools.data.households.paths import SYNTHETIC_ROOT

"""Append-only dataset generation in a separate directory; original files are read-only."""
import hashlib
import json
from collections import Counter
from functools import lru_cache
from pathlib import Path

ROOT=SYNTHETIC_ROOT / 'domestic-extra-90000'
PARENT=ROOT.parent
from tools.data.households.generate_owner_population import generate_population,summarize_owners
from tools.data.households.refine_owner_purchases import build_inventory,refine_population


def load_json(path):return json.loads(path.read_text(encoding='utf-8'))


def hash_existing():
    return {str(p):hashlib.sha256(p.read_bytes()).hexdigest()
            for folder in ['owner-funded','owner-population','ownership','generated','imported-owners']
            for p in (PARENT/folder).rglob('*') if p.is_file() and '__pycache__' not in p.parts}


@lru_cache(maxsize=1)
def schemas():
    return (list(load_json(PARENT/'owner-funded/learning-rows.json')[0]),
            list(load_json(PARENT/'owner-funded/purchase-audit.json')[0]))


def validate(rows,audit,inventory,start):
    people_template,audit_template=schemas()
    configs={v['configuration_id']:v for v in inventory}
    for i,(r,a) in enumerate(zip(rows,audit),start):
        assert list(r)==people_template and list(a)==audit_template
        assert r['프로필_식별자']==a['프로필_식별자']==f'P{i:06d}'
        assert 20<=r['나이_세']<=59
        assert r['보유차량_모델']==a['구매_모델']
        v=configs[a['차량사양_식별자']]
        assert a['기본가격_원']==v['price_won']
        names=[] if a['선택옵션']=='추가옵션_미선택' else a['선택옵션'].split('; ')
        options=[o for o in v['verified_options'] if o['name'] in names]
        assert len(names)==len(options)
        assert a['옵션가격_원']==sum(o['price_won'] for o in options)
        ids={o['id'] for o in options}
        assert all(set(o['requires'])<=ids for o in options)
        assert a['총구매비용_가정_원']==a['기본가격_원']+a['옵션가격_원']+a['등록비_가정_원']
        assert a['총구매비용_가정_원']==a['본인구매자금_원']+a['가족지원금_가정_원']+a['차량할부원금_원']
        assert a['구매직전_현금_원']-a['본인구매자금_원']==r['개인_현금성자산_원']
        assert r['개인_대출잔액_원']==a['기존대출잔액_보정후_원']+a['차량할부원금_원']
        assert r['개인_평균월대출상환액_원']==a['기존월상환액_보정후_원']+a['차량_월상환액_원']
        assert r['개인_순자산_차량제외_원']==r['개인_총자산_차량제외_원']-r['개인_대출잔액_원']
        assert r['개인_월잔여액_원']==r['개인_평균월실수령소득_원']-r['개인_평균월소비합계_원']-r['개인_평균월대출상환액_원']-r['개인_평균월저축액_원']
        net=round(a['구매당시_연간세전소득_가정_원']/12*.82)
        assert a['차량_월상환액_원']<=net*.2+2
        assert r['개인_평균월대출상환액_원']<=net*.45+2
        if r['경력_구분']=='사회초년생':assert a['옵션포함가격_원']<=40000000


def main():
    before=hash_existing();settings=load_json(ROOT/'generation_config.json')
    config=load_json(PARENT/'owner_population_config.json')
    config.update(count=settings['count'],seed=settings['seed'],version=settings['version'])
    catalog=load_json(PARENT/'owner-population/vehicle-label-catalog.json')
    finance=load_json(PARENT/'purchase_refinement_config.json');finance['version']=settings['version']
    raw_path=PARENT.parent.parent/'vehicles/normalized-vehicle-details.json'
    inventory=build_inventory(load_json(raw_path),catalog,finance)
    source,_=generate_population(config,catalog)
    existing_ids=set()
    signatures=set()
    for folder in ['owner-funded','owner-population','ownership','imported-owners']:
        for row in load_json(PARENT/folder/'learning-rows.json'):
            existing_ids.add(row['프로필_식별자'])
            keys=['나이_세','성별','개인_연간세전소득_원','개인_현금성자산_원','가구원수_명']
            if all(k in row for k in keys):signatures.add(tuple(row[k] for k in keys))
    rows=[];audit=[]
    for offset in range(0,len(source),settings['chunk_size']):
        finance['seed']=settings['seed']+offset
        part=source[offset:offset+settings['chunk_size']]
        refined,details=refine_population(part,inventory,finance)
        assert (refined,details)==refine_population(part,inventory,finance)
        for j,(r,a) in enumerate(zip(refined,details),settings['profile_id_start']+offset):
            pid=f'P{j:06d}';r['프로필_식별자']=pid;a['프로필_식별자']=pid
            r['난수_시드']=settings['seed'];r['라벨_근거']='가격자금보정_추가가상국내차보유자분포'
            assert pid not in existing_ids
            signature=tuple(r[k] for k in ['나이_세','성별','개인_연간세전소득_원','개인_현금성자산_원','가구원수_명'])
            assert signature not in signatures,'Duplicate financial profile'
            signatures.add(signature)
        validate(refined,details,inventory,settings['profile_id_start']+offset)
        rows.extend(refined);audit.extend(details)
        if (offset+len(part))%10000==0:print(json.dumps({'generated':offset+len(part)}),flush=True)
    assert len(rows)==settings['count']
    for split in ['학습','검증','평가']:
        assert len({r['보유차량_라벨코드'] for r in rows if r['데이터_구분']==split})==len(catalog)
    report={'status':'passed','profiles':len(rows),'models':len(catalog),'configurations':len(inventory),
            'id_first':rows[0]['프로필_식별자'],'id_last':rows[-1]['프로필_식별자'],
            'model_counts':dict(Counter(r['보유차량_모델'] for r in rows)),
            'splits':dict(Counter(r['데이터_구분'] for r in rows)),
            'paid_option_owners':sum(a['옵션가격_원']>0 for a in audit),
            'duplicate_profiles':0,'all_chunk_regenerations_identical':True,'funding_and_schema_validation':'passed',
            'preserved_input_hashes':before,
            'rule_input_hashes':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in [ROOT/'generation_config.json',PARENT/'owner_population_config.json',PARENT/'purchase_refinement_config.json',raw_path]}}
    for name,value in [('learning-rows.json',rows),('purchase-audit.json',audit),('owner-group-summary.json',summarize_owners(rows,catalog)),('validation-report.json',report)]:
        (ROOT/name).write_text(json.dumps(value,ensure_ascii=False,separators=(',',':')),encoding='utf-8')
    assert before==hash_existing(),'Existing data changed'
    print(json.dumps({k:v for k,v in report.items() if not k.endswith('hashes')},ensure_ascii=False),flush=True)


if __name__=='__main__':main()
