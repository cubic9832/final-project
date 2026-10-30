"""UI-aligned inputs and shared synthetic-choice policy for training/inference."""
import math
import numpy as np
from vehicle_matching.finance import Profile, assess
from vehicle_matching.scenario_features import channel_values

FEATURE_NAMES = ('log_income', 'log_expenses', 'log_debt', 'log_assets', 'log_price', 'log_running',
                 'length', 'seats', 'retention', 'affordability', 'fuel_match', 'fuel_specified',
                 'size_match', 'size_specified', 'angularity_match', 'angularity_specified',
                 'acceleration_match', 'acceleration_specified', 'charging', 'charging_known',
                 'cost_weight', 'retention_weight', 'running_weight', 'fuel_weight', 'size_weight',
                 'design_weight', 'performance_weight', 'weighted_retention', 'weighted_running',
                 'weighted_fuel', 'weighted_size', 'weighted_angularity', 'weighted_acceleration',
                 'fuel_GASOLINE', 'fuel_HYBRID', 'fuel_DIESEL', 'fuel_LPG', 'fuel_ELECTRIC')


def encode_ui_scenario(user, vehicle, traits, cost=None):
    p, prefs = user['profile'], user['preferences']
    profile = Profile(**p)
    cost = cost or assess(profile, vehicle)
    channels = channel_values({'profile': p, 'preferred_brands': [], 'model_affinities': {}}, vehicle, cost)
    retained, affordable, _, fuel, size, _, _, charging = map(float, channels)
    fuel_set, size_set = p['preferred_fuel'] is not None, p['preferred_size'] != 'any'
    angular_set, accel_set = prefs.get('angularity') is not None, prefs.get('acceleration') is not None
    angular = 1 - abs(prefs['angularity'] - traits['values']['exterior_angularity']) if angular_set else .5
    accel = 1 - abs(prefs['acceleration'] - traits['values']['acceleration_performance']) if accel_set else .5
    charging_known = p['preferred_fuel'] == 'ELECTRIC'
    charging = charging if charging_known else .5
    weight = lambda name, default: (prefs.get(name) if prefs.get(name) is not None else default) / 5
    cost_w = p['cost_importance'] / 5
    retention_w = weight('asset_retention_importance', p['cost_importance'])
    running_w = weight('running_cost_importance', p['cost_importance'])
    fuel_w, size_w = p['fuel_importance'] / 5, p['space_importance'] / 5
    design_w, performance_w = weight('design_importance', 3), weight('performance_importance', 3)
    values = [*(math.log1p(p[key]) for key in ('monthly_income', 'monthly_expenses', 'existing_monthly_payment', 'liquid_assets')),
              math.log1p(vehicle.price), math.log1p(cost['monthly_running_cost']), (vehicle.length_mm or 0)/6000,
              (vehicle.seats or 0)/9, retained, affordable, fuel, float(fuel_set), size, float(size_set),
              angular, float(angular_set), accel, float(accel_set), charging, float(charging_known),
              cost_w, retention_w, running_w, fuel_w, size_w, design_w, performance_w,
              retention_w*retained, running_w*affordable, fuel_w*(fuel-.5)*fuel_set,
              size_w*(size-.5)*size_set, design_w*(angular-.5)*angular_set,
              performance_w*(accel-.5)*accel_set,
              *(float(vehicle.fuel == fuel_type) for fuel_type in ('GASOLINE','HYBRID','DIESEL','LPG','ELECTRIC'))]
    return np.asarray(values, dtype=np.float32)


def choice_utility(features):
    """Absolute importance matters relative to cost even with a single taste answer."""
    v = dict(zip(FEATURE_NAMES, features))
    return float(.15*(v['retention']+v['affordability']) + .3*v['cost_weight']*(v['retention']+v['affordability'])
                 + v['weighted_retention'] + v['weighted_running'] + v['weighted_fuel'] + v['weighted_size']
                 + v['weighted_angularity'] + v['weighted_acceleration']
                 + .4*v['charging_known']*(v['charging']-.5))
