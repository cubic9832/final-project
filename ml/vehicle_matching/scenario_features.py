"""Shared observable feature contract for scenario population training/inference."""
import math

import numpy as np

from vehicle_matching.body_types import matches_body_preference
from vehicle_matching.preference_model import FEATURE_NAMES as LEGACY_FEATURE_NAMES, encode_preference
from vehicle_matching.preferences import SIZE_BANDS

CHANNELS = ('asset_retention', 'running_affordability', 'body_match', 'fuel_match',
            'length_match', 'brand_match', 'model_affinity', 'charging_convenience')
CHANNEL_LABELS = ('구매 후 자금 보존', '월 유지비 부담', '차체 취향', '연료 취향',
                  '외부 전장 취향', '브랜드 취향', '개별 모델 호감', '충전 접근성')
FEATURE_NAMES = (*LEGACY_FEATURE_NAMES, *('scenario_' + c for c in CHANNELS),
                 *('importance_' + c for c in CHANNELS))


def channel_values(user, vehicle, cost):
    profile = user['profile']
    funds = max(1, profile['liquid_assets'] - profile['emergency_reserve'])
    available = (profile['monthly_income'] - profile['monthly_expenses']
                 - profile['existing_monthly_payment'] - profile['monthly_savings'] - profile['minimum_buffer'])
    retained = max(0, min(1, (funds - cost['total_purchase_cost']) / funds))
    # Asset-supported households still react smoothly to recurring expenses.
    capacity = max(500000, available, funds / 120)
    affordability = math.exp(-cost['monthly_running_cost'] / capacity)
    body = .5 if vehicle.body_type is None or profile['preferred_body_type'] == 'any' else float(
        matches_body_preference(profile['preferred_body_type'], vehicle.body_type))
    fuel = 'HYBRID' if vehicle.original_fuel == 'PHEV' else vehicle.fuel
    fuel_match = .5 if profile['preferred_fuel'] is None else float(fuel == profile['preferred_fuel'])
    length_match = .5
    if profile['preferred_size'] != 'any' and vehicle.length_mm is not None:
        lower, upper = SIZE_BANDS[profile['preferred_size']]
        length_match = max(0, 1 - max(lower - vehicle.length_mm, vehicle.length_mm - upper, 0) / 1000)
    brand = .5 if not user['preferred_brands'] else float(vehicle.brand in user['preferred_brands'])
    affinity = user['model_affinities'].get(vehicle.model, .5)
    charging = 1.0 if vehicle.fuel != 'ELECTRIC' or profile['charging_available'] else .15
    return np.asarray([retained, affordability, body, fuel_match, length_match, brand, affinity, charging], dtype=np.float32)


def encode_scenario(user, profile, vehicle, cost):
    return np.concatenate((encode_preference(profile, vehicle, cost=cost),
                           channel_values(user, vehicle, cost), np.asarray(user['channel_weights'], dtype=np.float32)))


def utility(values, weights):
    weights = np.asarray(weights, dtype=np.float64)
    return float(np.dot(values, weights) / weights.sum())


def probability_a(utility_a, utility_b, temperature):
    if not math.isfinite(temperature) or temperature <= 0:
        raise ValueError('Positive finite temperature required')
    difference = (utility_a - utility_b) / temperature
    return 1 / (1 + math.exp(-difference)) if difference >= 0 else math.exp(difference) / (1 + math.exp(difference))


def explain_choice(a, b, values_a, values_b, weights, label):
    deltas = (values_a - values_b) * np.asarray(weights) * (1 if label else -1)
    favorable = sorted((i for i, v in enumerate(deltas) if v > .005), key=lambda i: -deltas[i])
    sacrifices = sorted((i for i, v in enumerate(deltas) if v < -.005), key=lambda i: deltas[i])
    chosen, other = (a, b) if label else (b, a)
    gain = '·'.join(CHANNEL_LABELS[i] for i in favorable[:2])
    loss = '·'.join(CHANNEL_LABELS[i] for i in sacrifices[:2])
    if deltas.sum() < -1e-6:
        text = f'종합 선호는 {other.model} 쪽이지만 이번 확률적 선택에서는 {chosen.model}을 선택했습니다.'
        if gain:
            text += f' 선택 후보의 상대적 장점은 {gain}입니다.'
    elif gain:
        text = f'{gain}을 더 중시해 {chosen.model}을 선택했습니다.'
    else:
        text = f'평가 항목이 거의 동률인 비교에서 {chosen.model}을 선택했습니다.'
    if loss:
        text += f' {loss}에서는 상대 후보에 비해 양보했습니다.'
    return text
