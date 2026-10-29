"""Fill a fixed usable specification schema, preserving per-field provenance.

Synthetic assumptions belong to a separate complete snapshot. Original source
catalog and financial eligibility evidence are never overwritten.
"""
import csv
import json
import math
import re
from collections import Counter

from tools.data.vehicles.build_full_vehicle_traits import (
    ROOT, OUTPUT as TRAITS, CATALOG, DETAILS, NORMALIZED, read, write, digest,
    match_specification,
)

OUTPUT = ROOT/'data/vehicles/complete-specifications-20261028'
# Declared synthetic segment assumptions: length, width, height, wheelbase, seats, mass.
BODY = {'SEDAN':(4800,1830,1450,2800,5,1600), 'SUV':(4700,1880,1660,2750,5,1800),
    'COUPE':(4600,1900,1350,2700,4,1600), 'CONVERTIBLE':(4550,1900,1320,2650,2,1700),
    'ROADSTER':(4300,1850,1300,2500,2,1450), 'MPV':(5100,1950,1900,3100,9,2200),
    'BOX':(3600,1600,1700,2500,4,1100), 'HATCHBACK':(4100,1750,1500,2550,5,1250),
    'WAGON':(4750,1830,1480,2800,5,1650)}
FIELDS = ('length_mm','width_mm','height_mm','wheelbase_mm','seats','curb_weight_kg',
    'displacement_cc','power_ps','torque_nm','top_speed_kmh','cargo_litres','ground_clearance_mm',
    'fuel','efficiency','efficiency_unit','price_won','model_year','body_type',
    'transmission','drive','monthly_insurance_won','monthly_tax_won','monthly_maintenance_won',
    'seconds_0_100','exterior_sportiness','exterior_angularity','interior_minimalism','ride_comfort')
DETAIL_LABELS = {
    'length_mm':('전장','Length','Dimensions and Weight · Length'),
    'width_mm':('미러 제외 전폭','전폭 (미러 제외)','Width'),
    'height_mm':('높이','전고','Dimensions and Weight · Height'),
    'wheelbase_mm':('휠베이스','Wheelbase','Dimensions and Weight · Wheelbase'),
    'seats':('정원',), 'curb_weight_kg':('공차중량',),
    'displacement_cc':('배기량','Displacement','Engine · Total displacement'),
    'power_ps':('시스템 합산 출력','Power combined (PS)','최고 출력','최대 출력','Engine · Max Power','Engine · Max Power*'),
    'torque_nm':('Torque combined','Max. torque','Engine · Max Torque*'),
    'top_speed_kmh':('최고 속도','최대 속도','Top speed','Performance · Max Speed'),
    'cargo_litres':('트렁크 용량',),
}


def record(value, status, basis, source=None, **extra):
    return dict(value=value,status=status,basis=basis,source_url=source or '',**extra)


def numeric_detail(details, key):
    for label in DETAIL_LABELS.get(key,()):
        candidates = [r for r in details.get('fields',[]) if r['label']==label and r.get('status')!='source-conflict']
        if len(candidates)!=1:
            continue
        match = re.fullmatch(r'\s*([\d,.]+)\s*(?:mm|kg|cc|cm³|cm3|PS|CV|Nm|명|km/h|l|L)?\s*',candidates[0]['value'])
        if match:
            value = float(match[1].replace(',',''))
            bounds = {'length_mm':(2500,6000),'width_mm':(1300,2300),'height_mm':(900,2600),
                'wheelbase_mm':(1800,4000),'seats':(1,15),'curb_weight_kg':(500,5000),
                'displacement_cc':(500,10000),'power_ps':(30,2000),'torque_nm':(30,2000),
                'top_speed_kmh':(80,450),'cargo_litres':(30,3000)}[key]
            if bounds[0] <= value <= bounds[1]:
                return record(value,'official-reference',label,details['source_url'],limitation='원문 조건·연식·미러 포함 여부를 함께 확인해야 합니다.')
    return None


def complete(car, traits, details, normalized):
    body = car['body_type']; length,width,height,wheelbase,seats,mass = BODY[body]
    fuel = car.get('fuel') or 'GASOLINE'
    estimated = lambda v,b:record(v,'estimated',b,method='synthetic-segment-prior-v1',confidence='low; unvalidated')
    length = car.get('length_mm') or length
    mass = round(mass*(length/BODY[body][0])**1.5)
    displacement = 0 if fuel=='ELECTRIC' else 2000
    power = 230 if fuel=='ELECTRIC' else 170
    defaults = {'length_mm':length,'width_mm':width,'height_mm':height,'wheelbase_mm':round(wheelbase*length/BODY[body][0]),
        'seats':seats,'curb_weight_kg':mass,'displacement_cc':displacement,'power_ps':power,
        'torque_nm':300 if fuel=='ELECTRIC' else 220,'top_speed_kmh':180 if fuel=='ELECTRIC' else 200,
        'cargo_litres':150 if body in ('COUPE','CONVERTIBLE','ROADSTER') else 450,
        'ground_clearance_mm':180 if body in ('SUV','MPV','BOX') else 135,
        'fuel':fuel,'efficiency':4.5 if fuel=='ELECTRIC' else 13 if fuel=='HYBRID' else 10,
        'efficiency_unit':'km/kWh' if fuel=='ELECTRIC' else 'km/L',
        'price_won':150000000 if body in ('COUPE','CONVERTIBLE','ROADSTER') else 50000000,
        'model_year':2026,'body_type':body,'transmission':'단일 감속기' if fuel=='ELECTRIC' else '자동 가정',
        'drive':'구동 방식 미확인 · 전륜 가정','monthly_insurance_won':120000,
        'monthly_tax_won':11000 if fuel=='ELECTRIC' else 40000,'monthly_maintenance_won':80000}
    result = {k:estimated(v,'차체·연료별로 선언한 합성 기본값. 실차 제원 또는 견적이 아님.') for k,v in defaults.items()}
    for key in DETAIL_LABELS:
        value = numeric_detail(details,key)
        if value:
            result[key]=value
    if normalized:
        for key in ('curb_weight_kg','displacement_cc'):
            value = normalized.get(key)
            if isinstance(value,(int,float)) and math.isfinite(value) and value>0:
                result[key]=record(value,'official-reference','정확한 연식·트림·가격으로 식별한 기존 제원',normalized.get('efficiency_source_url') or normalized.get('source_url'))
        for key in ('transmission','drive'):
            if normalized.get(key):
                result[key]=record(normalized[key],'official-reference','기존 정규화 제원',normalized.get('source_url'))
    for key,original,source in [('length_mm','length_mm','space_source_url'),('seats','seats','seats_source_url'),
        ('price_won','price','source_url'),('efficiency','efficiency','source_url'),('fuel','fuel','source_url'),
        ('model_year','year','source_url'),('body_type','body_type','source_url')]:
        value = car.get(original)
        if value is not None and value!='':
            result[key]=record(value,'catalog-reference','기존 차량 원장 값; 원장의 검증 상태를 유지',car.get(source),original_status=car.get('seats_status') if key=='seats' else car.get('quality','reference'))
    for key,labels in [('transmission',('변속기','Transmission','Transmission and Gearbox · Type')),('drive',('구동',))]:
        rows=[f for f in details.get('fields',[]) if f['label'] in labels and f.get('status')!='source-conflict']
        if len(rows)==1:
            result[key]=record(rows[0]['value'],'official-reference',rows[0]['label'],details['source_url'])
    acceleration=traits['evidence']['acceleration_performance']
    if acceleration['kind']=='estimated-acceleration' and result['power_ps']['status']=='official-reference':
        # Explicit power/weight engineering prior when actual power is available.
        # Dry weight is never silently reclassified as measured curb weight.
        power_kw=float(result['power_ps']['value'])*.73549875
        mass_kg=float(result['curb_weight_kg']['value'])
        seconds=round(min(25,max(2,1.3+.593*mass_kg/power_kw)),1)
        acceleration=dict(acceleration,seconds_0_100=seconds,
            heuristic_range_seconds=[round(max(1,seconds*.6),1),round(seconds*1.4,1)],
            method='synthetic-power-weight-prior-v1',
            inputs={'power_kw':power_kw,'power_source':result['power_ps'],
                'mass_kg':mass_kg,'mass_source':result['curb_weight_kg'],
                'formula':'1.3 + 0.593 * mass_kg / power_kw; uncalibrated heuristic'},
            basis='공개 출력과 공차중량(미공개이면 차체별 중량 가정)을 이용한 검증 전 합성 추정')
        traits['evidence']['acceleration_performance']=acceleration
        traits['values']['acceleration_performance']=min(1,max(0,(12-seconds)/10))
    result['seconds_0_100']=record(acceleration['seconds_0_100'],
        'estimated' if acceleration['kind']=='estimated-acceleration' else 'official-reference',
        acceleration.get('basis',acceleration.get('condition','공식 공개 조건의 가속 수치')),
        acceleration.get('source_url'),detail=acceleration)
    for key in ('exterior_sportiness','exterior_angularity'):
        e=traits['evidence'][key]
        result[key]=record(traits['values'][key],'visual-review',e['basis'],e['source_url'])
    # These neutral priors expressly do NOT assert photographed interiors or tested comfort.
    for key in ('interior_minimalism','ride_comfort'):
        result[key]=estimated(.5,'확인 자료가 없어 중립 0.5로 채운 합성 가정. 실제 실내·승차감 평가가 아님.')
    if set(result)!=set(FIELDS) or any(r['value'] is None or r['value']=='' for r in result.values()):
        raise ValueError('Incomplete specification schema')
    return result


def main():
    OUTPUT.mkdir(parents=True,exist_ok=True)
    cars=read(CATALOG); traits=read(TRAITS/'vehicle_traits.json')['vehicles']
    details={r['id']:r for r in read(DETAILS)['vehicles']}
    normalized=read(NORMALIZED)['vehicle_details']
    completed=[]
    for car in cars:
        row=traits[car['id']]
        specifications=complete(car,row,details.get(car['id'],{}),match_specification(car,normalized))
        row['specifications']=specifications
        for key,raw,transform in [('compactness','length_mm',lambda n:min(1,max(0,(6000-n)/3500))),
            ('seat_capacity','seats',lambda n:min(1,max(0,(n-2)/7)))]:
            if row['values'][key] is None:
                spec=specifications[raw]
                row['values'][key]=transform(float(spec['value']))
                row['evidence'][key]=dict(spec,kind='estimated-purpose-proxy',raw_field=raw,
                    limitation='취향 비교에만 사용. 정원·전장 확인이나 구매 적격 증거로 승격하지 않음.')
        for key in ('interior_minimalism','ride_comfort'):
            row['values'][key]=specifications[key]['value']
            row['evidence'][key]=dict(specifications[key],kind='synthetic-neutral-prior')
        if not row.get('body_type'):
            row.update(body_type=car['body_type'],body_sources=[],body_status='estimated-category')
        completed.append({'id':car['id'],'brand':car['brand'],'model':car['model'],'trim':car['trim'],
            'specifications':specifications,'source_identity':{k:car.get(k) for k in ('brand','model','trim','year')}})
    write(OUTPUT/'vehicle_traits.json',{'schema':'complete-vehicle-traits-v1','vehicles':traits})
    write(OUTPUT/'vehicles.json',completed)
    with (OUTPUT/'vehicles.csv').open('w',encoding='utf-8-sig',newline='') as stream:
        fields=['id','brand','model','trim']+[f'{k}{suffix}' for k in FIELDS for suffix in ('','_status','_basis')]
        writer=csv.DictWriter(stream,fieldnames=fields);writer.writeheader()
        for car in completed:
            flat={k:car[k] for k in ('id','brand','model','trim')}
            for k,spec in car['specifications'].items():
                flat.update({k:spec['value'],k+'_status':spec['status'],k+'_basis':spec['basis']})
            writer.writerow(flat)
    report={'vehicles':len(cars),'fields':list(FIELDS),'missing_values':0,
        'field_status_counts':{k:dict(Counter(car['specifications'][k]['status'] for car in completed)) for k in FIELDS},
        'policy':'Synthetic estimates fill usable specifications only. Evidence/source URLs, conflicts and optional metadata are not invented. Financial source catalog and identity remain unchanged.',
        'sources':{p.relative_to(ROOT).as_posix():digest(p) for p in [CATALOG,DETAILS,NORMALIZED,TRAITS/'vehicle_traits.json',ROOT/'tools/data/vehicles/complete_vehicle_specifications.py']},
        'outputs':{name:digest(OUTPUT/name) for name in ('vehicles.json','vehicles.csv','vehicle_traits.json')}}
    write(OUTPUT/'completion-report.json',report)
    print(json.dumps({k:report[k] for k in ('vehicles','missing_values','field_status_counts')}))


if __name__=='__main__':
    main()
