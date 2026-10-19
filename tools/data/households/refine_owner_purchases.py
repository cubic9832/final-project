from tools.data.households.paths import SYNTHETIC_ROOT

"""Refine fictional owners with sourced configurations and reconciled funding."""
import hashlib
import json
import math
import random
from collections import Counter
from pathlib import Path

from tools.data.households.budget_simulation import loan_payment

ROOT=SYNTHETIC_ROOT
OUTPUT=ROOT/'owner-funded'


def canonical_model(name):
    return name.replace(' Hybrid','')


def configuration_key(v):
    return '|'.join([v['model'],v['powertrain'],v['trim']])


def build_inventory(raw,catalog,config):
    models={(v['brand'],v['model']):v for v in catalog}
    inventory=[];seen=set()
    for v in raw['trim_prices']:
        model=canonical_model(v['model']);key=(v['brand'],model)
        if key not in models or not v.get('price_won'):continue
        signature=tuple(str(v.get(k,'')) for k in ['brand','model','model_year','trim','powertrain','fuel','price_won'])
        if signature in seen:continue
        seen.add(signature)
        record=dict(v,canonical_model=model,label_code=models[key]['code'],body=models[key]['body'],segment=models[key]['segment'])
        # Only retain options with visually reviewed page and powertrain applicability.
        record['verified_options']=config['verified_options'].get(configuration_key(v),[])
        record['configuration_id']=f'C{len(inventory)+1:04d}'
        inventory.append(record)
    if not inventory:raise ValueError('No source prices available')
    return inventory


def option_variants(v):
    options=v['verified_options'];variants=[]
    for mask in range(1<<len(options)):
        selected=[o for i,o in enumerate(options) if mask&(1<<i)]
        ids={o['id'] for o in selected}
        if all(set(o['requires'])<=ids for o in selected):
            variants.append((selected,sum(o['price_won'] for o in selected)))
    return variants


def funding_terms(row,invoice,support,purchase_income,available_own,config):
    monthly=round(purchase_income/12*0.82)
    early=row['경력_구분']=='사회초년생'
    price_cap=purchase_income*(config['early_career_price_income_ratio'] if early else config['experienced_price_income_ratio'])
    price_cap+=min(row['개인_현금성자산_원']*config['cash_price_allowance_ratio'],config['cash_price_allowance_cap_won'])
    if early:price_cap=min(price_cap,config['early_career_invoice_cap_won'])
    if invoice>price_cap:return None
    registration=round(invoice*config['registration_ratio_assumed']);cost=invoice+registration
    existing=row['개인_평균월대출상환액_원']
    payment_cap=min(monthly*config['vehicle_payment_net_income_cap'],monthly*config['total_payment_net_income_cap']-existing)
    if payment_cap<=0:return None
    rate=config['annual_rate_assumed']/12;n=config['loan_months']
    finance_cap=min(invoice*config['max_vehicle_finance_ratio'],payment_cap*(1-(1+rate)**-n)/rate)
    finance_cap=max(0,math.floor(finance_cap))
    support=min(support,round(cost*config['support_cost_ratio_cap']))
    own_needed=max(registration-support,cost-support-finance_cap,0)
    if own_needed>available_own:return None
    return {'cost':cost,'registration':registration,'support':support,'min_own':math.ceil(own_needed),
            'max_own':min(cost-support,available_own),'finance_cap':finance_cap,'price_cap':price_cap}


def refine_population(rows,inventory,config):
    rng=random.Random(config['seed']);output=[];audits=[]
    scenarios=[(v,options,price) for v in inventory for options,price in option_variants(v)]
    for source in rows:
        row=dict(source);original_payment=row['개인_평균월대출상환액_원'];original_debt=row['개인_대출잔액_원']
        # Repair implausible old synthetic mortgage burdens before adding vehicle debt.
        payment_cap=round(row['개인_평균월실수령소득_원']*config['existing_payment_net_income_cap'])
        existing_payment=min(original_payment,payment_cap)
        existing_debt=round(original_debt*(existing_payment/original_payment)) if original_payment else original_debt
        row['개인_평균월대출상환액_원']=existing_payment
        row['개인_대출잔액_원']=existing_debt
        current_annual=row['개인_연간세전소득_원']
        purchase_income=max(config['purchase_income_floor_won'],round(current_annual*rng.uniform(0.95,1.2)))
        saving_years=min(8,max(1,row['경력_년']+1))
        available_own=math.floor(purchase_income*config['purchase_savings_income_ratio_per_year']*saving_years+row['개인_현금성자산_원']*0.5)
        support=0
        if rng.random()<config['support_probability']:
            cap=config['support_early_cap_won'] if row['경력_구분']=='사회초년생' else config['support_other_cap_won']
            support=rng.randint(1,cap//100000)*100000
        feasible=[]
        for v,options,option_price in scenarios:
            invoice=v['price_won']+option_price
            terms=funding_terms(row,invoice,support,purchase_income,available_own,config)
            if not terms:continue
            # Normalize over configurations so models with many trims do not dominate.
            same_model=canonical_model(v['model'])==source['보유차량_모델']
            weight=config['same_model_weight'] if same_model else config['same_body_weight'] if v['body']==source['보유차량_차체'] else 1
            target=max(13000000,purchase_income*0.6+row['개인_현금성자산_원']*0.1)
            weight*=math.exp(-config['price_preference_penalty']*math.log(invoice/target)**2)
            weight*=config['paid_option_probability'] if options else 1-config['paid_option_probability']
            feasible.append((v,options,option_price,terms,weight))
        if not feasible:raise ValueError('No consistent purchase for '+row['프로필_식별자'])
        model_counts=Counter(v['label_code'] for v,_,_,_,_ in feasible)
        weights=[w/model_counts[v['label_code']] for v,o,p,t,w in feasible]
        v,options,option_price,terms,_=rng.choices(feasible,weights=weights)[0]
        own=rng.randint(terms['min_own'],terms['max_own'])
        finance=terms['cost']-own-terms['support']
        principal,interest=loan_payment(finance,config['annual_rate_assumed'],config['loan_months'],'annuity') if finance else (0,0)
        payment=principal+interest
        # Snapshot is at delivery: purchase cash minus own payment equals current cash.
        cash_now=row['개인_현금성자산_원']
        row.update({'보유차량_라벨코드':v['label_code'],'보유차량_브랜드':v['brand'],'보유차량_모델':v['canonical_model'],
                    '보유차량_차체':v['body'],'보유차량_차급':v['segment'],
                    '개인_대출잔액_원':existing_debt+finance,'개인_평균월대출상환액_원':existing_payment+payment,
                    '개인_순자산_차량제외_원':row['개인_총자산_차량제외_원']-existing_debt-finance,
                    '생성규칙_버전':config['version'],'난수_시드':config['seed']})
        before_savings=row['개인_평균월실수령소득_원']-row['개인_평균월소비합계_원']-row['개인_평균월대출상환액_원']
        row['개인_평균월저축액_원']=min(row['개인_평균월저축액_원'],max(0,before_savings))
        row['개인_월잔여액_원']=before_savings-row['개인_평균월저축액_원']
        # Purchase history and vehicle-specific payment are audit-only, avoiding answer leakage.
        audit={'프로필_식별자':row['프로필_식별자'],'차량사양_식별자':v['configuration_id'],
               '기존_모델':source['보유차량_모델'],'구매_모델':v['canonical_model'],'연식_표기':v.get('model_year'),
               '파워트레인':v['powertrain'],'연료':v['fuel'],'트림':v['trim'],
               '기본가격_원':v['price_won'],'선택옵션':'; '.join(o['name'] for o in options) or '추가옵션_미선택',
               '옵션가격_원':option_price,'옵션포함가격_원':v['price_won']+option_price,
               '등록비_가정_원':terms['registration'],'총구매비용_가정_원':terms['cost'],
               '본인구매자금_원':own,'가족지원금_가정_원':terms['support'],'차량할부원금_원':finance,
               '구매직전_현금_원':cash_now+own,'구매직후_현금_원':cash_now,
               '구매당시_연간세전소득_가정_원':purchase_income,
               '현재_개인연간세전소득_원':current_annual,
               '소득변화_가정': '예' if purchase_income!=current_annual else '아니오',
               '할부기간_개월':config['loan_months'] if finance else 0,
               '차량할부_연금리_가정':config['annual_rate_assumed'] if finance else 0,
               '차량_월원금상환액_원':principal,'차량_월이자_원':interest,
               '차량_월상환액_원':payment,'기존대출잔액_보정후_원':existing_debt,
               '기존월상환액_보정후_원':existing_payment,'기존월상환액_보정전_원':original_payment,
               '기존대출잔액_보정전_원':original_debt,
               '옵션수집범위':'해당사양_검토옵션만' if v['verified_options'] else '전체옵션미수집_추가옵션미선택',
               '기본가격_출처_URL':v['source_url'],'기본가격_출처_페이지':v['source_page']}
        assert terms['cost']==own+terms['support']+finance
        assert 0<=finance<=terms['finance_cap']+1
        assert abs((cash_now+own)-own-cash_now)<1
        assert payment<=round(purchase_income/12*.82)*config['vehicle_payment_net_income_cap']+2
        if row['경력_구분']=='사회초년생':assert audit['옵션포함가격_원']<=config['early_career_invoice_cap_won']
        output.append(row);audits.append(audit)
    return output,audits


def main():
    from tools.data.households.generate_owner_population import summarize_owners,validate_population
    config_path=ROOT/'purchase_refinement_config.json'
    config=json.loads(config_path.read_text(encoding='utf-8'))
    source_path=ROOT/'owner-population/learning-rows.json'
    rows=json.loads(source_path.read_text(encoding='utf-8'))
    catalog=json.loads((ROOT/'owner-population/vehicle-label-catalog.json').read_text(encoding='utf-8'))
    raw_path=ROOT.parent.parent/'vehicles/normalized-vehicle-details.json'
    inventory=build_inventory(json.loads(raw_path.read_text(encoding='utf-8')),catalog,config)
    refined,audit=refine_population(rows,inventory,config)
    assert (refined,audit)==refine_population(rows,inventory,config)
    report=validate_population(refined,catalog)
    report.update({'funding_identities':'passed','deterministic_regeneration':'passed','configurations':len(inventory),
                   'paid_option_owners':sum(a['옵션가격_원']>0 for a in audit),
                   'owners_with_family_support':sum(a['가족지원금_가정_원']>0 for a in audit),
                   'reassigned_models':sum(a['기존_모델']!=a['구매_모델'] for a in audit),
                   'early_career_max_invoice_won':max(a['옵션포함가격_원'] for r,a in zip(refined,audit) if r['경력_구분']=='사회초년생'),
                   'max_invoice_won':max(a['옵션포함가격_원'] for a in audit),
                   'input_sha256':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in [config_path,source_path,raw_path]}})
    OUTPUT.mkdir(exist_ok=True)
    for name,value in [('learning-rows.json',refined),('purchase-audit.json',audit),('configuration-catalog.json',inventory),
                       ('owner-group-summary.json',summarize_owners(refined,catalog)),('validation-report.json',report)]:
        (OUTPUT/name).write_text(json.dumps(value,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(report,ensure_ascii=False))


if __name__=='__main__':main()
