"""Build whole-catalog photo assessments and explicitly synthetic acceleration.

Run with PYTHONPATH=ml from the repository root. Never modifies financial data.
"""
import csv
import hashlib
import json
import math
from collections import Counter
from pathlib import Path

from vehicle_matching.catalog import ROOT
from tools.data.vehicles.lifestyle_traits import build_traits
from tools.data.households.generate_preference_cohorts import add_acceleration_evidence

OUTPUT = ROOT / 'data/vehicles/full-trait-evidence-20261028'
CATALOG = ROOT / 'data/households/synthetic/preference-cohorts-training-20261028/catalog.json'
DETAILS = ROOT / 'data/vehicles/new-model-details-20261028/vehicle-details.json'
NORMALIZED = ROOT / 'data/vehicles/normalized-vehicle-details.json'
METHOD = 'synthetic-body-fuel-engine-prior-v1'
# Declared dummy-data assumptions, not measured segment averages.
BODY_SECONDS = {'SEDAN':10.5, 'SUV':11.5, 'MPV':14, 'BOX':16,
                'HATCHBACK':12, 'HATCH':12, 'WAGON':10.5,
                'COUPE':8, 'CONVERTIBLE':8.5, 'ROADSTER':7.5}
FUEL_FACTORS = {'ELECTRIC':.78, 'EV':.78, 'HYBRID':.92, 'LPG':1.1, 'DIESEL':1.05}


def read(path):
    return json.loads(path.read_text(encoding='utf-8'))


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write(path, data):
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding='utf-8')


def estimate_acceleration(car, specification=None):
    """Deterministic uncalibrated prior; price, brand and photo scores excluded."""
    body, fuel = car.get('body_type'), car.get('fuel')
    inputs = {'body_type':body, 'fuel':fuel,
              'assumed_body_seconds':BODY_SECONDS.get(body, 12),
              'assumed_fuel_factor':FUEL_FACTORS.get(fuel, 1)}
    seconds = inputs['assumed_body_seconds'] * inputs['assumed_fuel_factor']
    if specification:
        displacement = specification.get('displacement_cc')
        weight = specification.get('curb_weight_kg')
        if isinstance(displacement, (int, float)) and 500 <= displacement <= 10000:
            inputs['displacement_cc'] = displacement
            seconds *= math.sqrt(1600 / displacement)
        if isinstance(weight, (int, float)) and 500 <= weight <= 5000:
            inputs['curb_weight_kg'] = weight
            inputs['assumed_reference_weight_kg'] = 1800 if body in ('SUV','MPV','BOX') else 1500
            seconds *= math.sqrt(weight / inputs['assumed_reference_weight_kg'])
        if len(inputs) > 4:
            inputs['specification_source_url'] = specification.get('efficiency_source_url') or specification.get('source_url')
    seconds = round(min(25, max(3, seconds)), 1)
    return {'kind':'estimated-acceleration', 'seconds_0_100':seconds,
        'heuristic_range_seconds':[round(max(1, seconds*.6),1), round(seconds*1.4,1)],
        'method':METHOD, 'inputs':inputs, 'checked_on':'2026-10-28',
        'basis':'차체·연료 가정에 식별 가능한 배기량·공차중량만 보정한 합성 데이터용 사전값',
        'limitation':'실측·학습으로 검증하지 않은 더미 값. 범위는 통계적 신뢰구간이 아님. 출력·변속기·구동·타이어 차이 미반영.',
        'source_url':None, 'confidence':'low; unvalidated synthetic assumption'}


def match_specification(car, rows):
    """Price disambiguates identity only; never enters the estimator."""
    matches = [row for row in rows if
        (row.get('brand'),row.get('model'),row.get('trim'),str(row.get('model_year') or '')) ==
        (car.get('brand'),car.get('model'),car.get('trim'),str(car.get('year') or ''))
        and row.get('price_won') == car.get('price')]
    return matches[0] if len(matches) == 1 else None


def visual_reviews():
    index = read(OUTPUT/'visual-review-index.json')
    corrected = OUTPUT/'sources/electrified-gv70-side.png'
    for row in index:
        if row['model'] == 'Electrified GV70':
            row.update(image_path=corrected.relative_to(ROOT).as_posix(), image_sha256=digest(corrected),
                source_url='https://www.genesis.com/kr/ko/models/electrified-gv70',
                source_image_url='https://dams.hyundai-autoever.com/cdn-cgi/image/width=708,height=400,fit=cover,quality=85,format=auto/v1/openapi/hmg-presigned-url/50534b313031303030303030303030303134383131/models/electrified-gv70/2027/exterior/genesis-electrified-gv70-exterior-detail-sideprofile-large.png',
                correction='Original registry asset depicted a sedan; reviewed replacement is the official SUV side profile.')
    by_number = {row['number']:row for row in index}
    assessments = read(OUTPUT/'visual-assessments.json')['rows']
    if len(assessments) != len(index) or len({r[0] for r in assessments}) != len(index):
        raise ValueError('Missing or duplicate family assessment')
    reviews = []
    for number,sport,angular,basis in assessments:
        source = by_number[number]
        reviews.append({'brand':source['brand'], 'model':source['model'],
            'scope':source['scope'], 'traits':{name:{'kind':'visual-review', 'value':value,
                'basis':basis, 'source_url':source['source_url'], 'image_path':source['image_path'],
                'image_sha256':source['image_sha256'], 'checked_on':'2026-10-28',
                'limitation':'대표 모델 사진의 주관적 3단계 평가. 트림·연식별 실물 검증이나 디자인 품질 점수가 아님.'}
                for name,value in [('exterior_sportiness',sport),('exterior_angularity',angular)]}})
    write(OUTPUT/'reviewed-image-index.json', index)
    return {'rubric':{'exterior_sportiness':'0 높고 직립 / 0.5 혼합 / 1 낮고 스포티한 비례',
        'exterior_angularity':'0 곡면 / 0.5 혼합 / 1 각진 윤곽'}, 'reviews':reviews}


def build():
    cars = read(CATALOG)
    reviews = visual_reviews()
    write(OUTPUT/'visual-reviews.json', reviews)
    traits = add_acceleration_evidence(cars, build_traits(cars,reviews), read(DETAILS))
    for review in read(OUTPUT/'official-acceleration-reviews.json')['reviews']:
        for car in cars:
            if (car['brand'],car['model']) != (review['brand'],review['model']) or car['trim'] not in review['trims'] or str(car.get('year')) not in review['years']:
                continue
            row = traits[car['id']]
            previous = row['evidence'].get('acceleration_performance')
            if previous and previous['seconds_0_100'] != review['seconds_0_100']:
                raise ValueError('Conflicting official acceleration')
            row['evidence']['acceleration_performance'] = dict(review,kind='official-acceleration',checked_on='2026-10-28')
            row['values']['acceleration_performance'] = min(1,max(0,(12-review['seconds_0_100'])/10))
    specifications = read(NORMALIZED)['vehicle_details']
    for car in cars:
        row = traits[car['id']]
        if row['values']['acceleration_performance'] is None:
            evidence = estimate_acceleration(car,match_specification(car,specifications))
            row['evidence']['acceleration_performance'] = evidence
            row['values']['acceleration_performance'] = min(1,max(0,(12-evidence['seconds_0_100'])/10))
    columns = ['id','brand','model','trim','year','body_type','exterior_sportiness','exterior_angularity',
        'visual_basis','visual_source_url','acceleration_status','official_0_100_seconds',
        'estimated_0_100_seconds','heuristic_range_seconds','acceleration_source_url','acceleration_method','acceleration_inputs']
    with (OUTPUT/'vehicle-traits.csv').open('w',encoding='utf-8-sig',newline='') as stream:
        writer = csv.DictWriter(stream,fieldnames=columns); writer.writeheader()
        for car in cars:
            row = traits[car['id']]; acceleration = row['evidence']['acceleration_performance']
            estimated = acceleration['kind']=='estimated-acceleration'
            visual = row['evidence']['exterior_sportiness']
            writer.writerow({**{key:car.get(key) for key in columns[:5]},'body_type':row['body_type'],
                **{key:row['values'][key] for key in columns[6:8]},
                'visual_basis':visual['basis'],'visual_source_url':visual['source_url'],
                'acceleration_status':'estimated' if estimated else 'official',
                'official_0_100_seconds':None if estimated else acceleration['seconds_0_100'],
                'estimated_0_100_seconds':acceleration['seconds_0_100'] if estimated else None,
                'heuristic_range_seconds':json.dumps(acceleration.get('heuristic_range_seconds')) if estimated else None,
                'acceleration_source_url':acceleration.get('source_url'), 'acceleration_method':acceleration.get('method'),
                'acceleration_inputs':json.dumps(acceleration.get('inputs'),ensure_ascii=False) if estimated else None})
    write(OUTPUT/'vehicle_traits.json',{'schema':'full-vehicle-traits-v1','vehicles':traits})
    write(OUTPUT/'catalog-with-traits.json',[dict(car,lifestyle_traits=traits[car['id']]) for car in cars])
    counts = Counter(row['evidence']['acceleration_performance']['kind'] for row in traits.values())
    report = {'catalog_count':len(cars),'model_families':len(reviews['reviews']),
        'coverage':{name:sum(row['values'][name] is not None for row in traits.values()) for name in next(iter(traits.values()))['values']},
        'acceleration_kinds':dict(counts),'method':METHOD,
        'sources':{p.relative_to(ROOT).as_posix():digest(p) for p in
            [CATALOG,DETAILS,NORMALIZED,OUTPUT/'visual-assessments.json',OUTPUT/'reviewed-image-index.json',OUTPUT/'official-acceleration-reviews.json',Path(__file__)]},
        'outputs':{name:digest(OUTPUT/name) for name in ['vehicle_traits.json','catalog-with-traits.json','vehicle-traits.csv','visual-reviews.json']}}
    write(OUTPUT/'generation-report.json',report)
    print(json.dumps(report,ensure_ascii=False))


if __name__ == '__main__':
    build()
