"""Check training class coverage, independent inputs and unchanged baseline rows."""
import csv
import json
from collections import Counter

from tools.data.households.supplement_vehicle_coverage import OUTPUT, DESTINATION
from tools.data.households.extend_training_preferences import FEATURES, PREFERENCES


def signature(row):
    return tuple(row[k] for k in (*FEATURES,*PREFERENCES,'월저축액_원','비상자금_원',
                                  '구매투입가능자금_원','최소월여유자금_원','구매가격상한_원_0이면미지정'))


def verify():
    counts = {split:Counter() for split in ('학습','검증','평가')}
    originals = set()
    total = 0
    with (OUTPUT/'combined_training.csv').open(encoding='utf-8-sig',newline='') as old, \
         (DESTINATION/'combined_training.csv').open(encoding='utf-8-sig',newline='') as new:
        previous, current = csv.DictReader(old), csv.DictReader(new)
        for before in previous:
            after = next(current)
            assert before==after, 'Existing row changed'
            originals.add(signature(before))
            counts[after['데이터_구분']][after['선택차량_라벨코드']]+=1
            total+=1
        additions = list(current)
    unique = set()
    for row in additions:
        assert row['데이터_구분']=='학습'
        key = signature(row)
        assert key not in originals and key not in unique, 'Repeated input'
        unique.add(key)
        counts['학습'][row['선택차량_라벨코드']]+=1
    all_labels = set().union(*(set(values) for values in counts.values()))
    assert all(counts['학습'][label]>=100 for label in all_labels)
    result = {'rows':total+len(additions),'added_rows':len(additions),'unique_new_inputs':len(unique),
              'existing_rows_unchanged':total,'validation_and_evaluation_unchanged':True,
              'training_label_count':len(counts['학습']),'minimum_training_rows_per_label':min(counts['학습'].values()),
              'unseen_validation_labels':list(set(counts['검증'])-set(counts['학습'])),
              'unseen_evaluation_labels':list(set(counts['평가'])-set(counts['학습'])),
              'splits':{split:sum(values.values()) for split,values in counts.items()}}
    (DESTINATION/'coverage_validation.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(result,ensure_ascii=True,indent=2))


if __name__=='__main__': verify()
