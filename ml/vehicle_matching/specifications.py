"""Apply identity-checked official specification additions to runtime catalogs."""
import json
from dataclasses import replace
from vehicle_matching.catalog import ROOT

DEFAULT_EVIDENCE = ROOT / 'data/vehicles/candidate-specifications-v1.json'


def apply_specifications(vehicles, path=DEFAULT_EVIDENCE):
    rows=json.loads(path.read_text(encoding='utf-8'))['vehicles']
    lookup={r['id']:r for r in rows}
    if len(lookup)!=len(rows):raise ValueError('Duplicate specification identity')
    result=[]
    for vehicle in vehicles:
        row=lookup.get(vehicle.id)
        if row is None:
            result.append(vehicle);continue
        if any(getattr(vehicle,key)!=row[key] for key in ('brand','model','trim','price')) or vehicle.fuel not in (row['fuel'],row['updates'].get('fuel',row['fuel'])):
            raise ValueError(f'Specification identity mismatch: {vehicle.id}')
        updates={}
        for key,value in row['updates'].items():
            if key not in ('efficiency','length_mm','space_source_url','seats','seat_options','seats_source_url','seats_status','fuel','original_fuel','source_note','default_configuration','efficiency_reference_only'):
                raise ValueError(f'Unsupported specification field: {key}')
            previous=row.get('corrections',{}).get(key)
            if previous is not None and getattr(vehicle,key) not in (previous,value,None):
                raise ValueError(f'Unexpected previous specification: {vehicle.id} {key}')
            linked_source=(key=='space_source_url' and 'length_mm' in updates) or (key=='seats_source_url' and 'seats' in updates)
            if getattr(vehicle,key) is None or previous is not None or linked_source or key=='efficiency_reference_only' or (key=='seat_options' and not vehicle.seat_options):
                updates[key]=tuple(value) if key=='seat_options' else value
        result.append(replace(vehicle,**updates))
    return result


def apply_base_specifications(vehicles):
    """Use the same registered size/seating evidence in training and inference."""
    evidence = json.loads((ROOT / 'data/vehicles/candidate-space-evidence.json').read_text(encoding='utf-8'))['vehicles']
    lookup = {(row['brand'], row['model']): row for row in evidence}
    vehicles = [replace(v, length_mm=lookup[(v.brand, v.model)]['length_mm'],
                        space_source_url=lookup[(v.brand, v.model)]['source_url'])
                if (v.brand, v.model) in lookup else v for v in vehicles]
    seating = json.loads((ROOT / 'data/vehicles/candidate-seating-evidence.json').read_text(encoding='utf-8'))['vehicles']
    seats_lookup = {(row['brand'], row['model']): row for row in seating}
    vehicles = [replace(v, seats=seats_lookup[(v.brand, v.model)]['seats'],
                        seat_options=tuple(seats_lookup[(v.brand, v.model)]['seat_options']),
                        length_mm=v.length_mm or seats_lookup[(v.brand, v.model)].get('length_mm'),
                        space_source_url=v.space_source_url or (seats_lookup[(v.brand, v.model)]['source_url'] if seats_lookup[(v.brand, v.model)].get('length_mm') else None),
                        seats_source_url=seats_lookup[(v.brand, v.model)]['source_url'])
                if (v.brand, v.model) in seats_lookup else v for v in vehicles]
    return vehicles
