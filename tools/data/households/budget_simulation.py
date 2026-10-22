from tools.data.households.paths import SYNTHETIC_ROOT

"""Pure loan and vehicle budget calculations; amounts are KRW."""
import math


def loan_payment(balance, annual_rate, months, method):
    if balance < 0 or annual_rate < 0 or months <= 0:
        raise ValueError('Invalid loan terms')
    interest = balance * annual_rate / 12
    if method == 'bullet':
        return 0, round(interest)
    if method == 'equal_principal':
        return round(balance / months), round(interest)
    if method != 'annuity':
        raise ValueError('Unknown repayment method')
    rate = annual_rate / 12
    payment = balance / months if rate == 0 else balance * rate / -math.expm1(-months * math.log1p(rate))
    return round(payment - interest), round(interest)


def simulate_budget(profile, expense, loans, scenario, config):
    income = profile['monthly_net_income_won'] + profile['monthly_extra_income_won']
    consumption = sum(expense[k] for k in expense if k.endswith('_won') and k != 'target_savings_won')
    payments = sum(l['monthly_principal_won'] + l['monthly_interest_won'] for l in loans)
    savings = expense['target_savings_won']
    before = income - consumption - payments - savings
    balance = scenario['vehicle_price_won'] - scenario['down_payment_won']
    months = scenario['installment_months']
    vehicle_payment = sum(loan_payment(balance, scenario['annual_rate_assumed'], months, 'annuity')) if months else 0
    stressed_vehicle = sum(loan_payment(balance, scenario['annual_rate_assumed'] + config['rate_stress_increase'], months, 'annuity')) if months else 0
    stressed_loans = sum(sum(loan_payment(l['balance_won'], l['annual_rate_assumed'] + config['rate_stress_increase'], l['remaining_months'], l['repayment_method'])) for l in loans)
    running = scenario['monthly_operating_cost_won'] - scenario['monthly_replaced_transport_won']
    after = before - vehicle_payment - running
    income_stress = round(income * (1 - config['income_stress_drop'])) - consumption - payments - savings - vehicle_payment - running
    rate_stress = income - consumption - stressed_loans - savings - stressed_vehicle - running
    upfront = scenario['down_payment_won'] + scenario['registration_cost_assumed_won']
    cash_after = profile['liquid_cash_won'] - upfront
    outflow = consumption + payments + vehicle_payment + running
    return {'monthly_before_purchase_won': before, 'monthly_vehicle_payment_won': vehicle_payment,
            'monthly_after_purchase_won': after, 'income_stress_remaining_won': income_stress,
            'rate_stress_remaining_won': rate_stress, 'cash_after_purchase_won': cash_after,
            'cash_runway_months': round(max(0, cash_after) / outflow, 3) if outflow > 0 else None,
            'upfront_funding_gap_won': max(0, upfront - profile['liquid_cash_won']),
            'emergency_shortfall_won': max(0, profile['emergency_target_won'] - cash_after),
            'budget_exceeded_rule': after < 0 or cash_after < profile['emergency_target_won'],
            'label_origin': 'simulation_rule_not_observed_outcome'}
