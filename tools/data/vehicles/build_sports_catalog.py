"""Build the reviewed sports supplement; never invent missing specifications."""
import csv
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
DIRECTORY = ROOT / 'data/vehicles/sports-catalog-20261028'


def build_catalog():
    reviewed = json.loads((DIRECTORY / 'reviewed.json').read_text(encoding='utf-8'))
    sources = {p.stem: json.loads(p.read_text(encoding='utf-8')) for p in (DIRECTORY / 'sources').glob('*.json')}
    records, evidence = [], []
    for values in reviewed['configurations']:
        row = dict(zip(reviewed['columns'], values, strict=True))
        price_source, spec_source = (sources[row[name]] for name in ('price_source', 'spec_source'))
        if any(source['status'] != 'EXTRACTED' for source in (price_source, spec_source)):
            raise ValueError(f"Unverified source: {row['model']}")
        identity = [row[key] for key in ('brand', 'model', 'trim')]
        identifier = 'SPORT-' + hashlib.sha256(json.dumps(identity, ensure_ascii=False).encode()).hexdigest()[:16]
        source_urls = list(dict.fromkeys([price_source['url'], spec_source['url']]))
        records.append({
            'id': identifier, 'brand': row['brand'], 'model': row['model'], 'trim': row['trim'],
            'year': '2026' if row['brand'] == '마세라티' else '',
            'price': row['price'], 'fuel': row['fuel'], 'efficiency': row['efficiency'],
            'source_url': price_source['url'], 'checked_on': reviewed['checked_on'],
            'quality': 'official-price-body-reviewed-specs-partial' if row['length_mm'] is None or row['seats'] is None else 'official-price-spec-reviewed',
            'length_mm': row['length_mm'], 'seats': row['seats'], 'seat_options': [],
            'space_source_url': spec_source['url'] if row['length_mm'] else None,
            'seats_source_url': ('https://www.maserati.com/kr/ko/models/grancabrio' if row['brand'] == '마세라티' else spec_source['url']) if row['seats'] else None,
            'seats_status': 'official-source-verified' if row['seats'] else 'unknown',
            'body_type': row['body_type'], 'body_source_urls': source_urls,
            'default_configuration': row['trim'], 'source_note': '공식 국내 가격 스냅샷. 선택품목·등록비·할인 제외. 미확인 전장·정원은 추정하지 않음.',
        })
        evidence.append({**row, 'id': identifier, 'source_urls': source_urls,
            'missing_fields': [name for name in ('length_mm', 'seats', 'efficiency') if row[name] is None],
            'source_hashes': {name: sources[name].get('sha256') or hashlib.sha256(sources[name]['text'].encode()).hexdigest() for name in (row['price_source'], row['spec_source'])}})
    assert len({r['id'] for r in records}) == len(records)
    (DIRECTORY / 'catalog.json').write_text(json.dumps(records, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    (DIRECTORY / 'field-evidence.json').write_text(json.dumps(evidence, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    with (DIRECTORY / 'catalog.csv').open('w', encoding='utf-8-sig', newline='') as stream:
        columns = ['brand', 'model', 'trim', 'body_type', 'price', 'fuel', 'length_mm', 'seats', 'efficiency', 'quality', 'source_url']
        writer = csv.DictWriter(stream, fieldnames=columns, extrasaction='ignore'); writer.writeheader(); writer.writerows(records)
    registry_path = ROOT / 'data/vehicles/body-type-registry-v1.json'
    registry = json.loads(registry_path.read_text(encoding='utf-8'))
    existing = {(r['brand'], r['model']): r for r in registry['models']}
    for row in records:
        key = (row['brand'], row['model'])
        if key in existing:
            if existing[key]['body_type'] != row['body_type']:
                raise ValueError(f'Body classification conflict: {key}')
            continue
        entry = {key: row[key] for key in ('brand', 'model', 'body_type')}
        entry.update(source_urls=row['body_source_urls'], classification_basis='국내 공식 가격표의 쿠페·그란쿠페·컨버터블·로드스터 분류 및 모델 카탈로그 대조', note='2026-10-28 스포츠 차체 추가. 모델명 유사도 추정이나 SUV 기본값 없음.')
        registry['models'].append(entry); existing[key] = entry
    registry_path.write_text(json.dumps(registry, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'configurations': len(records), 'families': len({(r['brand'], r['model']) for r in records}), 'missing_seats': sum(r['seats'] is None for r in records), 'missing_length': sum(r['length_mm'] is None for r in records)}, ensure_ascii=False))


if __name__ == '__main__':
    build_catalog()
