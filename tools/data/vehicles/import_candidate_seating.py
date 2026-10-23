"""Import the supplied TSV seating table and preserve conflicts for review."""
import argparse
import csv
import hashlib
import io
import json
import re
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / 'ml'))

from vehicle_matching.catalog import read_catalog
from vehicle_matching.catalog_merge import expand_catalog


def parse_seating(label):
    match = re.fullmatch(r'(\d+)인승(?:\s*\(옵션:\s*([\d/]+)인승\))?', label.strip())
    if match:
        base = int(match[1])
        options = sorted({base, *(map(int, match[2].split('/')) if match[2] else [])})
    elif re.fullmatch(r'\d+인승(?:\s*/\s*\d+인승)+', label.strip()):
        base, options = None, sorted(set(map(int, re.findall(r'\d+', label))))
    else:
        raise ValueError(f'Unknown seating notation: {label}')
    if not all(1 <= value <= 15 for value in options):
        raise ValueError(f'Invalid capacity: {label}')
    return base, options


def import_table(input_path):
    raw = input_path.read_bytes()
    text = raw.decode('utf-8-sig')
    start = text.index('번호\t브랜드\t')
    rows = list(csv.DictReader(io.StringIO(text[start:]), delimiter='\t'))
    vehicles, _ = expand_catalog(read_catalog(ROOT / 'ml/experiments/candidate-v2/catalog.json'))
    by_id = {v.id: v for v in vehicles}
    supplied_ids = [row['후보 ID'] for row in rows]
    if len(supplied_ids) != len(set(supplied_ids)) or set(supplied_ids) != set(by_id):
        raise ValueError('Supplied table must cover every candidate ID exactly once')
    evidence = json.loads((ROOT / 'data/vehicles/candidate-seating-evidence.json').read_text(encoding='utf-8'))['vehicles']
    references = {(row['brand'], row['model']): row for row in evidence if row['seat_options']}
    # The ordinary Palisade shares the same published 7/9-seat configuration family.
    manifest = json.loads((ROOT / 'data/vehicles/official-model-manifest.json').read_text(encoding='utf-8'))['models']
    palisade = next(m for m in manifest if m['model'] == '팰리세이드')
    doc = next(d for d in palisade['documents'] if d['kind'] == 'price')
    extracted = json.loads((ROOT / 'data/vehicles' / doc['extractedPath']).read_text(encoding='utf-8'))
    quoted = []
    for count in (7, 9):
        for page in extracted['pages']:
            match = re.search(str(count) + r'\s*인승', page['text'])
            if match:
                quoted.append(page['text'][max(0, match.start()-25):match.end()+25])
                break
    if len(quoted) != 2:
        raise ValueError('Palisade 7/9-seat reference no longer matches')
    references[('현대', '팰리세이드')] = {'seat_options': [7, 9], 'seats': None, 'source_url': doc['url']}
    electric = next(m for m in manifest if m['model'] == '더 뉴 스타리아 Electric')
    electric_doc = next(d for d in electric['documents'] if d['kind'] == 'price')
    electric_text = json.loads((ROOT / 'data/vehicles' / electric_doc['extractedPath']).read_text(encoding='utf-8'))['pages'][0]['text']
    if not re.search(r'투어러\s*일렉트릭\s*11\s*\(11인승\)', electric_text):
        raise ValueError('Staria Electric tourer reference no longer matches')
    references[('현대', '더 뉴 스타리아 Electric')] = {'seat_options': [11], 'seats': 11, 'source_url': electric_doc['url']}
    registered = []
    for row in rows:
        vehicle = by_id[row['후보 ID']]
        if (row['브랜드'], row['모델'], row['트림'], int(row['등록 가격(원)'].replace(',', ''))) != (vehicle.brand, vehicle.model, vehicle.trim, vehicle.price):
            raise ValueError(f'Table identity mismatch: {vehicle.id}')
        base, options = parse_seating(row['승차 정원'])
        status, source_url = 'user-provided', None
        label = row['승차 정원']
        note = '사용자 제공 목록의 승차 정원. 제조사 사양 검증 완료를 뜻하지 않습니다.'
        ref = references.get((vehicle.brand, vehicle.model))
        conflict = bool(ref and not set(options).issubset(ref['seat_options']))
        if conflict:
            base, options = ref['seats'], ref['seat_options']
            model = next((m for m in manifest if (m['brand'], m['model']) == (vehicle.brand, vehicle.model)), None)
            price_doc = next((d for d in model['documents'] if d['kind'] == 'price' and d.get('extractedPath')), None) if model else None
            if price_doc:
                pages = json.loads((ROOT / 'data/vehicles' / price_doc['extractedPath']).read_text(encoding='utf-8')).get('pages', [])
                price_tokens = [f'{int(vehicle.price):,}']
                if vehicle.price % 10000 == 0:
                    price_tokens.append(f'{int(vehicle.price / 10000):,}만')
                matching = [p for p in pages if any(token in p['text'] for token in price_tokens)]
                if len(matching) == 1:
                    mentioned = {int(n) for n in re.findall(r'(?<!\d)(\d+)\s*인승', matching[0]['text'])} & set(options)
                    header = {int(n) for n in re.findall(r'(?<!\d)(\d+)\s*인승', matching[0]['text'][:160])} & set(options)
                    if len(header) == 1:
                        mentioned = header
                    if len(mentioned) == 1:
                        base = next(iter(mentioned))
                        options = [base]
            status, source_url = 'official-reference-conflict', ref['source_url']
            label = f'{base}인승' if base else ' / '.join(f'{n}인승' for n in options)
            note = f"입력 목록의 ‘{row['승차 정원']}’과 공식 정원 자료가 달라 공식 자료를 적용했습니다. 세부 좌석 사양 확인이 필요합니다."
        registered.append({'id': vehicle.id, 'brand': vehicle.brand, 'model': vehicle.model, 'trim': vehicle.trim,
                           'price': vehicle.price, 'seats': base, 'seat_options': options,
                           'provided_label': row['승차 정원'], 'label': label,
                           'status': status, 'source_url': source_url, 'note': note,
                           'input_row': int(row['번호'])})
    result = {'source_file': input_path.name, 'source_sha256': hashlib.sha256(raw).hexdigest(),
              'description': '운전자 포함 승차 정원. 사용자 입력은 보존하고 확인된 공식 자료와 충돌하면 공식 자료 우선.',
              'counts': dict(Counter(row['status'] for row in registered)), 'vehicles': registered}
    (ROOT / 'data/vehicles/candidate-seating-registry.json').write_text(json.dumps(result, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    report = ['# 차량 후보별 승차 정원 등록 결과', '', f'전체 {len(registered)}건. 사용자 제공 목록을 기준으로 등록하며 공식 자료와 충돌한 값은 별도로 표시한다.', '',
              '| 번호 | 브랜드 | 모델 | 트림 | 입력 정원 | 적용 정원 | 상태 | 후보 ID |', '|---:|---|---|---|---|---|---|---|']
    for row in registered:
        report.append('| '+' | '.join(str(row[key]) for key in ('input_row','brand','model','trim','provided_label','label','status','id'))+' |')
    (ROOT / 'ml/reports/candidate-seating-registration.md').write_text('\n'.join(report)+'\n', encoding='utf-8')
    return result['counts']


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--input', type=Path, required=True)
    print(import_table(parser.parse_args().input))
