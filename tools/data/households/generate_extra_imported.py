from tools.data.households.paths import SYNTHETIC_ROOT

"""Create an additional imported-owner dataset without modifying existing data."""
import hashlib
import json
import random
from collections import Counter
from pathlib import Path

ROOT=SYNTHETIC_ROOT / 'imported-extra-90000'
PARENT=ROOT.parent
from tools.data.households.generate_imported_owners import create_dataset,inventory_from_catalog,validate,load_json
from tools.data.households.generate_owner_population import summarize_owners


def existing_hashes():
    return {str(p):hashlib.sha256(p.read_bytes()).hexdigest()
            for folder in ['owner-funded','owner-population','ownership','generated','imported-owners','domestic-extra-90000']
            for p in (PARENT/folder).rglob('*') if p.is_file() and '__pycache__' not in p.parts}


def main():
    before=existing_hashes();config=load_json(ROOT/'generation_config.json')
    catalog=load_json(PARENT/'imported-owners/catalog.json');inventory=inventory_from_catalog(catalog)
    settings=load_json(PARENT/'imported-owners/generation_config.json')
    settings.update(version=config['version'],owners_per_model=config['owners_per_model_per_batch'],candidate_count=config['candidate_count_per_batch'])
    per_batch=len(catalog['models'])*settings['owners_per_model']
    assert config['count']%per_batch==0
    existing_ids=set();signatures=set()
    signature_keys=['나이_세','성별','개인_연간세전소득_원','개인_현금성자산_원','가구원수_명']
    for folder in ['owner-funded','owner-population','ownership','imported-owners','domestic-extra-90000']:
        for r in load_json(PARENT/folder/'learning-rows.json'):
            existing_ids.add(r['프로필_식별자'])
            if all(k in r for k in signature_keys):signatures.add(tuple(r[k] for k in signature_keys))
    rows=[];audit=[];rejected=Counter()
    for batch in range(config['count']//per_batch):
        settings['seed']=config['seed']+batch*config['seed_stride']
        settings['profile_id_start']=config['profile_id_start']+batch*per_batch
        part,details,failures=create_dataset(settings,catalog,inventory)
        assert (part,details,failures)==create_dataset(settings,catalog,inventory)
        validate(part,details,catalog,inventory)
        for r in part:
            assert r['프로필_식별자'] not in existing_ids
            signature=tuple(r[k] for k in signature_keys)
            assert signature not in signatures,'Duplicate profile';signatures.add(signature)
            r['난수_시드']=config['seed']
            r['라벨_근거']='가격자금보정_추가가상수입차보유자분포'
        rows.extend(part);audit.extend(details);rejected.update(failures)
        if (batch+1)%10==0:print(json.dumps({'generated':len(rows)}),flush=True)
    shuffled=list(range(len(rows)));random.Random(config['seed']+100).shuffle(shuffled)
    for j,idx in enumerate(shuffled):rows[idx]['데이터_구분']='학습' if j<len(rows)*.7 else '검증' if j<len(rows)*.85 else '평가'
    report=validate(rows,audit,catalog,inventory)
    assert len(rows)==config['count']
    assert [r['프로필_식별자'] for r in rows]==[f'P{i:06d}' for i in range(config['profile_id_start'],config['profile_id_start']+config['count'])]
    assert set(report['model_counts'].values())=={config['count']//len(catalog['models'])}
    for split in ['학습','검증','평가']:assert len({r['보유차량_라벨코드'] for r in rows if r['데이터_구분']==split})==6
    report.update({'id_first':rows[0]['프로필_식별자'],'id_last':rows[-1]['프로필_식별자'],
                   'all_batch_regenerations_identical':True,'duplicate_profiles':0,'rejected_candidates':dict(rejected),
                   'preserved_input_hashes':before,'rule_input_hashes':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in [ROOT/'generation_config.json',PARENT/'imported-owners/catalog.json',PARENT/'imported-owners/generation_config.json',PARENT/'owner_population_config.json',PARENT/'purchase_refinement_config.json']}})
    for name,value in [('learning-rows.json',rows),('purchase-audit.json',audit),('owner-group-summary.json',summarize_owners(rows,catalog['models'])),('validation-report.json',report)]:
        (ROOT/name).write_text(json.dumps(value,ensure_ascii=False,separators=(',',':')),encoding='utf-8')
    assert before==existing_hashes(),'Existing data changed'
    print(json.dumps({k:v for k,v in report.items() if not k.endswith('hashes')},ensure_ascii=False),flush=True)


if __name__=='__main__':main()
