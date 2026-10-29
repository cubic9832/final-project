"""Shared evidence masks and features for generation, training and inference."""
from vehicle_matching.body_types import matches_body_preference
from vehicle_matching.preferences import SIZE_BANDS

DIMENSIONS = ('exterior_sportiness', 'exterior_angularity', 'interior_minimalism',
              'ride_comfort', 'acceleration_performance', 'seat_capacity', 'compactness')
PURPOSES = ('commute', 'family', 'camping', 'weekend-drive', 'business')
PURPOSE_DIMENSIONS = ('compactness', 'seat_capacity', None, 'acceleration_performance', 'ride_comfort')
FEATURE_NAMES = tuple(f'{name}_match' for name in DIMENSIONS) + (
    'purpose_match', 'body_match', 'fuel_match', 'size_match', 'brand_match', 'asset_retention')
DATASET_SCHEMA = 'lifestyle-choice-v3-million'


def encode(taste, attributes, car, retention):
    values = attributes['values']
    matches = [0 if values[name] is None or taste['targets'].get(name) is None
               else 1 - abs(taste['targets'][name] - values[name]) for name in DIMENSIONS]
    purpose_dimension = dict(zip(PURPOSES, PURPOSE_DIMENSIONS)).get(taste.get('purpose'))
    purpose = values.get(purpose_dimension) or 0
    body = float(matches_body_preference(taste.get('body_type', 'any'), attributes['body_type']))
    fuel = 'HYBRID' if car.get('original_fuel') == 'PHEV' else car.get('fuel')
    fuel_match = float(fuel == taste.get('fuel'))
    size = 0
    if taste.get('size') in SIZE_BANDS and values['compactness'] is not None and car.get('length_mm') is not None:
        lower, upper = SIZE_BANDS[taste['size']]
        size = max(0, 1 - max(lower - car['length_mm'], car['length_mm'] - upper, 0) / 1000)
    brand = float(taste.get('brand') == car['brand'])
    return matches + [purpose, body, fuel_match, size, brand, retention]


def comparison_mask(taste, a, b, eligible, car_a=None, car_b=None):
    masks = [int(taste['targets'].get(name) is not None and a['values'][name] is not None
                 and b['values'][name] is not None) for name in DIMENSIONS]
    dimension = dict(zip(PURPOSES, PURPOSE_DIMENSIONS)).get(taste.get('purpose'))
    purpose_known = dimension is not None and a['values'][dimension] is not None and b['values'][dimension] is not None
    return masks + [int(purpose_known), int(taste.get('body_type') not in (None, 'any') and a['body_type'] is not None and b['body_type'] is not None),
                    int(taste.get('fuel') is not None and car_a is not None and car_b is not None and car_a.get('fuel') is not None and car_b.get('fuel') is not None),
                    int(taste.get('size') in SIZE_BANDS and a['values']['compactness'] is not None and b['values']['compactness'] is not None
                        and car_a is not None and car_b is not None and car_a.get('length_mm') is not None and car_b.get('length_mm') is not None),
                    int(taste.get('brand') is not None), int(eligible)]


def effective_weights(importance, masks):
    weights = [weight * mask for weight, mask in zip(importance, masks)]
    weights[-1] = min(weights[-1], .2 * sum(weights[:-1]))
    return weights


def comparison_channels(a, b):
    channels = [name for name in DIMENSIONS if a['values'][name] is not None
                and b['values'][name] is not None and a['values'][name] != b['values'][name]]
    if a['body_type'] is not None and b['body_type'] is not None and a['body_type'] != b['body_type']:
        channels.append('body_type')
    return channels


def score(features, weights):
    total = sum(weights)
    return sum(a * b for a, b in zip(features, weights)) / total if total else 0
