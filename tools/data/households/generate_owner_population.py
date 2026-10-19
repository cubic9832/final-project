from tools.data.households.paths import SYNTHETIC_ROOT

"""Synthetic owner cohorts with overlapping characteristics; no purchase screening."""
import hashlib
import json
import math
import random
from collections import Counter
from pathlib import Path

from tools.data.households.budget_simulation import loan_payment

ROOT = SYNTHETIC_ROOT
OUTPUT = ROOT/'owner-population'


def money(value):
    return max(0, round(value/1000)*1000)


def create_catalog(source):
    grouped = {}
    for vehicle in source:
        model = vehicle['model'].replace(' Hybrid', '')
        grouped.setdefault((vehicle['brand'],model), []).append(vehicle)
    return [{'code':f'OWN{i:03d}', 'brand':brand, 'model':model,
             'segment':variants[0]['segment'], 'body':variants[0]['body'],
             'source_variants':variants}
            for i,((brand,model),variants) in enumerate(sorted(grouped.items()),1)]


def generate_population(config,catalog):
    rng = random.Random(config['seed'])
    count = config['count']
    # Uniform model sampling is experimental coverage, not market share.
    assigned = [catalog[i%len(catalog)] for i in range(count)]
    rng.shuffle(assigned)
    split_order = list(range(count));random.Random(config['seed']+1).shuffle(split_order)
    splits={idx:'학습' if j<count*0.7 else '검증' if j<count*0.85 else '평가' for j,idx in enumerate(split_order)}
    rows,audit=[],[]
    for i,vehicle in enumerate(assigned):
        group_name = vehicle['segment']
        cross = rng.random()<config['cross_group_probability']
        if cross: group_name=rng.choice(list(config['groups']))
        group = config['groups'][group_name]
        while True:
            age=round(rng.gauss(group['age_mean'],group['age_sd']))
            if config['age_min']<=age<=config['age_max']:break
        gender = rng.choice(['남성','여성'])
        experience = max(0,age-rng.randint(20,27)-rng.randint(0,3))
        career_stage = '사회초년생' if experience<=3 else '경력자'
        job = rng.choices(['근로자','자영업자','프리랜서','비취업'],[0.65,0.18,0.12,0.05])[0]
        annual = money(rng.lognormvariate(math.log(group['annual_income_median_won']),config['annual_income_log_sigma']))
        if career_stage=='사회초년생':annual=money(annual*rng.uniform(0.65,0.95))
        if job=='비취업':annual=money(annual*rng.uniform(0.15,0.5))
        monthly = money(annual/12*config['net_income_ratio_assumed'])
        family = rng.random()<group['family_probability']
        size = rng.choice([2,3,4,5]) if family else 1
        dependents = rng.randint(0,size-1)
        additional_household_income = money(rng.uniform(1000000,4000000)) if size>1 and rng.random()<0.6 else 0
        cash = money(monthly*rng.lognormvariate(math.log(group['cash_income_months']),config['liquid_cash_log_sigma']))
        other_financial = money(cash*rng.uniform(0,1.5))
        deposit = money(rng.uniform(5000000,150000000)) if rng.random()<0.6 else 0
        # Personal housing ownership is optional; household assets are not substituted.
        real_estate = money(rng.uniform(150000000,800000000)) if age>=30 and rng.random()<0.2 else 0
        housing_debt = money(real_estate*rng.uniform(0.15,0.65)) if real_estate else 0
        unsecured = money(monthly*rng.uniform(1,18)) if rng.random()<config['debt_probability'] else 0
        debt = housing_debt+unsecured
        principal_h,interest_h = loan_payment(housing_debt,0.045,240,'annuity') if housing_debt else (0,0)
        principal_u,interest_u = loan_payment(unsecured,0.075,60,'annuity') if unsecured else (0,0)
        payment=principal_h+interest_h+principal_u+interest_u
        housing_cost=money(monthly*rng.uniform(0.08,0.22))
        other_living=money(monthly*rng.uniform(*config['monthly_living_ratio_range']))
        consumption=housing_cost+other_living
        remaining=monthly-consumption-payment
        savings=money(max(0,remaining)*rng.uniform(0.2,0.65))
        purpose=rng.choices(list(group['purpose_weights']),list(group['purpose_weights'].values()))[0]
        mileage=rng.randint(8000,28000) if purpose in ['출퇴근','업무'] else rng.randint(3000,18000)
        assets=cash+other_financial+deposit+real_estate
        pid=f'P{i+1:06d}'
        rows.append({'프로필_식별자':pid,'나이_세':age,'연령대':f'{age//10*10}대','성별':gender,
                     '직업_유형':job,'경력_년':experience,'경력_구분':career_stage,
                     '가구원수_명':size,'부양인원_명':dependents,
                     '개인_연간세전소득_원':annual,'개인_평균월실수령소득_원':monthly,
                     '가구_평균월실수령소득_원':monthly+additional_household_income,
                     '개인_현금성자산_원':cash,'개인_기타금융자산_원':other_financial,
                     '개인_주거보증금자산_원':deposit,'개인_부동산자산_원':real_estate,
                     '개인_총자산_차량제외_원':assets,'개인_대출잔액_원':debt,
                     '개인_순자산_차량제외_원':assets-debt,
                     '개인_평균월주거비_원':housing_cost,'개인_평균월기타생활소비_원':other_living,
                     '개인_평균월소비합계_원':consumption,'개인_평균월대출상환액_원':payment,
                     '개인_평균월저축액_원':savings,'개인_월잔여액_원':remaining-savings,
                     '차량_이용목적':purpose,'연간_주행거리_km':mileage,
                     '보유차량_라벨코드':vehicle['code'],'보유차량_브랜드':vehicle['brand'],'보유차량_모델':vehicle['model'],
                     '보유차량_차체':vehicle['body'],'보유차량_차급':vehicle['segment'],
                     '데이터_구분':splits[i],'합성데이터_여부':'예','라벨_근거':'가상_보유자집단_분포',
                     '생성규칙_버전':config['version'],'난수_시드':config['seed']})
        audit.append({'profile_id':pid,'latent_group':group_name,'cross_group_draw':cross})
    return rows,audit


def validate_population(rows,catalog):
    labels={v['code'] for v in catalog}
    assert len({r['프로필_식별자'] for r in rows})==len(rows)
    for i,r in enumerate(rows,1):
        assert r['프로필_식별자']==f'P{i:06d}'
        assert 20<=r['나이_세']<=59
        assert r['보유차량_라벨코드'] in labels
        assert r['개인_총자산_차량제외_원']==sum(r[k] for k in ['개인_현금성자산_원','개인_기타금융자산_원','개인_주거보증금자산_원','개인_부동산자산_원'])
        assert r['개인_순자산_차량제외_원']==r['개인_총자산_차량제외_원']-r['개인_대출잔액_원']
        assert r['개인_월잔여액_원']==r['개인_평균월실수령소득_원']-r['개인_평균월소비합계_원']-r['개인_평균월대출상환액_원']-r['개인_평균월저축액_원']
    return {'status':'passed','profiles':len(rows),'models':len(labels),
            'splits':dict(Counter(r['데이터_구분'] for r in rows)),
            'negative_monthly_balance':sum(r['개인_월잔여액_원']<0 for r in rows)}


def summarize_owners(rows,catalog):
    summary=[]
    for v in catalog:
        group=[r for r in rows if r['보유차량_라벨코드']==v['code']]
        def mean(key):return round(sum(r[key] for r in group)/len(group))
        income=sorted(r['개인_연간세전소득_원'] for r in group)
        summary.append({'차량_라벨코드':v['code'],'모델':v['model'],'차체':v['body'],'차급':v['segment'],
                        '보유자수':len(group),'평균나이_세':mean('나이_세'),'연간세전소득_중앙값_원':income[len(income)//2],
                        '연간세전소득_10백분위_원':income[round((len(income)-1)*0.1)],
                        '연간세전소득_90백분위_원':income[round((len(income)-1)*0.9)],
                        '평균현금성자산_원':mean('개인_현금성자산_원'),'평균월소비_원':mean('개인_평균월소비합계_원'),
                        '평균월대출상환액_원':mean('개인_평균월대출상환액_원'),
                        '최빈연령대':Counter(r['연령대'] for r in group).most_common(1)[0][0],
                        '최빈이용목적':Counter(r['차량_이용목적'] for r in group).most_common(1)[0][0]})
    return summary


def main():
    config_path=ROOT/'owner_population_config.json'
    config=json.loads(config_path.read_text(encoding='utf-8'))
    source_path=ROOT/'ownership/vehicle-label-catalog.json'
    catalog=create_catalog(json.loads(source_path.read_text(encoding='utf-8')))
    rows,audit=generate_population(config,catalog)
    assert (rows,audit)==generate_population(config,catalog)
    report=validate_population(rows,catalog)
    report['deterministic_regeneration']='passed'
    report['input_sha256']={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in [config_path,source_path]}
    OUTPUT.mkdir(exist_ok=True)
    for name,value in [('learning-rows.json',rows),('owner-group-summary.json',summarize_owners(rows,catalog)),
                       ('vehicle-label-catalog.json',catalog),('generation-audit.json',audit),('validation-report.json',report)]:
        (OUTPUT/name).write_text(json.dumps(value,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(report,ensure_ascii=False))


if __name__=='__main__':main()
