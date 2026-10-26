"""Export the enriched catalog and audit financial boundaries on independent profiles."""
import argparse
import hashlib
import json
import sys
from collections import Counter
from dataclasses import asdict, replace
from pathlib import Path

ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT/'ml'))
from vehicle_matching.api import load_service
from vehicle_matching.catalog import FUELS
from vehicle_matching.dataset import profiles
from vehicle_matching.finance import Profile, assess


def verify(run):
    original=load_service(ROOT/'ml/experiments/candidate-v2',apply_specification_updates=False)
    current=load_service(run)
    assert [(v.id,v.price) for v in original.vehicles]==[(v.id,v.price) for v in current.vehicles]
    def missing(vehicles):
        return {'efficiency':sum(v.efficiency is None for v in vehicles),
                'length_mm':sum(v.length_mm is None for v in vehicles),
                'seating':sum(v.seats is None and not v.seat_options for v in vehicles)}
    assert not any(missing(current.vehicles).values())
    base=Profile(monthly_income=20000000,monthly_expenses=1000000,existing_monthly_payment=0,
                 liquid_assets=300000000,down_payment=0,emergency_reserve=10000000,
                 monthly_savings=1000000,annual_distance=15000,months=0,annual_rate=0,
                 minimum_buffer=500000,financing_mode='recommendation')
    people=profiles(300,99221)
    for price in sorted({v.price for v in current.vehicles}):
        people.extend(replace(base,liquid_assets=price+base.emergency_reserve+offset) for offset in (-1,0))
    for fuel in FUELS:
        for income in (2500000,5000000,10000000):
            people.append(replace(base,monthly_income=income,preferred_fuel=fuel,fuel_importance=5))
    violations=[]; recommendation_count=0; empty=0
    for index,p in enumerate(people):
        result=current.recommend(p)
        recommendations=result['recommendations'];empty+=not recommendations
        recommendation_count+=len(recommendations)
        ids=[(r['vehicle']['brand'],r['vehicle']['model']) for r in recommendations]
        if len(set(ids))!=len(ids):violations.append((index,'duplicate-model'))
        if len(recommendations)!=min(3,result['financialEligibleModelCount']):violations.append((index,'missing-eligible-candidate'))
        for row in recommendations:
            if row['vehicle']['price']>p.liquid_assets-p.emergency_reserve:violations.append((index,'cash-limit'))
            if row['cost']['remaining_monthly']<p.minimum_buffer:violations.append((index,'monthly-buffer'))
            if not row['cost']['eligible']:violations.append((index,'ineligible'))
    patch=ROOT/'data/vehicles/candidate-specifications-v1.json'
    report={'model_run':str(run.relative_to(ROOT)), 'vehicles':len(current.vehicles),
            'models':len({(v.brand,v.model) for v in current.vehicles}),
            'before_missing':missing(original.vehicles),'after_missing':missing(current.vehicles),
            'fuel_counts':dict(Counter(v.fuel for v in current.vehicles)),
            'reference_only':[asdict(v) for v in current.vehicles if v.efficiency_reference_only],
            'registered_seating_not_independently_reverified':sum(v.seats_status=='user-provided' for v in current.vehicles),
            'cases':len(people),'recommendations':recommendation_count,'no_candidates':empty,
            'violations':violations,'specification_sha256':hashlib.sha256(patch.read_bytes()).hexdigest()}
    out=ROOT/'ml/reports/candidate-specifications-v1-audit.json'
    out.write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    (ROOT/'data/vehicles/candidate-catalog-specifications-v1.json').write_text(
        json.dumps([asdict(v) for v in current.vehicles],ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps({k:v for k,v in report.items() if k not in ('reference_only',)},ensure_ascii=False))
    assert not violations,violations[:5]


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--run',type=Path,required=True)
    verify(parser.parse_args().run.resolve())
