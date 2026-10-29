"""Apply reviewed web evidence without modifying frozen financial source data."""
import csv
from collections import Counter

from tools.data.vehicles.complete_vehicle_specifications import ROOT,FIELDS,read,write,digest
from tools.data.vehicles.recheck_vehicle_evidence import apply_reviews

BASE=ROOT/'data/vehicles/complete-specifications-20261028'
OUTPUT=ROOT/'data/vehicles/web-recheck-20261028'


def main():
    files=[OUTPUT/name for name in ('reviewed-evidence.json','additional-reviewed-evidence.json','luxury-reviewed-evidence.json','final-reviewed-evidence.json','official-dimension-reviews.json')]
    registry={'reviews':[review for path in files for review in read(path)['reviews']]}
    originals=read(BASE/'vehicles.json')
    vehicles,changes,decisions=apply_reviews(originals,registry)
    traits=read(BASE/'vehicle_traits.json')['vehicles']
    for car in vehicles:
        specs=car['specifications'];row=traits[car['id']];row['specifications']=specs
        for raw,name,transform in [('length_mm','compactness',lambda x:min(1,max(0,(6000-x)/3500))),
            ('seats','seat_capacity',lambda x:min(1,max(0,(x-2)/7)))]:
            if 'previous_estimate' in specs[raw]:
                row['values'][name]=transform(float(specs[raw]['value']))
                row['evidence'][name]=dict(specs[raw],kind='web-rechecked-purpose-proxy',raw_field=raw,
                    limitation='취향 비교 참고값. 원본 재무·필수 정원 검증 증거로 승격하지 않음.')
        acceleration=specs['seconds_0_100']
        if 'previous_estimate' in acceleration:
            row['values']['acceleration_performance']=min(1,max(0,(12-acceleration['value'])/10))
            row['evidence']['acceleration_performance']=dict(acceleration,
                kind='official-acceleration-rechecked' if acceleration['status']=='official-reference' else 'cross-site-acceleration',
                seconds_0_100=acceleration['value'])
    write(OUTPUT/'vehicles.json',vehicles)
    write(OUTPUT/'vehicle_traits.json',{'schema':'web-rechecked-vehicle-traits-v1','vehicles':traits})
    write(OUTPUT/'changes.json',changes)
    write(OUTPUT/'review-decisions.json',decisions)
    fetch_audit=read(OUTPUT/'official-fetch-audit.json')
    reviewed={(r['brand'],r['model']) for r in fetch_audit['families']}
    reviewed.update((r['selector']['brand'],r['selector']['model']) for r in registry['reviews'])
    reviewed.update((r['brand'],r['model']) for r in read(OUTPUT/'held-family-reviews.json')['families'])
    write(OUTPUT/'remaining-estimates.json',[
        {'id':car['id'],'brand':car['brand'],'model':car['model'],'trim':car['trim'],
            'field':field,'value':spec['value'],'status':'estimated',
            'reason':'이 항목을 대체할 동일 조건의 공식/3출처 근거가 이번 검토 자료에서 확정되지 않음.'}
        for car in vehicles for field,spec in car['specifications'].items() if spec['status']=='estimated'])
    with (OUTPUT/'vehicles.csv').open('w',encoding='utf-8-sig',newline='') as stream:
        names=['id','brand','model','trim']+[key+suffix for key in FIELDS for suffix in ('','_status','_source_count','_sources')]
        writer=csv.DictWriter(stream,fieldnames=names);writer.writeheader()
        for car in vehicles:
            flat={key:car[key] for key in names[:4]}
            for key,spec in car['specifications'].items():
                sources=[s['url'] for s in spec.get('sources',[])] or ([spec['source_url']] if spec.get('source_url') else [])
                flat.update({key:spec['value'],key+'_status':spec['status'],key+'_source_count':spec.get('source_count',len(sources)),key+'_sources':' | '.join(sources)})
            writer.writerow(flat)
    changed={(r['brand'],r['model']) for r in changes}
    report={'vehicles':len(vehicles),'fields':len(FIELDS),'missing_values':sum(s['value'] in (None,'') for car in vehicles for s in car['specifications'].values()),
        'families_with_recorded_web_review':len(reviewed),
        'changed_fields':len(changes),'changed_vehicles':len({r['id'] for r in changes}),
        'changed_families':len(changed),'replacement_status_counts':dict(Counter(r['status'] for r in changes)),
        'decisions':dict(Counter(r['result'] for r in decisions)),
        'remaining_estimated_fields':sum(s['status']=='estimated' for car in vehicles for s in car['specifications'].values()),
        'sources':{p.relative_to(ROOT).as_posix():digest(p) for p in files+[OUTPUT/'official-fetch-audit.json',OUTPUT/'held-family-reviews.json',BASE/'vehicles.json',BASE/'vehicle_traits.json',
            ROOT/'tools/data/vehicles/recheck_vehicle_evidence.py',ROOT/'tools/data/vehicles/build_rechecked_specifications.py']},
        'outputs':{name:digest(OUTPUT/name) for name in ('vehicles.json','vehicle_traits.json','vehicles.csv','changes.json','review-decisions.json')},
        'scope':'Official scoped references or >=3 publication consensus replace only synthetic fields. Reported specs do not assert independent measurement. Unresolved estimates stay labelled; financial catalog unchanged.'}
    write(OUTPUT/'recheck-report.json',report)
    print({k:report[k] for k in ('vehicles','changed_fields','changed_vehicles','changed_families','replacement_status_counts','remaining_estimated_fields','missing_values')})


if __name__=='__main__':
    main()
