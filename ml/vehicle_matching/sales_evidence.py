"""Sales display evidence is separate from frozen training/financial inputs."""
from copy import deepcopy
import json

from vehicle_matching.catalog import ROOT

REGISTRY = ROOT / 'data/vehicles/sales-verification-20261028/vehicles.json'
IDENTITY_FIELDS = ('id', 'brand', 'model', 'trim', 'year')


def load_sales_evidence(catalog, path=REGISTRY):
    records = json.loads(path.read_text(encoding='utf-8'))['vehicles']
    indexed = {record['identity']['id']: record for record in records}
    if len(indexed) != len(records):
        raise ValueError('Duplicate sales evidence identity')
    return {car['id']: deepcopy(indexed[car['id']]) for car in catalog
            if car['id'] in indexed and all(car.get(key) == indexed[car['id']]['identity'].get(key)
                                            for key in IDENTITY_FIELDS)}


def sales_display_specifications(specifications, verification):
    """Never present a synthetic price/year/seating prior as verified sales data."""
    if not verification or not specifications:
        return specifications
    result = deepcopy(specifications)
    for field, key in (('price_won', 'price'), ('model_year', 'year'), ('seats', 'seats')):
        item = verification[key]
        result[field] = {'value': item['value'] if item['value'] is not None else '미확인',
            'status': item['status'], 'basis': item['basis'],
            'sources': [{'url': url, 'publisher': '판매 정보'} for url in item['sources']],
            'training_assumption': specifications.get(field)}
    return result
