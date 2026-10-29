"""Re-read saved sports examples and audit eligibility, labels and split isolation."""
import csv
import json
from collections import Counter
from dataclasses import asdict
from pathlib import Path

from vehicle_matching.catalog import ROOT, read_catalog
from vehicle_matching.finance import Assumptions, Profile
from vehicle_matching.retrain_verified_catalog import teacher_keys
from vehicle_matching.train_sports_population import acceptable, financial_key, ROLES


def main():
    directory = ROOT / 'data/households/synthetic/sports-official-v1-20261028'
    cars = {car.id: car for car in read_catalog(directory / 'catalog.json')}
    records, signatures, groups, counts = {}, set(), {}, Counter()
    for role in ROLES:
        for line in (directory / f'{role}_profiles.jsonl').read_text(encoding='utf-8').splitlines():
            record = json.loads(line)
            profile = Profile(**record['profile'])
            signature = json.dumps(asdict(profile), sort_keys=True)
            assert signature not in signatures
            signatures.add(signature)
            key = financial_key(profile)
            assert groups.setdefault(key, role) == role
            assert record['id'] not in records
            records[record['id']] = (profile, role)
    with (directory / 'sports_cases.csv').open(encoding='utf-8-sig', newline='') as stream:
        for row in csv.DictReader(stream):
            profile, role = records.pop(int(row['profile_id']))
            assert role == row['split']
            higher, lower = cars[row['higher_id']], cars[row['lower_id']]
            assert {higher.id, lower.id} == {row['anchor_id'], row['comparison_id']}
            costs = [acceptable(profile, car, Assumptions()) for car in (higher, lower)]
            assert all(cost is not None for cost in costs)
            keys = teacher_keys(profile, [higher, lower], costs)
            assert keys[0] < keys[1]
            counts[row['anchor_brand'] + '|' + row['anchor_model']] += 1
    assert not records and len(counts) == 11 and set(counts.values()) == {10000}
    report = {'cases_reread': sum(counts.values()), 'counts': dict(counts),
              'duplicate_inputs': 0, 'new_financial_group_split_leakage': 0,
              'ineligible_pairs': 0, 'incorrect_teacher_order': 0}
    (directory / 'saved_data_audit.json').write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps(report, ensure_ascii=False))


if __name__ == '__main__':
    main()
