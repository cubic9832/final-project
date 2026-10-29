"""Apply versioned, explicitly scoped seating references to an experiment copy."""
from dataclasses import replace
import json


def apply_registry(catalog, path):
    registry = json.loads(path.read_text(encoding='utf-8'))
    entries = {}
    for entry in registry['entries']:
        key = (entry['brand'], entry['model'])
        if key in entries or type(entry['seats']) is not int or not 1 <= entry['seats'] <= 15:
            raise ValueError('Duplicate selector or invalid seating reference')
        if not entry.get('source_url') or not entry.get('scope') or not entry.get('status'):
            raise ValueError('Seating reference requires source, scope and status')
        entries[key] = entry
    result, changes, matched = [], [], set()
    for vehicle in catalog:
        entry = entries.get((vehicle.brand, vehicle.model))
        if entry is None:
            result.append(vehicle)
            continue
        matched.add((vehicle.brand, vehicle.model))
        if vehicle.seats is not None and vehicle.seats != entry['seats']:
            raise ValueError(f'Conflicting existing seating: {vehicle.id}')
        result.append(replace(vehicle, seats=entry['seats'], seat_options=(),
                      seats_source_url=entry['source_url'], seats_status=entry['status'],
                      seats_label=f'{entry["seats"]}인승 (출처 범위 별도 기록)',
                      seats_note=f'{entry["scope"]} 확인일 {registry["checked_on"]}.'))
        changes.append({'id':vehicle.id,'brand':vehicle.brand,'model':vehicle.model,
                        'previous_seats':vehicle.seats,'seats':entry['seats'],'reference':entry})
    if set(entries) != matched:
        raise ValueError('Seating registry contains unmatched model selectors')
    return result, {'models':len(matched),'specifications':len(changes),'changes':changes}
