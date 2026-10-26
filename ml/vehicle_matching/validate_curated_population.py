"""Independently audit persisted data and explicit one-won financial boundaries."""
import argparse
import csv
import json
from collections import Counter
from dataclasses import replace
from pathlib import Path

from vehicle_matching.api import load_service
from vehicle_matching.finance import Profile, assess
from vehicle_matching.partition_preference_population import digest
from vehicle_matching.refine_population import verify_saved
from vehicle_matching.train_preference_population import independent_eligible


def boundary_cases(directory,vehicles):
    fields=['차량번호','경계유형','월소득_원','월생활지출_원','구매유지예금_원','기대적격','실제적격']
    count=0
    with (directory/'financial_boundary_cases.csv').open('w',encoding='utf-8-sig',newline='') as stream:
        writer=csv.DictWriter(stream,fieldnames=fields);writer.writeheader()
        for car in vehicles:
            base=Profile(monthly_income=5000000,monthly_expenses=1000000,existing_monthly_payment=0,liquid_assets=0,
                         down_payment=0,emergency_reserve=0,monthly_savings=0,annual_distance=15000,months=0,
                         annual_rate=0,financing_mode='recommendation')
            for delta in (-1,0,1):
                cash=int(car.price)+delta
                profile=replace(base,liquid_assets=cash)
                cost=assess(profile,car);expected=delta>=0
                assert cost['eligible']==expected==independent_eligible(profile,car,cost)
                writer.writerow(dict(zip(fields,[car.id,f'구매가격{delta:+}',5000000,1000000,cash,int(expected),int(cost['eligible'])])));count+=1
            cost=assess(base,car);running=int(cost['monthly_running_cost'])
            for net in (0,-1000000):
                boundary=int(car.price)+12*(running-net)
                for delta in (-1,0,1):
                    profile=replace(base,monthly_income=1000000,monthly_expenses=1000000-net,liquid_assets=boundary+delta)
                    cost=assess(profile,car);expected=delta>=0
                    assert cost['eligible']==expected==independent_eligible(profile,car,cost)
                    writer.writerow(dict(zip(fields,[car.id,f'12개월예금소진_월차액{net}_{delta:+}',1000000,1000000-net,boundary+delta,int(expected),int(cost['eligible'])])));count+=1
    return count


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--data-dir',type=Path,required=True);parser.add_argument('--model-dir',type=Path,required=True)
    args=parser.parse_args();report=json.loads((args.data_dir/'refinement_report.json').read_text(encoding='utf-8'))
    # Present amounts without meaningless .0 decimals; model arrays retain precision.
    for filename in ('training.csv','validation.csv','evaluation.csv','financial_validation.csv'):
        path=args.data_dir/filename
        with path.open(encoding='utf-8-sig',newline='') as stream:
            reader=csv.DictReader(stream);fields=reader.fieldnames;rows=list(reader)
        for row in rows:
            for key in fields:
                if key.endswith('_원'):
                    value=float(row[key]);assert value.is_integer();row[key]=str(int(value))
        with path.open('w',encoding='utf-8-sig',newline='') as stream:
            writer=csv.DictWriter(stream,fieldnames=fields);writer.writeheader();writer.writerows(rows)
    service=load_service(args.model_dir)
    audit=verify_saved(args.data_dir,service.vehicles,report)
    audit['boundary_cases']=boundary_cases(args.data_dir,service.vehicles)
    audit['boundary_violations']=0
    coverage=Counter()
    with (args.data_dir/'financial_validation.csv').open(encoding='utf-8-sig',newline='') as rows, (args.data_dir/'financial_profiles.jsonl').open(encoding='utf-8') as profiles:
        for row,line in zip(csv.DictReader(rows),profiles,strict=True):
            key=(row['분류사유'],row['데이터구분'])
            if coverage[key]>=5:continue
            p=Profile(**json.loads(line)['profile'])
            recommendations=service.recommend(p,k=9)['recommendations']
            assert len(recommendations)==int(row['기대최대추천대수'])
            for recommendation in recommendations:
                car=next(car for car in service.vehicles if car.id==recommendation['vehicle']['id'])
                assert independent_eligible(p,car,recommendation['cost'])
            coverage[key]+=1
    audit['financial_service_cases']=sum(coverage.values())
    audit['financial_service_violations']=0
    (args.data_dir/'validation_report.json').write_text(json.dumps(audit,ensure_ascii=False,indent=2),encoding='utf-8')
    report['output_hashes']={path.name:digest(path) for path in args.data_dir.iterdir() if path.is_file() and path.name!='refinement_report.json'}
    for path in (args.data_dir/'refinement_report.json',args.model_dir/'report.json'):
        path.write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(audit,ensure_ascii=False),flush=True)


if __name__=='__main__':main()
