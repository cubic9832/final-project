"""Build display-only sales evidence without promoting research cars to finance eligibility."""
import csv
import hashlib
import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
OUTPUT = ROOT / 'data/vehicles/sales-verification-20261028'
CATALOG = ROOT / 'ml/outputs/models/preference-cohorts/20261028-v6-web-recheck/catalog.json'
REVIEW = ROOT / 'data/vehicles/luxury-sports-review-20261028/reviewed.json'
PORSCHE = 'https://www.porsche.com/korea/ko/models/911/configure/'


def observation(value, status, basis, *urls):
    return {'value': value, 'status': status, 'basis': basis, 'sources': list(dict.fromkeys(urls))}


def build_record(car, review):
    identity = {key: car.get(key) for key in ('id', 'brand', 'model', 'trim', 'year')}
    unknown_year = observation(None, 'unverified', '국내 판매 연식 미확인. 합성 데이터의 기준 연도를 실제 연식으로 사용하지 않습니다.')
    unknown_seats = observation(None, 'unverified', '국내 등록 정원과 좌석 옵션 구성 미확인. 학습용 추정 정원과 구분합니다.')
    record = {'identity': identity, 'checked_on': '2026-10-28',
        'financial_assessment': 'not-assessed',
        'order': observation(None, 'unverified', '현재 신규 주문 접수·국내 배정 물량·재고·인도 일정 미확인.'),
        'year': unknown_year, 'seats': unknown_seats}
    if car['brand'] == 'Porsche':
        row = next(row for row in review['porsche']['configurations'] if row[1] == car['trim'])
        record.update(
            designation=observation(car['trim'], 'official-reference', '국내 공식 구성기의 사양명.', PORSCHE),
            domestic=observation('국내 공식 라인업 · 2026-10-28 등재 확인', 'official-reference', '국내 라인업 등재 확인일이며 최초 출시일이 아닙니다. 개별 차량 주문·재고를 의미하지 않습니다.', PORSCHE),
            year=observation(row[3], 'official-reference', '구성기에 표시된 연식. Spirit 70의 기술 제원 각주는 2025 MY로 별도 표기되어 있습니다.' if row[1] == 'Spirit 70' else '국내 구성기 표시 연식.', PORSCHE),
            price=observation(row[4], 'official-reference', review['porsche']['price_basis'], PORSCHE))
        record['seats']['sources'] = [PORSCHE]
        record['seats']['basis'] += ' 모델군의 2+2 소개를 모든 트림의 기본 정원으로 적용하지 않습니다.'
        return record
    section = 'ferrari' if car['brand'] == 'Ferrari' else 'lamborghini'
    candidate = next(row for row in review[section]['candidates'] if row['model'] == car['model'])
    model = car['model']
    ferrari_slugs = {'12Cilindri': '12-cilindri', '12Cilindri Spider': '12-cilindri-spider',
        '296 GTB': '296-gtb', '296 GTS': '296-gts', 'Roma Spider': 'roma-spider',
        'Amalfi': 'amalfi', 'Amalfi Spider': 'amalfi-spider'}
    model_source = ('https://www.ferrarisouthbay.com/new-vehicles/' + ferrari_slugs[model]
                    if section == 'ferrari' else candidate['spec_source'])
    record['designation'] = observation(model, 'official-model', '공식 모델명 확인. 별도 국내 판매 트림·옵션 구성은 미확인.', model_source)
    domestic = {
        'Amalfi': ('2025-10-23 국내 출시', '2025-10-23 국내 출시 보도.', 'https://zdnet.co.kr/view/?no=20251023162226'),
        'Amalfi Spider': ('2026-06 국내 첫 공개', '카사 페라리 국내 첫 공개 행사. 현재 주문·재고와 구분합니다.', 'https://biz.heraldcorp.com/article/10777821'),
        '12Cilindri': ('2024-05-30 국내 공개', '국내 공개 행사일. 당시 국내 가격·인도 시점은 미정이었으며 이후 가격 목록과 구분합니다.', 'https://autodiary.kr/2024/05/4241422/'),
        '296 GTB': ('2022-01-20 국내 출시', '2022-01-20 국내 출시. 현재 주문 상태와는 구분합니다.', 'https://zdnet.co.kr/view/?no=20220120114253'),
        '296 GTS': ('2022-08-05 국내 출시', '2022-08-05 국내 출시. 현재 주문 상태와는 구분합니다.', 'https://m.etnews.com/20220805000078'),
        'Roma Spider': ('2023-06-01 국내 출시', '2023-06-01 국내 출시 행사. 현재 주문 상태와는 구분합니다.', 'https://www.newspim.com/news/view/20230601000928'),
        'Temerario': ('2025-03 국내 공개 · 2026-05 국내 인도 개시', '제조사 한국 프리미어 보도자료 배포 2025-03-07. 2026-05-26 국내 고객 인도 개시 보도.', 'https://v.daum.net/v/20260526170611256'),
        'Revuelto': ('2023-06-23 국내 출시', '2023-06-23 국내 도입 보도. 현재 주문·재고와는 구분합니다.', 'https://www.koreajoongangdaily.com/business/lamborghini-introduces-its-first-plugin-hybrid-electric-vehicle-in-korea/10283832'),
    }
    if model in domestic:
        value, basis, source = domestic[model]
        record['domestic'] = observation(value, 'reported-history', basis, source)
    else:
        record['domestic'] = observation('2026년 국내 신차 목록 등재 · 정식 출시일 미공표', 'secondary-reference', '다나와 국내 모델 목록의 2026년~현재 표기와 카눈 판매중인 모델 목록 등재 확인. 판매 개시·인증 완료 날짜는 별도로 확인되지 않았습니다.', 'https://auto.danawa.com/auto/?Model=4644&Work=model', 'https://www.carnoon.co.kr/newcar/search/?brand=262')
    price = candidate.get('reported_price')
    record['price'] = observation(price, 'secondary-reference' if price else 'unverified',
        '기존 2차 사이트 참고 가격. 동일 연식·세금·옵션 조건의 독립 3출처 합의와 현재 공식 가격은 미확인.' if price else '국내 공식 가격과 동일 조건의 독립 3출처 가격 근거를 확인하지 못했습니다.',
        *([candidate['price_source']] if candidate.get('price_source') else []))
    if model == 'Amalfi':
        record['price'] = observation(385000000, 'reported-launch-price', '2025-10-23 국내 출시 당시 보도 가격. 현재 공식 견적과 세금·옵션 조건은 미확인.', domestic[model][2])
    conflicts = {
        '296 GTB': '기존 참고가 376,000,000원과 카눈 398,000,000~415,000,000원이 다릅니다. 연식·옵션 조건 미확인으로 가격 확정 보류.',
        '296 GTS': '기존 참고가 460,000,000원과 카눈 461,000,000원이 있습니다. 근사해도 동일 조건의 독립 3출처 검증이 아니므로 확정 보류.',
        'Roma Spider': '기존 참고가 340,000,000원의 로마 쿠페·스파이더 구분과 현재 연식 조건이 불명확하여 채택 보류.',
        'Temerario': '기존 목록가 473,000,000원과 출시 보도 440,000,000원이 다릅니다. 같은 연식·세금·옵션 조건 미확인.',
        'Revuelto': '기존 목록가 784,000,000원과 다른 보도 795,000,000원이 다릅니다. 연식·세금 조건 미확인.',
    }
    # Retain a scoped published reference instead of blanking the price when
    # another year/site differs. None of these single-site prices claims the
    # independent three-source consensus required for verified promotion.
    prices = {
        '296 GTB': (398000000, 'secondary-reference', '카눈 국내 296 GTB 목록의 시작가 398,000,000원. 범위 상단 415,000,000원과 과거 참고가 376,000,000원은 연식·옵션 조건이 달라 병기합니다.', 'https://www.carnoon.co.kr/newcar/search/?brand=262'),
        '296 GTS': (461000000, 'secondary-reference', '카눈 국내 296 GTS 목록가 461,000,000원. 기존 참고가 460,000,000원과 차이가 있으며 현재 공식 견적은 아닙니다.', 'https://www.carnoon.co.kr/newcar/search/?brand=262'),
        'Roma Spider': (375000000, 'secondary-reference', '카눈의 2024년형 Roma Spider V8 가격 375,000,000원 채택. 겟차의 같은 모델명 340,000,000원은 대체 관측값으로 보존합니다.', 'https://www.carnoon.co.kr/newcar/vehicle/11730'),
        'Temerario': (473000000, 'secondary-reference', '겟차 2026년형 목록가 473,000,000원. 과거 출시 보도 가격 440,000,000원과 구분합니다.', 'https://web.getcha.kr/discount-price/4'),
        'Revuelto': (784000000, 'secondary-reference', '겟차 2024년형 V12(2025.03) 목록가 784,000,000원. 다른 시점의 795,000,000원 보도와 연식·세금 조건이 다를 수 있습니다.', 'https://web.getcha.kr/discount-price/4'),
        '12Cilindri Spider': (700000000, 'secondary-reference', '카눈 판매중인 12Cilindri Spider 목록가 700,000,000원. KB차차차 매거진의 과거 630,000,000원대 보도와 구분합니다. 제조사 공식 확정가 또는 독립 3출처 합의로 승격하지 않습니다.', 'https://www.carnoon.co.kr/newcar/search/?brand=262'),
        'Amalfi Spider': (round(385000000 * 272000 / 242000 / 1000000) * 1000000, 'estimated-price', '국내 아말피 쿠페 출시가 385,000,000원에 Motor1 보도 이탈리아 스파이더/쿠페 가격비 272,000/242,000을 적용하고 백만 원 단위 반올림. 국내 예상가 433,000,000원이며 공식 판매 가격이 아닙니다.', 'https://it.motor1.com/reviews/803509/ferrari-amalfi-spider-2026-prova/'),
    }
    if model in prices:
        value, status, basis, source = prices[model]
        record['price'] = observation(value, status, basis, source)
        if model in conflicts:
            record['price']['alternative_note'] = conflicts[model]
    if model == 'Amalfi Spider':
        record['price']['sources'].append(domestic['Amalfi'][2])
        record['price']['calculation'] = {'base_price_won': 385000000, 'spider_eur': 272000, 'coupe_eur': 242000, 'rounding_won': 1000000}
    if model in ('Temerario', 'Revuelto', 'Roma Spider'):
        year = {'Temerario': '2026', 'Revuelto': '2024', 'Roma Spider': '2024'}[model]
        record['year'] = observation(year, 'secondary-reference', '채택한 가격 자료의 연식. 현재 주문 차량의 연식 또는 최초 출시 연도를 의미하지 않습니다.', record['price']['sources'][0])
    if model in ('12Cilindri', '12Cilindri Spider', '296 GTB', '296 GTS'):
        record['seats'] = observation(2, 'official-reference', '해외 공식 딜러의 모델 좌석 구성. 국내 개별 차량 등록 사양과 구분합니다.', model_source)
    elif model in ('Amalfi', 'Amalfi Spider', 'Roma Spider'):
        record['seats'] = observation('2+ 구조 · 국내 등록 정원 미확인', 'official-layout',
            '공식 설명은 앞좌석과 소형 뒷좌석의 2+ 구조입니다. 학습용 추정 2명을 공식 정원으로 해석하지 않습니다.',
            'https://www.ferraribeverlyhills.com/articles/introducing-the-amalfi-spider' if model == 'Amalfi Spider' else model_source)
    return record


def main():
    catalog = json.loads(CATALOG.read_text(encoding='utf-8'))
    review = json.loads(REVIEW.read_text(encoding='utf-8'))
    research = [car for car in catalog if car['provenance']['kind'] != 'existing-snapshot']
    records = [build_record(car, review) for car in research]
    data = {'checked_on': '2026-10-28', 'revision': '20261028-prices-v2', 'scope': 'display-only-sales-verification', 'vehicles': records}
    OUTPUT.mkdir(parents=True, exist_ok=True)
    def save(name, value):
        (OUTPUT / name).write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    save('vehicles.json', data)
    (ROOT / 'front/src/features/vehicle/newVehicleSales.json').write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    fields = ('designation', 'domestic', 'price', 'year', 'seats', 'order')
    with (OUTPUT / 'vehicles.csv').open('w', encoding='utf-8-sig', newline='') as stream:
        names = list(records[0]['identity']) + [key + suffix for key in fields for suffix in ('', '_status', '_basis', '_sources')]
        writer = csv.DictWriter(stream, fieldnames=names)
        writer.writeheader()
        for record in records:
            row = dict(record['identity'])
            for key in fields:
                item = record[key]
                row.update({key: item['value'], key + '_status': item['status'], key + '_basis': item['basis'], key + '_sources': ' | '.join(item['sources'])})
            writer.writerow(row)
    save('audit.json', {'catalog_configurations': len(catalog), 'research_configurations_reviewed': len(records),
        'placeholder_trims': sum(car['trim'] == 'research-candidate' for car in catalog),
        'price_status_counts': dict(Counter(row['price']['status'] for row in records)),
        'missing_prices': sum(row['price']['value'] is None for row in records),
        'missing_domestic_information': sum(not row['domestic']['value'] for row in records),
        'current_orders_confirmed': 0,
        'financial_eligibility_promoted': 0,
        'source_hashes': {str(path.relative_to(ROOT)): hashlib.sha256(path.read_bytes()).hexdigest() for path in (CATALOG, REVIEW)},
        'registry_sha256': hashlib.sha256((OUTPUT / 'vehicles.json').read_bytes()).hexdigest()})
    print('Reviewed sales evidence:', len(records))


if __name__ == '__main__':
    main()
