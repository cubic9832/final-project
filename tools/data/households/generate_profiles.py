from tools.data.households.paths import SYNTHETIC_ROOT

"""Generate reproducible synthetic finances and sourced vehicle scenarios."""
import argparse
import hashlib
import json
import math
import random
from collections import Counter
from pathlib import Path

from tools.data.households.budget_simulation import loan_payment, simulate_budget

ROOT = SYNTHETIC_ROOT


def choose(rng, weights):
    return rng.choices(list(weights), weights=list(weights.values()))[0]


def money(value):
    return max(0, round(value / 1000) * 1000)


def create_finances(index, rng, config, case='general'):
    employment = choose(rng, config['employment_weights'])
    size = rng.choices(range(1, 6), weights=config['household_size_weights'])[0]
    scope = 'individual' if size == 1 else 'household'
    housing = choose(rng, config['housing_weights'])
    age = rng.randint(20, 75)
    # Shared income/lifestyle factors introduce explicit assumed dependencies.
    income = money(rng.lognormvariate(math.log(config['income_medians_won'][employment]), config['income_log_sigma']) * (1 + 0.25 * (size - 1)))
    if case == 'high_income_high_debt': income = 12000000
    if case == 'low_income_high_assets': income = 1200000
    if case == 'deficit': income = 700000
    if case == 'unstable_income': employment = 'temporary'
    extra = money(income * rng.uniform(0, 0.12)) if rng.random() < 0.3 else 0
    lifestyle = rng.lognormvariate(0, 0.22) * (max(income, 500000) / 3000000) ** 0.3
    expense = {'housing_won': money((250000 if housing == 'owner' else 400000 if housing == 'deposit_rental' else 750000) * lifestyle),
               'living_won': money((400000 + 200000 * (size - 1)) * lifestyle),
               'phone_won': money(60000 * size * rng.uniform(0.7, 1.3)),
               'transport_won': money(rng.uniform(80000, 350000) * lifestyle),
               'fixed_won': money((180000 + 80000 * (size - 1)) * lifestyle),
               'discretionary_won': money(income * rng.uniform(0.04, 0.2)),
               'target_savings_won': money(income * rng.uniform(0, 0.25))}
    if case == 'deficit': expense['living_won'] = max(expense['living_won'], income + extra + 100000)
    consumption = sum(v for k, v in expense.items() if k != 'target_savings_won')
    emergency = consumption * rng.randint(*config['emergency_months_range'])
    cash = money(income * rng.lognormvariate(math.log(5), 1.1))
    if case == 'low_income_high_assets': cash = 300000000
    if case == 'emergency_shortfall': cash = 100000
    loans = []
    if case not in ['no_debt', 'low_income_high_assets'] and (rng.random() < config['debt_probability'] or case == 'high_income_high_debt'):
        for j in range(rng.randint(1, 2)):
            kind = rng.choice(['secured', 'unsecured', 'card'])
            months = rng.choice([12, 24, 36, 60, 120, 240]) if kind == 'secured' else rng.choice([12, 24, 36, 60])
            balance = money(income * rng.uniform(*config[f'{kind}_balance_income_months_range']))
            if case == 'high_income_high_debt': balance = 500000000
            method = rng.choice(['annuity', 'equal_principal', 'bullet'])
            rate = round(rng.uniform(*config['loan_rate_range']), 5)
            principal, interest = loan_payment(balance, rate, months, method)
            loans.append({'loan_sequence': j + 1, 'loan_type': kind, 'balance_won': balance,
                          'annual_rate_assumed': rate, 'remaining_months': months, 'repayment_method': method,
                          'monthly_principal_won': principal, 'monthly_interest_won': interest,
                          'maturity_lump_sum_won': balance if method == 'bullet' else 0})
    profile = {'profile_id': f'P{index:06d}' if case == 'general' else f'E{index:06d}', 'budget_scope': scope,
               'case_type': case, 'age_years': age, 'employment': employment, 'household_size': size,
               'dependents': rng.randint(0, size - 1), 'housing': housing,
               'monthly_net_income_won': income, 'monthly_extra_income_won': extra,
               'income_volatility_assumed': round(0.35 if employment in ['temporary', 'self_employed'] else 0.1, 2),
               'liquid_cash_won': cash, 'locked_housing_deposit_won': money(rng.uniform(20000000, 200000000)) if housing == 'deposit_rental' else money(rng.uniform(5000000, 20000000)) if housing == 'monthly_rental' else 0,
               'emergency_target_won': emergency}
    return profile, expense, loans


def create_scenario(profile, expense, vehicle, rng, config):
    price = vehicle['price_won']
    registration = round(price * config['registration_cost_ratio_assumed'])
    available_cash = max(0, profile['liquid_cash_won'] - profile['emergency_target_won'] - registration)
    months = rng.choice(config['vehicle_months'])
    down = price if months == 0 else min(price, available_cash, money(available_cash * rng.uniform(0.3, 1)))
    distance = rng.randint(5000, 25000)
    fuel = vehicle['fuel']
    energy_price = config['energy_price_assumptions'].get(fuel)
    if energy_price is None:
        raise ValueError(f'Unsupported fuel: {fuel}')
    energy = round(distance / vehicle['combined_efficiency'] * energy_price / 12)
    insurance = rng.randint(*config['insurance_annual_range_won'])
    maintenance = rng.randint(*config['maintenance_annual_range_won'])
    running = energy + round((insurance + maintenance + config['annual_tax_reserve_won']) / 12)
    return {'vehicle_id': vehicle['vehicle_id'], 'brand': vehicle['brand'], 'model': vehicle['model'], 'trim': vehicle['trim'],
            'powertrain': vehicle['powertrain'], 'fuel': fuel, 'vehicle_price_won': price,
            'combined_efficiency': vehicle['combined_efficiency'], 'efficiency_unit': vehicle['efficiency_unit'],
            'price_source_url': vehicle['source_url'], 'price_source_page': vehicle['source_page'],
            'efficiency_source_url': vehicle['efficiency_source_url'], 'efficiency_source_page': vehicle['efficiency_source_page'],
            'down_payment_won': down, 'installment_months': months,
            'annual_rate_assumed': round(rng.uniform(*config['vehicle_rate_range']), 5),
            'annual_distance_km': distance, 'energy_price_assumed': energy_price,
            'monthly_energy_cost_won': energy, 'insurance_annual_assumed_won': insurance,
            'maintenance_annual_assumed_won': maintenance, 'registration_cost_assumed_won': registration,
            'monthly_operating_cost_won': running,
            'monthly_replaced_transport_won': money(expense['transport_won'] * rng.uniform(0, 0.7)),
            'vehicle_data_origin': 'official_extract_automatic_join', 'cost_origin': 'assumed_simulation'}


def generate_dataset(config, vehicle_data, count):
    rng = random.Random(config['seed'])
    vehicles = []
    for index, vehicle in enumerate(vehicle_data['vehicle_details']):
        if vehicle.get('price_won') and vehicle.get('combined_efficiency') and '1건' in vehicle.get('join_status', ''):
            if vehicle['fuel'] in config['energy_price_assumptions'] and vehicle['efficiency_unit'] in ['km/L', 'km/kWh']:
                vehicles.append(dict(vehicle, vehicle_id=f'V{index+1:04d}'))
    if not vehicles:
        raise ValueError('No usable sourced vehicle rows')
    split_ids = list(range(1, count + 1))
    random.Random(config['seed'] + 1).shuffle(split_ids)
    train_end = round(count * config['split_ratios'][0])
    valid_end = train_end + round(count * config['split_ratios'][1])
    splits = {i: 'train' if n < train_end else 'validation' if n < valid_end else 'test' for n, i in enumerate(split_ids)}
    tables = {k: [] for k in ['profiles', 'expenses', 'loans', 'vehicle_scenarios', 'simulation_results']}
    edge_cases = ['high_income_high_debt', 'low_income_high_assets', 'unstable_income', 'no_debt', 'deficit', 'emergency_shortfall']
    for index in range(1, count + 61):
        case = 'general' if index <= count else edge_cases[(index - count - 1) % len(edge_cases)]
        profile, expense, loans = create_finances(index, rng, config, case)
        meta = {'profile_id': profile['profile_id'], 'budget_scope': profile['budget_scope'], 'is_synthetic': True,
                'generator_version': config['version'], 'seed': config['seed'], 'split': splits[index] if case == 'general' else 'edge_test'}
        profile.update(meta)
        tables['profiles'].append(profile)
        tables['expenses'].append(dict(expense, **meta))
        tables['loans'].extend(dict(loan, loan_id=f"{profile['profile_id']}-L{loan['loan_sequence']}", **meta) for loan in loans)
        for j in range(config['scenarios_per_profile']):
            scenario = create_scenario(profile, expense, rng.choice(vehicles), rng, config)
            result = simulate_budget(profile, expense, loans, scenario, config)
            scenario_meta = dict(meta, scenario_id=f"{profile['profile_id']}-S{j+1}")
            tables['vehicle_scenarios'].append(dict(scenario, **scenario_meta))
            tables['simulation_results'].append(dict(result, **scenario_meta))
    return tables, vehicles


def validate_dataset(tables):
    profiles = {p['profile_id']: p for p in tables['profiles']}
    assert len(profiles) == len(tables['profiles'])
    expenses = {e['profile_id']: e for e in tables['expenses']}
    loans = {pid: [] for pid in profiles}
    for loan in tables['loans']: loans[loan['profile_id']].append(loan)
    for p in profiles.values():
        if p['case_type'] in ['no_debt', 'low_income_high_assets']: assert not loans[p['profile_id']]
    scenarios = {s['scenario_id']: s for s in tables['vehicle_scenarios']}
    for rows in tables.values():
        for row in rows:
            assert row['split'] == profiles[row['profile_id']]['split']
            assert row['is_synthetic'] is True
    for result in tables['simulation_results']:
        p = profiles[result['profile_id']]; s = scenarios[result['scenario_id']]; e = expenses[p['profile_id']]
        consumed = sum(e[k] for k in ['housing_won', 'living_won', 'phone_won', 'transport_won', 'fixed_won', 'discretionary_won'])
        debt_paid = sum(l['monthly_principal_won'] + l['monthly_interest_won'] for l in loans[p['profile_id']])
        assert result['monthly_before_purchase_won'] == p['monthly_net_income_won'] + p['monthly_extra_income_won'] - consumed - debt_paid - e['target_savings_won']
        assert result['monthly_after_purchase_won'] == result['monthly_before_purchase_won'] - result['monthly_vehicle_payment_won'] - s['monthly_operating_cost_won'] + s['monthly_replaced_transport_won']
        assert result['cash_after_purchase_won'] == p['liquid_cash_won'] - s['down_payment_won'] - s['registration_cost_assumed_won']
        assert 0 <= s['monthly_replaced_transport_won'] <= e['transport_won']
        if s['installment_months']:
            assert s['down_payment_won'] <= max(0, p['liquid_cash_won'] - p['emergency_target_won'] - s['registration_cost_assumed_won'])
        else:
            assert s['down_payment_won'] == s['vehicle_price_won']
        assert result['income_stress_remaining_won'] <= result['monthly_after_purchase_won']
        assert result['rate_stress_remaining_won'] <= result['monthly_after_purchase_won']
        if p['case_type'] == 'deficit': assert result['monthly_before_purchase_won'] < 0
    return {'status': 'passed', 'row_counts': {k: len(v) for k, v in tables.items()},
            'profile_splits': dict(Counter(p['split'] for p in profiles.values())),
            'negative_before_purchase': sum(r['monthly_before_purchase_won'] < 0 for r in tables['simulation_results']),
            'budget_exceeded_scenarios': sum(r['budget_exceeded_rule'] for r in tables['simulation_results'])}


def distribution_summary(tables):
    profiles = [p for p in tables['profiles'] if p['case_type'] == 'general']
    expenses = {e['profile_id']: e for e in tables['expenses']}
    debts = {p['profile_id']: 0 for p in profiles}
    for loan in tables['loans']:
        if loan['profile_id'] in debts: debts[loan['profile_id']] += loan['balance_won']
    income = [p['monthly_net_income_won'] for p in profiles]
    consumption = [sum(v for k, v in expenses[p['profile_id']].items() if k.endswith('_won') and k != 'target_savings_won') for p in profiles]
    def correlation(a, b):
        mean_a, mean_b = sum(a)/len(a), sum(b)/len(b)
        denominator = math.sqrt(sum((x-mean_a)**2 for x in a)*sum((y-mean_b)**2 for y in b))
        return round(sum((x-mean_a)*(y-mean_b) for x, y in zip(a, b))/denominator, 4) if denominator else None
    ordered = sorted(income)
    return {'generated_correlations': {'income_consumption': correlation(income, consumption),
                                      'income_liquid_cash': correlation(income, [p['liquid_cash_won'] for p in profiles]),
                                      'income_debt_balance': correlation(income, [debts[p['profile_id']] for p in profiles])},
            'income_quantiles_won': {str(q): ordered[round((len(ordered)-1)*q)] for q in [0.1, 0.5, 0.9]},
            'general_no_debt_profiles': sum(v == 0 for v in debts.values()),
            'general_negative_before_purchase_profiles': len({r['profile_id'] for r in tables['simulation_results'] if r['split'] != 'edge_test' and r['monthly_before_purchase_won'] < 0})}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--count', type=int)
    parser.add_argument('--output', default='generated')
    args = parser.parse_args()
    config = json.loads((ROOT / 'generation_config.json').read_text(encoding='utf-8'))
    count = args.count if args.count is not None else config['profile_count']
    if count <= 0: raise ValueError('Count must be positive')
    vehicle_path = ROOT.parent.parent / 'vehicles' / 'normalized-vehicle-details.json'
    vehicle_data = json.loads(vehicle_path.read_text(encoding='utf-8'))
    tables, vehicles = generate_dataset(config, vehicle_data, count)
    report = validate_dataset(tables)
    report.update(distribution_summary(tables))
    repeated, _ = generate_dataset(config, vehicle_data, count)
    assert repeated == tables, 'Deterministic regeneration failed'
    report.update({'deterministic_regeneration': 'passed', 'eligible_vehicle_rows': len(vehicles),
                   'vehicle_source_sha256': hashlib.sha256(vehicle_path.read_bytes()).hexdigest(),
                   'config_sha256': hashlib.sha256((ROOT / 'generation_config.json').read_bytes()).hexdigest()})
    general = [p for p in tables['profiles'] if p['case_type'] == 'general']
    report['general_means_won'] = {k: round(sum(p[k] for p in general)/len(general)) for k in ['monthly_net_income_won', 'liquid_cash_won']}
    official = json.loads((ROOT.parent / 'official-household-statistics.json').read_text(encoding='utf-8'))
    anchor = next(p for p in official['financial_profiles'] if p['survey_year'] == 2025 and p['dimension'] == '전체')
    report['scale_reference_only'] = {'official_household_annual_gross_income_divided_by_12_won': anchor['monthly_income_mean_derived_won'],
                                    'note': 'Gross household aggregate and synthetic net incomes with mixed budget scopes are not directly comparable; no distribution calibration claimed.'}
    output = ROOT / args.output
    output.mkdir(parents=True, exist_ok=True)
    (output / 'dataset.json').write_text(json.dumps(tables, ensure_ascii=False), encoding='utf-8')
    (output / 'validation-report.json').write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
    (output / 'columns.json').write_text(json.dumps({k: list(v[0]) for k, v in tables.items()}, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps(report, ensure_ascii=False))


if __name__ == '__main__':
    main()
