"""Keep the original ownership catalog when expanding recommendation candidates."""
import hashlib
import json
from dataclasses import replace

from vehicle_matching.catalog import ROOT, Vehicle

LEGACY_CATALOGS = (
    ROOT / 'data/households/synthetic/owner-funded/configuration-catalog.json',
    ROOT / 'data/households/synthetic/imported-owners/configuration-catalog.json',
)


def expand_catalog(vehicles):
    merged = {vehicle.id: vehicle for vehicle in vehicles}
    added = []
    for path in LEGACY_CATALOGS:
        count = 0
        for row in json.loads(path.read_text(encoding='utf-8')):
            year = str(row['model_year']) if row.get('model_year') else ''
            identity = [row['brand'], row['model'], year, row['trim'], row['powertrain'],
                        str(row.get('default_wheel_inches') or '')]
            candidate_id = 'V-' + hashlib.sha256(json.dumps(identity, ensure_ascii=False).encode()).hexdigest()[:16]
            fuel = {'MILD_HYBRID': 'GASOLINE', 'PHEV': 'GASOLINE'}.get(row['fuel'], row['fuel'])
            if not fuel and row['brand'] == '기아' and row['model'] == '모닝' and row['powertrain'].lower() == 'g 1.0':
                fuel = 'GASOLINE'
            existing = merged.get(candidate_id)
            if existing and existing.price == row['price_won'] and existing.fuel == fuel:
                continue
            # Conflicting historical price/configuration is retained with its own provenance.
            legacy_id = 'legacy-' + row['configuration_id']
            if legacy_id in merged:
                continue
            vehicle = Vehicle(
                id=legacy_id, brand=row['brand'], model=row['model'], trim=row['trim'], year=year,
                price=row['price_won'], fuel=fuel, efficiency=None,
                source_url=row['source_url'], checked_on=row.get('checked_on') or '기존 자료 · 확인일 미기록',
                quality='legacy-price-snapshot', original_fuel=row['fuel'],
                source_note=row.get('source_period_note') or '기존 보유자 데이터 차량 사양 보존',
            )
            merged[legacy_id] = vehicle
            count += 1
        added.append({'source': str(path.relative_to(ROOT)), 'added': count,
                      'sha256': hashlib.sha256(path.read_bytes()).hexdigest()})
    supplement_path = ROOT / 'data/vehicles/official-candidate-supplement-v1.json'
    supplement = json.loads(supplement_path.read_text(encoding='utf-8'))
    count = 0
    for row in supplement['vehicles']:
        values = {**row, 'seat_options': tuple(row.get('seat_options', ())) }
        vehicle = Vehicle(**values)
        existing = merged.get(vehicle.id)
        if existing is not None:
            if any(getattr(existing, key) != getattr(vehicle, key)
                   for key in ('brand', 'model', 'trim', 'year', 'price', 'fuel', 'source_url')):
                raise ValueError(f'Supplement identity conflict: {vehicle.id}')
            # Official supplemental specifications also enrich saved training snapshots.
            fields = ('efficiency', 'length_mm', 'space_source_url', 'seats',
                      'seat_options', 'seats_source_url', 'seats_status', 'source_note')
            updates = {key: getattr(vehicle, key) for key in fields
                       if getattr(vehicle, key) is not None and getattr(vehicle, key) != ()}
            merged[vehicle.id] = replace(existing, **updates)
            continue
        merged[vehicle.id] = vehicle
        count += 1
    added.append({'source': str(supplement_path.relative_to(ROOT)), 'added': count,
                  'sha256': hashlib.sha256(supplement_path.read_bytes()).hexdigest()})
    return list(merged.values()), {'sources': added, 'total': len(merged),
                                  'models': len({(v.brand, v.model) for v in merged.values()})}
