"""Collect public domestic new-car documents; never infer trim/efficiency joins."""

import argparse
import hashlib
import io
import json
import re
import time
import urllib.parse
import urllib.request
from pathlib import Path

from bs4 import BeautifulSoup
from pypdf import PdfReader

ROOT = (Path(__file__).resolve().parents[3] / 'data/vehicles')
CHECKED_ON = '2026-10-14'


def read_source(name):
    return (ROOT / 'sources' / f'{name}.html').read_text(encoding='utf-8')


def fetch(url, data=None):
    time.sleep(0.15)
    request = urllib.request.Request(
        url, data=data, headers={'User-Agent': 'VehicleResearch/1.0',
                                'Accept': '*/*'})
    with urllib.request.urlopen(request, timeout=35) as response:
        return response.read(), response.geturl()


def record(brand, model, model_url, documents):
    return {'brand': brand, 'model': model, 'modelUrl': model_url,
            'checkedOn': CHECKED_ON, 'condition': 'NEW',
            'documents': documents, 'status': 'pending',
            'normalizedSpecifications': [],
            'notes': '공식 목록에 노출된 모델. 계약 가능 여부와 모든 사양 조합은 별도 검증.'}


def discover_models():
    models = []
    for car in json.loads(read_source('hyundai-catalog-data'))['data']:
        name = car['carName'].strip()
        if car['carTypeCode'] in ['T', 'B', 'L'] or any(
                word in name for word in ['포터', 'ST1', '킨더']):
            continue
        documents = [{'kind': kind, 'url': urllib.parse.urljoin(
            'https://www.hyundai.com', car[key])}
            for kind, key in [('price', 'pTableFilePath'), ('catalog', 'catalogFilePath')]
            if car.get(key)]
        models.append(record('현대', name,
            'https://www.hyundai.com/kr/ko/e/vehicles/' + car['carEngName'], documents))

    # Discover actual model cards rather than assuming a historical model list.
    kia_seen = set()
    for source in ['kia', 'kia-rv', 'kia-ev', 'kia-pbv']:
        soup = BeautifulSoup(read_source(source), 'html.parser')
        for anchor in soup.find_all('a', href=True):
            path = anchor['href']
            label = anchor.get_text(' ', strip=True)
            if not path.startswith('/kr/vehicles/') or not label.endswith('자세히 보기'):
                continue
            slug = path.split('/')[-1]
            if slug in kia_seen or any(word in slug for word in
                    ['bongo', 'tasman', 'cargo', 'openbed', 'prime', 'wav']):
                continue
            kia_seen.add(slug)
            models.append(record('기아', label.removesuffix('자세히 보기').strip(),
                'https://www.kia.com' + path, []))

    genesis = {}
    soup = BeautifulSoup(read_source('genesis-catalog'), 'html.parser')
    for anchor in soup.select('a[data-download-info]'):
        info = json.loads(anchor['data-download-info'])
        if info['fileType'] not in ['BROCHURE', 'CATALOG']:
            continue
        name = info['cateName']
        key = re.search(r"viewPdf\('([^']+)'", anchor.get('href', ''))
        if not key:
            continue
        genesis.setdefault(name, []).append({
            'kind': 'price' if info['fileType'] == 'BROCHURE' else 'catalog',
            'url': 'https://www.genesis.com/wsvc/kr/api/v2/download-center/pdfview',
            'postFileKey': key.group(1), 'filename': info['realFileNm']})
    for name, docs in genesis.items():
        unique = {doc['filename']: doc for doc in docs}
        models.append(record('제네시스', name,
            'https://www.genesis.com/kr/ko/support/download-center/genesis-models.html',
            list(unique.values())))

    kgm_data = json.loads(read_source('kgm-models'))['body']['typeList']
    kgm_menu = json.loads(read_source('kgm-download'))['body']['menuList']
    price = next(menu for menu in kgm_menu if menu['menuNm'] == '종합가격표')
    price_url = price['modelList'][0]['periodList'][0]['fileList'][0]['fileUrl']
    for category in kgm_data:
        if category['typeNm'] != 'SUV':
            continue
        for car in category['modelList']:
            item = record('KG모빌리티', car['modelNm'],
                'https://www.kg-mobility.com/pr/model/show-room/' + car['dispCatNo'],
                [{'kind': 'shared-price', 'url': price_url}])
            item['advertisedStartingPriceWon'] = int(car['price'].replace(',', ''))
            item['startingPriceBasis'] = '공식 모델 목록 표시값; 트림 가격과 구분'
            models.append(item)

    soup = BeautifulSoup(read_source('renault-catalog'), 'html.parser')
    renault_seen = set()
    for button in soup.select('[onclick]'):
        match = re.search(r"viewPdf\('[^']*', 'price', '([^']+)'", button['onclick'])
        if not match or match.group(1) == 'RKM':
            continue
        original = match.group(1)
        slug = {'Grand Koleos': 'koleos', 'XM3': 'xm3'}.get(original, original.lower())
        if slug in renault_seen:
            continue
        renault_seen.add(slug)
        name = {'koleos': '그랑 콜레오스', 'xm3': '아르카나', 'filante': '필랑트'}.get(slug, original)
        models.append(record('르노코리아', name,
            'https://www.renault.co.kr/ko/model/' + ('arkana' if slug == 'xm3' else slug) + '_overview.jsp',
            [{'kind': 'price', 'url': f'https://www.renault.co.kr/upload/asset/price/price_{slug}_202610.pdf'},
             {'kind': 'catalog', 'url': f'https://www.renault.co.kr/upload/asset/ebrochure/eBrochure_{slug}_202610.pdf'}]))

    for name, slug in [('트레일블레이저', 'suvs/trailblazer'),
                       ('트랙스 크로스오버', 'cuvs/trax-crossover')]:
        models.append(record('쉐보레', name, 'https://www.chevrolet.co.kr/' + slug,
            [{'kind': 'price-page', 'url': 'https://www.chevrolet.co.kr/finance/type-price'}]))
    return models


def collect_documents(models, limit=None):
    output = ROOT / 'extracted'
    output.mkdir(exist_ok=True)
    downloaded = {}
    selected = models if limit is None else models[:limit]
    for index, model in enumerate(selected, 1):
        if model['brand'] == '기아' and not model['documents']:
            try:
                html, _ = fetch(model['modelUrl'] + '/features')
                soup = BeautifulSoup(html, 'html.parser')
                urls = set(re.findall(r'[^\s"\'<>]+\.pdf', str(soup)))
                model['documents'] = [{'kind': 'price' if 'price' in url else 'catalog',
                    'url': urllib.parse.urljoin('https://www.kia.com', url)}
                    for url in sorted(urls) if '/ko/' in url and any(
                        word in url for word in ['/price/', '/catalog/'])]
            except Exception as error:
                model['discoveryError'] = str(error)
        for document in model['documents']:
            if document.get('status') == 'extracted' and (ROOT / document['extractedPath']).is_file():
                continue
            cache_key = document['url'] + document.get('postFileKey', '')
            if cache_key in downloaded:
                document.update(downloaded[cache_key])
                continue
            try:
                body = urllib.parse.urlencode({'file_key': document['postFileKey']}).encode() if document.get('postFileKey') else None
                content, final_url = fetch(document['url'], body)
                name = hashlib.sha256(cache_key.encode()).hexdigest()[:16]
                if content.startswith(b'%PDF'):
                    reader = PdfReader(io.BytesIO(content))
                    pages = [{'page': i + 1, 'text': page.extract_text() or ''}
                             for i, page in enumerate(reader.pages)]
                    result = {'sourceUrl': document['url'], 'pages': pages,
                              'verification': 'raw-extraction-not-normalized'}
                elif document['kind'] in ['price-page', 'model-page']:
                    soup = BeautifulSoup(content, 'html.parser')
                    result = {'sourceUrl': document['url'], 'text': soup.get_text(' ', strip=True),
                              'tables': [[[cell.get_text(' ', strip=True) for cell in row.find_all(['td', 'th'])]
                                          for row in table.find_all('tr')] for table in soup.find_all('table')],
                              'verification': 'raw-extraction-not-normalized'}
                else:
                    raise ValueError('Expected PDF, received another response')
                path = output / f'{name}.json'
                path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')
                info = {'status': 'extracted', 'extractedPath': f'extracted/{name}.json',
                        'sha256': hashlib.sha256(content).hexdigest(), 'finalUrl': final_url}
            except Exception as error:
                info = {'status': 'failed', 'error': str(error)}
            document.update(info)
            downloaded[cache_key] = info
        successes = sum(doc.get('status') == 'extracted' for doc in model['documents'])
        model['status'] = 'sources-extracted' if successes == len(model['documents']) and successes else 'incomplete'
        print(json.dumps({'index': index, 'brand': model['brand'], 'model': model['model'],
                          'documents': len(model['documents']), 'successes': successes}, ensure_ascii=True), flush=True)
        save_manifest(models)


def save_manifest(models):
    result = {'checkedOn': CHECKED_ON, 'scope': '국내 6개 브랜드 승용 신차; 파워트레인·특별 모델 표기는 별도 항목',
              'excluded': ['중고차', '상용 트럭', '버스', '택시 전용', '어린이 통학 전용'],
              'completeness': '공식 목록 기반. 자료 추출과 트림별 정규화·검증 완료 여부는 별개.',
              'models': models}
    (ROOT / 'official-model-manifest.json').write_text(
        json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--limit', type=int)
    parser.add_argument('--resume', action='store_true')
    args = parser.parse_args()
    models = json.loads((ROOT / 'official-model-manifest.json').read_text(encoding='utf-8'))['models'] if args.resume else discover_models()
    for model in models:
        model['notes'] = '공식 목록에 노출된 모델. 계약 가능 여부와 모든 사양 조합은 별도 검증.'
        if model['brand'] == '르노코리아' and model['model'] == '아르카나':
            for doc in model['documents']:
                doc['url'] = doc['url'].replace('_xm3_', '_Arkana_')
        if model['brand'] == '쉐보레':
            source = 'chevrolet-trailblazer-modal' if model['model'] == '트레일블레이저' else 'chevrolet-trax-modal'
            soup = BeautifulSoup(read_source(source), 'html.parser')
            known = {doc['url'] for doc in model['documents']}
            for anchor in soup.find_all('a', href=True):
                if '.pdf' not in anchor['href']:
                    continue
                url = urllib.parse.urljoin('https://www.chevrolet.co.kr', anchor['href'])
                if url not in known:
                    model['documents'].append({'kind': 'price' if 'pricelist' in url else 'catalog', 'url': url})
                    known.add(url)
        if not model['documents']:
            url = model['modelUrl']
            if '캐스퍼' in model['model']:
                url = 'https://casper.hyundai.com/vehicles/' + ('electric/highlight' if '일렉트릭' in model['model'] else 'highlight')
            model['documents'].append({'kind': 'model-page', 'url': url})
    save_manifest(models)
    collect_documents(models, args.limit)


if __name__ == '__main__':
    main()
