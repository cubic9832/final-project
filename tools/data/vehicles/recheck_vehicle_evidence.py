"""Promote synthetic fields using scoped official or three-publisher evidence.

Published specifications and instrumented tests are separate evidence types.
Three URLs never imply three independent physical measurements.
"""
import copy
import math
from statistics import median
from urllib.parse import urlparse

DIMENSIONS = {'length_mm','width_mm','height_mm','wheelbase_mm','ground_clearance_mm'}
NUMERIC_FIELDS = DIMENSIONS | {'seats','curb_weight_kg','displacement_cc','power_ps',
    'torque_nm','top_speed_kmh','cargo_litres','seconds_0_100'}
BOUNDS={'length_mm':(2500,6000),'width_mm':(1300,2300),'height_mm':(900,2600),
    'wheelbase_mm':(1800,4000),'ground_clearance_mm':(50,500),'seats':(1,15),
    'curb_weight_kg':(500,5000),'displacement_cc':(500,10000),'power_ps':(30,2000),
    'torque_nm':(30,3000),'top_speed_kmh':(80,450),'cargo_litres':(30,3000),'seconds_0_100':(1,30)}


def normalized_value(field, sample):
    value = sample['values'][field]
    if isinstance(value,bool) or not isinstance(value,(int,float)) or not math.isfinite(value) or value <= 0:
        raise ValueError('Evidence must contain finite positive numbers')
    unit = sample.get('units',{}).get(field)
    factors = {'inch':25.4,'m':1000,'lb':.45359237,'bhp':1.0138696654,'kW':1.3596216173}
    canonical=('mm' if field in DIMENSIONS else {'seats':'count','curb_weight_kg':'kg',
        'displacement_cc':'cc','power_ps':'PS','torque_nm':'Nm','top_speed_kmh':'km/h',
        'cargo_litres':'L','seconds_0_100':'s'}[field])
    if unit and unit != canonical and unit not in factors:
        raise ValueError('Evidence unit does not match field')
    if unit and unit not in ('mm','kg','PS','Nm','km/h','L','cc','s','count'):
        if unit not in factors or (unit in ('inch','m') and field not in DIMENSIONS) or (unit=='lb' and field!='curb_weight_kg') or (unit in ('bhp','kW') and field!='power_ps'):
            raise ValueError('Unsupported evidence unit conversion')
        value *= factors[unit]
    if not BOUNDS[field][0] <= value <= BOUNDS[field][1]:
        raise ValueError('Implausible evidence value')
    return value


def select_evidence(field, samples):
    """All eligible sources must agree; no cherry-picking a favourable cluster."""
    if field not in NUMERIC_FIELDS:
        return None,'not-a-comparable-numeric-specification'
    eligible=[]
    for sample in samples:
        if field not in sample.get('values',{}) or not sample.get('compatible',False):
            continue
        if sample.get('verification')!='page-reviewed' or not sample.get('conditions'):
            continue
        host=urlparse(sample['url']).hostname
        if not host or not sample.get('publisher') or not sample.get('origin_id'):
            raise ValueError('Reviewed source provenance required')
        eligible.append(dict(sample,normalized_value=normalized_value(field,sample)))
    official=[s for s in eligible if s.get('official')]
    considered=official or eligible
    if not considered:
        return None,'no-compatible-reviewed-source'
    if len({s['evidence_type'] for s in considered})!=1:
        return None,'mixed-test-and-reported-specifications'
    # Contradictory copies still matter, even when they count as one origin.
    all_values=[s['normalized_value'] for s in considered]
    center=median(all_values)
    absolute=10 if field in DIMENSIONS else .4 if field=='seconds_0_100' else 0
    relative=0 if field=='seats' else .005 if field in DIMENSIONS else .05 if field=='seconds_0_100' else .03
    if max(all_values)-min(all_values)>max(absolute,abs(center)*relative)+1e-9:
        return None,'conflicting-values'
    # A regional manufacturer domain or a syndication mirror adds no new origin.
    origins={};publishers=set();hosts=set()
    for sample in considered:
        host=urlparse(sample['url']).hostname.lower().removeprefix('www.')
        if sample['publisher'] in publishers or sample['origin_id'] in origins or host in hosts:
            continue
        hosts.add(host)
        publishers.add(sample['publisher']);origins[sample['origin_id']]=sample
    considered=list(origins.values())
    if not official and len(considered)<3:
        return None,'fewer-than-three-independent-publications'
    values=[s['normalized_value'] for s in considered]; center=median(values)
    measured=considered[0]['evidence_type']=='instrumented-test'
    status='official-reference' if official else 'cross-site-measured' if measured else 'cross-site-reported'
    value=round(center,2 if field=='seconds_0_100' else 1)
    return {'value':value,'status':status,
        'basis':('공식 자료에서 재확인' if official else f'{len(considered)}개 출처의 근접 수치 중앙값'),
        'source_url':considered[0]['url'],'sources':considered,
        'observed_range':[min(values),max(values)],'source_count':len(considered),
        'evidence_type':considered[0]['evidence_type'],'checked_on':'2026-10-28',
        'limitation':'세대·차체·사양 조건 범위의 참고값. 제원표 재확인은 독립 실측 3회와 다름. 구매 적격의 검증 증거로 자동 승격하지 않음.'},'accepted'


def matches(car, selector):
    return all(car.get(k)==selector[k] for k in ('brand','model')) and (
        'trims' not in selector or car['trim'] in selector['trims']) and (
        'ids' not in selector or car['id'] in selector['ids'])


def apply_reviews(cars, registry):
    result=copy.deepcopy(cars);changes=[];decisions=[]
    touched=set()
    for review in registry['reviews']:
        for car in result:
            if not matches(car,review['selector']):
                continue
            for field in sorted(set().union(*(s.get('values',{}) for s in review['samples']))):
                previous=car['specifications'].get(field)
                if not previous or previous['status']!='estimated':
                    continue
                key=(car['id'],field)
                replacement,reason=select_evidence(field,review['samples'])
                decisions.append({'id':car['id'],'field':field,'result':reason})
                if replacement:
                    if key in touched:
                        raise ValueError('Overlapping accepted review selectors')
                    touched.add(key)
                    replacement['previous_estimate']=previous
                    replacement['scope']=review['scope']
                    car['specifications'][field]=replacement
                    changes.append({'id':car['id'],'brand':car['brand'],'model':car['model'],
                        'trim':car['trim'],'field':field,'previous':previous['value'],
                        'value':replacement['value'],'status':replacement['status'],
                        'source_count':replacement['source_count'],'sources':[s['url'] for s in replacement['sources']]})
    return result,changes,decisions
