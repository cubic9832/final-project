"""Versioned display/explicit-preference traits; never edits a trained catalog."""
from collections import Counter
from copy import deepcopy
import hashlib
import json
from pathlib import Path

from vehicle_matching.catalog import ROOT
from tools.data.vehicles.build_full_vehicle_traits import estimate_acceleration

CATALOG = ROOT / 'ml/outputs/models/scenario-choices/20261029-v3-broad-taste-10k/catalog.json'
SOURCE = ROOT / 'data/vehicles/full-trait-evidence-20261028/vehicle_traits.json'
OUTPUT = ROOT / 'data/vehicles/scenario-traits-20261030'
DIMENSIONS = ('exterior_sportiness', 'exterior_angularity', 'acceleration_performance')
# Explicit editorial priors for uncovered specifications, not observed photo reviews.
BODY_STYLE = {'SEDAN': (.5, .5), 'SUV': (.5, .5), 'MPV': (0., .5),
              'BOX': (0., 1.), 'PICKUP': (0., 1.), 'HATCHBACK': (.5, .5),
              'WAGON': (.5, .5), 'COUPE': (1., .5), 'CONVERTIBLE': (1., .5),
              'ROADSTER': (1., .5)}


def build():
    cars = json.loads(CATALOG.read_text(encoding='utf-8'))
    source = json.loads(SOURCE.read_text(encoding='utf-8'))['vehicles']
    rows = {}
    for car in cars:
        row = deepcopy(source.get(car['id'], {'values': {}, 'evidence': {}}))
        for dimension, value in zip(DIMENSIONS[:2], BODY_STYLE[car['body_type']]):
            if row['values'].get(dimension) is None:
                row['values'][dimension] = value
                row['evidence'][dimension] = {
                    'kind': 'editorial-body-prior', 'value': value,
                    'basis': f"미수집 사양의 {car['body_type']} 차체 분류에 따른 자체 기준값",
                    'method': 'body-style-prior-v1', 'checked_on': '2026-10-30',
                    'inputs': {'body_type': car['body_type']},
                    'limitation': '사진을 검토한 개별 모델 평가가 아닌 차체별 가정. 실제 디자인과 다를 수 있음.'}
        if row['values'].get('acceleration_performance') is None:
            acceleration = estimate_acceleration(car)
            acceleration['checked_on'] = '2026-10-30'
            row['evidence']['acceleration_performance'] = acceleration
            row['values']['acceleration_performance'] = min(1., max(0., (12 - acceleration['seconds_0_100']) / 10))
        # Current catalog identity wins over historical metadata. Cost fields stay untouched.
        row['identity'] = {key: car[key] for key in ('brand', 'model', 'trim', 'year')}
        rows[car['id']] = row
    report = {'catalog_count': len(cars), 'catalog_sha256': hashlib.sha256(CATALOG.read_bytes()).hexdigest(),
              'source_sha256': hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
              'coverage': {key: sum(row['values'].get(key) is not None for row in rows.values()) for key in DIMENSIONS},
              'evidence_counts': {key: dict(Counter(row['evidence'][key]['kind'] for row in rows.values())) for key in DIMENSIONS}}
    assert all(count == len(cars) for count in report['coverage'].values())
    OUTPUT.mkdir(parents=True, exist_ok=True)
    for filename, data in [('vehicle_traits.json', {'schema': 'scenario-traits-v1', 'vehicles': rows}), ('coverage_report.json', report)]:
        (OUTPUT / filename).write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(report, ensure_ascii=False))


if __name__ == '__main__':
    build()
