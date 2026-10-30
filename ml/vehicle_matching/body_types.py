"""Explicit model registry: no name/length heuristics and no SUV fallback."""
import json
from dataclasses import replace
from vehicle_matching.catalog import ROOT

LEGACY_BODY_TYPES = ('SEDAN', 'SUV', 'HATCHBACK', 'WAGON', 'MPV', 'BOX', 'PICKUP')
SPORTS_BODY_TYPES = ('COUPE', 'CONVERTIBLE', 'ROADSTER')
BODY_TYPES = (*LEGACY_BODY_TYPES, *SPORTS_BODY_TYPES)

OTHER_BODY_TYPES = ('HATCHBACK', 'WAGON', 'MPV', 'BOX', 'PICKUP', *SPORTS_BODY_TYPES)


def matches_body_preference(preferred, actual):
    if preferred == 'any':
        return True
    return actual in OTHER_BODY_TYPES if preferred == 'OTHER' else preferred == actual


OTHER_BODY_TYPES = ('HATCHBACK', 'WAGON', 'MPV', 'BOX', 'PICKUP')


def matches_body_preference(preferred, actual):
    if preferred == 'any':
        return True
    return actual in OTHER_BODY_TYPES if preferred == 'OTHER' else preferred == actual


def apply_body_types(vehicles, strict=True):
    registry = json.loads((ROOT/'data/vehicles/body-type-registry-v1.json').read_text(encoding='utf-8'))
    entries = {(row['brand'], row['model']): row for row in registry['models']}
    result = []
    for vehicle in vehicles:
        entry = entries.get((vehicle.brand, vehicle.model))
        if entry is None:
            if strict:
                raise ValueError(f'Unverified body type: {vehicle.brand} {vehicle.model}')
            result.append(vehicle)
            continue
        if entry['body_type'] not in BODY_TYPES or not entry['source_urls']:
            raise ValueError('Body type or source missing')
        result.append(replace(vehicle, body_type=entry['body_type'], body_source_urls=tuple(entry['source_urls'])))
    return result
