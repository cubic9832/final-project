"""Preference-aware candidate ranker; separate artifacts from legacy candidate-v2."""
import hashlib
import json
import math
from pathlib import Path

import numpy as np
import torch
from torch import nn

from vehicle_matching.catalog import FUELS
from vehicle_matching.finance import Assumptions, assess
from vehicle_matching.preferences import SIZE_BANDS

FEATURE_NAMES = ('log_income', 'log_expenses', 'log_debt_payment', 'log_assets', 'log_price',
                 'log_running', 'net_monthly_millions', 'price_cash_ratio', 'cash_after_ratio',
                 'monthly_burden', 'length', 'length_known', 'seats', 'seats_known',
                 'fuel_match', 'fuel_specified', 'size_lower', 'size_upper', 'size_specified',
                 'minimum_seats', 'cost_weight', 'size_weight', 'fuel_weight', 'seats_weight',
                 *('fuel_' + fuel for fuel in FUELS))


def encode_preference(profile, vehicle, assumptions=Assumptions(), cost=None):
    cost = cost or assess(profile, vehicle, assumptions)
    if not cost['eligible']:
        raise ValueError('Only financially eligible pairs can be encoded')
    funds = max(1, profile.liquid_assets - profile.emergency_reserve)
    remaining = max(0, funds - cost['total_purchase_cost'])
    available = profile.monthly_income-profile.monthly_expenses-profile.existing_monthly_payment-profile.monthly_savings
    capacity = max(1, available-profile.minimum_buffer)
    if cost['funding_source'] == 'assets':
        capacity = max(1, available-profile.minimum_buffer+remaining/cost['required_asset_coverage_months'])
    seats = vehicle.seats if vehicle.seats is not None else min(vehicle.seat_options) if vehicle.seat_options else None
    lower, upper = SIZE_BANDS.get(profile.preferred_size, (0, 0))
    fuel = 'HYBRID' if vehicle.original_fuel == 'PHEV' else vehicle.fuel
    return np.asarray([*(math.log1p(value) for value in (profile.monthly_income, profile.monthly_expenses,
                       profile.existing_monthly_payment, funds, vehicle.price, cost['monthly_running_cost'])),
                       available/1e6, vehicle.price/funds, remaining/funds,
                       min(10, cost['monthly_running_cost']/capacity),
                       (vehicle.length_mm or 0)/6000, float(vehicle.length_mm is not None),
                       (seats or 0)/9, float(seats is not None),
                       float(fuel == profile.preferred_fuel) if profile.preferred_fuel else .5,
                       float(profile.preferred_fuel is not None), lower/6000, upper/6000,
                       float(profile.preferred_size != 'any'), profile.minimum_seats/9,
                       profile.cost_importance/5, profile.space_importance/5,
                       profile.fuel_importance/5, profile.seating_importance/5,
                       *(float(vehicle.fuel == value) for value in FUELS)], dtype=np.float32)


def preference_network():
    return nn.Sequential(nn.Linear(len(FEATURE_NAMES), 64), nn.ReLU(), nn.Linear(64, 32), nn.ReLU(), nn.Linear(32, 1))


class PreferenceRanker:
    schema = 'candidate-preferences-v3'

    def __init__(self, net, mean, scale, minimum, maximum, assumptions=Assumptions()):
        self.net = net.eval()
        self.mean, self.scale = np.asarray(mean), np.asarray(scale)
        self.minimum, self.maximum = np.asarray(minimum), np.asarray(maximum)
        self.assumptions = assumptions

    def predict(self, profile, vehicles):
        if not vehicles:
            return [], []
        x = np.stack([encode_preference(profile, vehicle, self.assumptions) for vehicle in vehicles])
        with torch.no_grad():
            scores = self.net(torch.from_numpy(((x-self.mean)/self.scale).astype(np.float32))).sigmoid().flatten().numpy()
        return scores.tolist(), np.any((x < self.minimum-1e-5) | (x > self.maximum+1e-5), axis=1).tolist()

    def ranking_scores(self, profile, vehicles):
        """Unbounded logits for ordering; never use rounded/saturated UI scores.

        predict retains its bounded contribution contract for the rule-based
        service. These logits are not probabilities or weighted-rule scores.
        """
        if not vehicles:
            return []
        x = np.stack([encode_preference(profile, vehicle, self.assumptions) for vehicle in vehicles])
        with torch.no_grad():
            return self.net(torch.from_numpy(((x-self.mean)/self.scale).astype(np.float32))).flatten().tolist()

    def save(self, directory, provenance):
        directory = Path(directory)
        directory.mkdir(parents=True, exist_ok=True)
        torch.save(self.net.state_dict(), directory/'model.pt')
        meta = {'schema': 'candidate-preferences-v3', 'features': list(FEATURE_NAMES),
                'mean': self.mean.tolist(), 'scale': self.scale.tolist(), 'minimum': self.minimum.tolist(),
                'maximum': self.maximum.tolist(), 'assumptions': self.assumptions.to_dict(), 'training': provenance,
                'weights_sha256': hashlib.sha256((directory/'model.pt').read_bytes()).hexdigest()}
        (directory/'metadata.json').write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding='utf-8')

    @classmethod
    def load(cls, directory):
        directory = Path(directory)
        meta = json.loads((directory/'metadata.json').read_text(encoding='utf-8'))
        if meta['schema'] != 'candidate-preferences-v3' or meta['features'] != list(FEATURE_NAMES):
            raise ValueError('Preference model schema mismatch')
        if hashlib.sha256((directory/'model.pt').read_bytes()).hexdigest() != meta['weights_sha256']:
            raise ValueError('Preference model checksum mismatch')
        mean, scale = np.asarray(meta['mean'], dtype=np.float32), np.asarray(meta['scale'], dtype=np.float32)
        if mean.shape != (len(FEATURE_NAMES),) or scale.shape != mean.shape or not np.all(np.isfinite(mean)) or not np.all(np.isfinite(scale)) or np.any(scale <= 0):
            raise ValueError('Invalid preference scaler')
        net = preference_network()
        net.load_state_dict(torch.load(directory/'model.pt', map_location='cpu', weights_only=True))
        return cls(net, mean, scale, meta['minimum'], meta['maximum'], Assumptions(**meta['assumptions']))
