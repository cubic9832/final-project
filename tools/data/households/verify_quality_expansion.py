"""Validate exact 100k addition, provenance, class coverage and preserved source."""
import csv
import hashlib
import json
from collections import Counter

from tools.data.households.expand_quality_training import SOURCE, OUTPUT, FLOORS
from tools.data.households.verify_vehicle_coverage import signature


def verify():
    report=json.loads((OUTPUT/'generation_report.json').read_text(encoding='utf-8'))
    assert hashlib.sha256((SOURCE/'combined_training.csv').read_bytes()).hexdigest()==report['source_sha256']
    ids=set()
    signatures=set()
    counts={split:Counter() for split in FLOORS}
    with (SOURCE/'combined_training.csv').open(encoding='utf-8-sig',newline='') as old, \
         (OUTPUT/'combined_training.csv').open(encoding='utf-8-sig',newline='') as new:
        original,current=csv.DictReader(old),csv.DictReader(new)
        preserved=0
        for row in original:
            result=next(current)
            assert row==result, 'Unexpected baseline change; review change log'
            ids.add(row['프로필_식별자']); signatures.add(signature(row))
            counts[row['데이터_구분']][row['선택차량_라벨코드']]+=1
            preserved+=1
        added=list(current)
    with (OUTPUT/'additional_100000.csv').open(encoding='utf-8-sig',newline='') as source:
        assert list(csv.DictReader(source))==added
    with (OUTPUT/'additional_provenance.csv').open(encoding='utf-8-sig',newline='') as source:
        provenance=list(csv.DictReader(source))
    assert len(added)==len(provenance)==100000
    modes=Counter()
    for row,origin in zip(added,provenance):
        assert row['프로필_식별자']==origin['프로필_식별자']
        assert row['데이터_구분']==origin['데이터_구분']
        assert row['프로필_식별자'] not in ids
        ids.add(row['프로필_식별자'])
        key=signature(row)
        assert key not in signatures, 'Additional profile is duplicated'
        signatures.add(key)
        assert int(row['월소득보정액_원'])==0
        # Every column whose name expresses a numeric unit remains integer-valued.
        for name,value in row.items():
            if name.endswith(('_원','_km','_명','_퍼센트','_개월')) or name in ('가성비중요도_1부터5',):
                assert value.lstrip('-').isdigit(), (name,value)
        modes[origin['생성유형']]+=1
        counts[row['데이터_구분']][row['선택차량_라벨코드']]+=1
    labels=set().union(*(set(c) for c in counts.values()))
    assert all(counts[s][label]>=FLOORS[s] for s in counts for label in labels)
    result={'total_rows':preserved+len(added),'preserved_rows':preserved,'new_unique_input_rows':len(added),
            'source_unchanged':True,'original_evaluation_unchanged':True,'numeric_integer_checks':True,
            'label_count':len(labels),'minimum_rows_per_label':{s:min(counts[s].values()) for s in counts},
            'modes':modes,'splits':{s:sum(c.values()) for s,c in counts.items()}}
    (OUTPUT/'expansion_validation.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(result,ensure_ascii=True,indent=2))


if __name__=='__main__': verify()
