"""Apply candidate-specific seating registration without changing model weights."""
import json
from dataclasses import replace

from vehicle_matching.catalog import ROOT

DEFAULT_REGISTRY = ROOT / 'data/vehicles/candidate-seating-registry.json'


def apply_seating_registry(vehicles, path=DEFAULT_REGISTRY):
    rows = json.loads(path.read_text(encoding='utf-8'))['vehicles']
    lookup = {row['id']: row for row in rows}
    if len(lookup) != len(rows):
        raise ValueError('Duplicate candidate seating registration')
    result = []
    for vehicle in vehicles:
        row = lookup.get(vehicle.id)
        if row is None:
            result.append(vehicle)
            continue
        if (vehicle.brand, vehicle.model, vehicle.trim, vehicle.price) != (row['brand'], row['model'], row['trim'], row['price']):
            raise ValueError(f'Seating registration identity mismatch: {vehicle.id}')
        result.append(replace(vehicle, seats=row['seats'], seat_options=tuple(row['seat_options']),
                              seats_status=row['status'], seats_label=row['label'], seats_note=row['note'],
                              seats_source_url=row['source_url']))
    return result
