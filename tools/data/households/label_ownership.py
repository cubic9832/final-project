from tools.data.households.paths import SYNTHETIC_ROOT

"""Assign one hypothetical owned vehicle or purchase deferral to each profile."""
import hashlib
import json
import math
import random
from collections import Counter
from pathlib import Path

from tools.data.households.budget_simulation import loan_payment

ROOT = SYNTHETIC_ROOT
OUTPUT = ROOT / 'ownership'
FUEL_LABELS = {'GASOLINE': '가솔린', 'HYBRID': '하이브리드', 'LPG': 'LPG', 'DIESEL': '디젤'}


def build_catalog(vehicle_data, config):
    grouped = {}
    for vehicle in vehicle_data['vehicle_details']:
        if not vehicle.get('price_won') or not vehicle.get('combined_efficiency'): continue
        if '1건' not in vehicle.get('join_status', '') or vehicle.get('efficiency_unit') != 'km/L': continue
        if vehicle['fuel'] not in config['energy_prices_assumed']: continue
        if vehicle['model'] not in config['model_body_assumptions']:
            raise ValueError('Missing body classification: ' + vehicle['model'])
        # One available representative trim per model/fuel avoids trim-count bias.
        key = (vehicle['brand'], vehicle['model'], vehicle['fuel'])
        if key not in grouped or vehicle['price_won'] < grouped[key]['price_won']:
            grouped[key] = vehicle
    return [dict(v, label_id=f'M{i:03d}', body=config['model_body_assumptions'][v['model']][0],
                 segment=config['model_body_assumptions'][v['model']][1])
            for i, (_, v) in enumerate(sorted(grouped.items()), 1)]


def candidate_budget(profile, expense, debt_payment, annual_km, vehicle, config):
    consumption = sum(v for k, v in expense.items() if k.endswith('_won') and k != 'target_savings_won')
    income = profile['monthly_net_income_won'] + profile['monthly_extra_income_won']
    surplus = income - consumption - debt_payment - expense['target_savings_won']
    registration = round(vehicle['price_won'] * config['registration_ratio_assumed'])
    spendable = max(0, profile['liquid_cash_won'] - profile['emergency_target_won'])
    if spendable < registration: return None
    down = min(vehicle['price_won'], spendable - registration)
    finance = vehicle['price_won'] - down
    payment = sum(loan_payment(finance, config['annual_rate_assumed'], config['installment_months'], 'annuity')) if finance else 0
    energy = annual_km / vehicle['combined_efficiency'] * config['energy_prices_assumed'][vehicle['fuel']] / 12
    running = round(energy + (config['annual_insurance_assumed_won'] + config['annual_maintenance_assumed_won'] + config['annual_tax_reserve_assumed_won']) / 12)
    replaced = round(expense['transport_won'] * config['transport_replacement_ratio'])
    incremental = payment + running - replaced
    if surplus < 0 or incremental > surplus * config['monthly_surplus_spend_limit']: return None
    return {'down_payment_won': down, 'registration_won': registration, 'monthly_payment_won': payment,
            'monthly_running_won': running, 'replaced_transport_won': replaced,
            'monthly_remaining_won': surplus - incremental,
            'cash_remaining_won': profile['liquid_cash_won'] - down - registration}


def preference_score(profile, purpose, preference, annual_km, vehicle, config):
    spendable = max(0, profile['liquid_cash_won'] - profile['emergency_target_won'])
    income = profile['monthly_net_income_won'] + profile['monthly_extra_income_won']
    target = min(config['target_price_cap_won'], max(config['target_price_floor_won'],
                 spendable * config['target_price_cash_ratio'] + income * config['target_price_income_months']))
    score = -config['price_distance_penalty'] * math.log(vehicle['price_won'] / target) ** 2
    if vehicle['body'] == preference: score += config['preference_score']
    if profile['household_size'] >= 3 or purpose == '가족이동':
        if vehicle['body'] in ['SUV', '승합']: score += config['family_suv_score']
        if vehicle['body'] == '경차': score -= config['family_compact_penalty']
    if purpose == '출퇴근' and vehicle['segment'] in ['경형', '소형', '준중형']:
        score += config['commute_compact_score']
    if annual_km >= config['high_mileage_km'] and vehicle['fuel'] == 'HYBRID':
        score += config['high_mileage_hybrid_score']
    return score


def generate_labels(data, catalog, config):
    rng = random.Random(config['seed'])
    expenses = {e['profile_id']: e for e in data['expenses']}
    loans = {p['profile_id']: [] for p in data['profiles']}
    for loan in data['loans']: loans[loan['profile_id']].append(loan)
    rows, audit = [], []
    for profile in data['profiles']:
        if profile['case_type'] != 'general' or not config['age_min'] <= profile['age_years'] <= config['age_max']: continue
        pid = profile['profile_id']; expense = expenses[pid]
        debt_payment = sum(l['monthly_principal_won'] + l['monthly_interest_won'] for l in loans[pid])
        purpose_weights = config['purpose_weights_family' if profile['household_size'] >= 3 else 'purpose_weights_single']
        purpose = rng.choices(list(purpose_weights), list(purpose_weights.values()))[0]
        preference = rng.choice(config['body_preferences'])
        annual_km = rng.randint(5000, 25000)
        gender = rng.choice(['남성', '여성'])
        # Gender and age do not impose unsupported preference differences.
        row = {'프로필_식별자': pid, '나이_세': profile['age_years'], '연령대': f"{profile['age_years']//10*10}대",
               '성별_합성': gender, '예산_범위': '개인' if profile['budget_scope'] == 'individual' else '가구',
               '가구원수_명': profile['household_size'], '부양인원_명': profile['dependents'],
               '월_실수령소득_원': profile['monthly_net_income_won'], '월_기타소득_원': profile['monthly_extra_income_won'],
               '인출가능_현금_원': profile['liquid_cash_won'], '묶인_주거보증금_원': profile['locked_housing_deposit_won'],
               '목표_비상금_원': profile['emergency_target_won'],
               '월_생활소비합계_원': sum(v for k,v in expense.items() if k.endswith('_won') and k != 'target_savings_won'),
               '월_목표저축_원': expense['target_savings_won'], '기존대출잔액_원': sum(l['balance_won'] for l in loans[pid]),
               '월_기존대출상환액_원': debt_payment, '기존_월교통비_원': expense['transport_won'],
               '차량_이용목적_합성': purpose, '차체_선호_합성': preference, '연간_주행거리_가정_km': annual_km,
               '구매결과_라벨': '구매보류', '가상보유차량_라벨코드': None, '가상보유차량_모델': None,
               '가상보유차량_차체': None, '가상보유차량_차급': None, '가상보유차량_연료': None,
               '합성데이터_여부': '예', '라벨_생성근거': '가정기반_확률선택', '생성규칙_버전': config['version'],
               '난수_시드': config['seed'], '데이터_구분': {'train':'학습','validation':'검증','test':'평가'}[profile['split']]}
        candidates = []
        for vehicle in catalog:
            budget = candidate_budget(profile, expense, debt_payment, annual_km, vehicle, config)
            if budget is not None:
                candidates.append((vehicle, budget, preference_score(profile, purpose, preference, annual_km, vehicle, config)))
        details = {'profile_id':pid, 'candidate_count':len(candidates), 'selected_label':None, 'selected_probability':None,
                   'budget': None, 'reason':'no_candidate_meets_cash_and_monthly_budget' if not candidates else 'weighted_random_choice_among_feasible_candidates'}
        if candidates:
            maximum = max(c[2] for c in candidates)
            weights = [math.exp(c[2]-maximum) for c in candidates]
            selected_index = rng.choices(range(len(candidates)), weights=weights)[0]
            vehicle, budget, _ = candidates[selected_index]
            row.update({'구매결과_라벨':'가상구매', '가상보유차량_라벨코드':vehicle['label_id'],
                        '가상보유차량_모델':vehicle['model'], '가상보유차량_차체':vehicle['body'],
                        '가상보유차량_차급':vehicle['segment'], '가상보유차량_연료':FUEL_LABELS[vehicle['fuel']]})
            details.update({'selected_label':vehicle['label_id'], 'selected_probability':weights[selected_index]/sum(weights),
                            'budget':budget, 'candidate_scores':[{'label':v['label_id'], 'score':s, 'probability':w/sum(weights)} for (v,b,s),w in zip(candidates,weights)]})
            assert budget['cash_remaining_won'] >= profile['emergency_target_won']
            assert budget['monthly_remaining_won'] >= 0
        new_id = f'P{len(rows)+1:06d}'
        row['프로필_식별자'] = new_id
        details['source_profile_id'] = pid
        details['profile_id'] = new_id
        rows.append(row); audit.append(details)
    assert len({r['프로필_식별자'] for r in rows}) == len(rows)
    return rows, audit


def main():
    config_path = ROOT/'ownership_config.json'
    config = json.loads(config_path.read_text(encoding='utf-8'))
    dataset_path = ROOT/'generated/dataset.json'
    data = json.loads(dataset_path.read_text(encoding='utf-8'))
    vehicle_path = ROOT.parent.parent/'vehicles/normalized-vehicle-details.json'
    catalog = build_catalog(json.loads(vehicle_path.read_text(encoding='utf-8')), config)
    rows, audit = generate_labels(data, catalog, config)
    assert (rows,audit) == generate_labels(data,catalog,config)
    bands = [(0,10000000,'1천만원 미만'),(10000000,30000000,'1천만~3천만원'),(30000000,50000000,'3천만~5천만원'),(50000000,100000000,'5천만~1억원'),(100000000,math.inf,'1억원 이상')]
    by_label = {v['label_id']:v for v in catalog}
    summary = []
    for lo,hi,name in bands:
        group = [r for r in rows if lo<=r['인출가능_현금_원']<hi]
        bought = [r for r in group if r['구매결과_라벨']=='가상구매']
        summary.append({'현금구간':name,'프로필수':len(group),'가상구매수':len(bought),'구매보류수':len(group)-len(bought),
                        '선택차량평균가격_원':round(sum(by_label[r['가상보유차량_라벨코드']]['price_won'] for r in bought)/len(bought)) if bought else None,
                        '선택차체분포':dict(Counter(r['가상보유차량_차체'] for r in bought))})
    report = {'status':'passed', 'profiles':len(rows), 'catalog_labels':len(catalog),
              'outcomes':dict(Counter(r['구매결과_라벨'] for r in rows)), 'splits':dict(Counter(r['데이터_구분'] for r in rows)),
              'label_counts':dict(Counter(r['가상보유차량_라벨코드'] for r in rows if r['구매결과_라벨']=='가상구매')),
              'cash_band_summary':summary, 'deterministic_regeneration':'passed',
              'checks':['age_filter','unique_profile','original_split_preserved','cash_and_monthly_budget','one_label_or_deferral'],
              'input_sha256':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in [config_path,dataset_path,vehicle_path]}}
    OUTPUT.mkdir(exist_ok=True)
    mapping = [{'프로필_식별자':a['profile_id'], '원본_프로필_식별자':a['source_profile_id']} for a in audit]
    report['profile_id_scheme'] = 'Sequential P000001 through row count; original IDs in profile-id-map.json'
    for name,value in [('learning-rows.json',rows),('label-audit.json',audit),('profile-id-map.json',mapping),('vehicle-label-catalog.json',catalog),('validation-report.json',report)]:
        (OUTPUT/name).write_text(json.dumps(value,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(report,ensure_ascii=False))


if __name__ == '__main__': main()
