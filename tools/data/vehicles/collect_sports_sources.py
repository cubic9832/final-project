"""Fetch public Korean-market sports-car evidence without changing catalog data."""
import concurrent.futures
import hashlib
import io
import json
import urllib.request
from pathlib import Path

from bs4 import BeautifulSoup
from pypdf import PdfReader

ROOT = Path(__file__).resolve().parents[3]
OUTPUT = ROOT / 'data/vehicles/sports-catalog-20261028'
SOURCES = {
    'bmw-price': 'https://www.bmw.co.kr/content/dam/bmw/marketKR/bmw_co_kr/Pricelist/pricelist_oct2026.pdf.asset.1792129034710.pdf',
    'bmw-lineup': 'https://www.bmw.co.kr/ko/all-models.html',
    'mini-price': 'https://minikr.co.kr/2023/pdf-cta/images/MINI-COOPER-CONVERTIBLE-Price-Option-List.pdf',
    'mini-spec': 'https://minikr.co.kr/2023/pdf-cta/images/MINI-COOPER-CONVERTIBLE-Specification.pdf',
    'mini-lineup': 'https://www.mini.co.kr/ko_KR/home/Product-Information-KR.html',
    'toyota-gr86': 'https://www.toyota.co.kr/models/gr86/',
    'toyota-spec': 'https://www.toyota.co.kr/download/model/GR86_spec.pdf',
    'maserati-home': 'https://www.maserati.com/kr/ko?redirect=1',
    'maserati-dealer': 'https://www.maserati.com/kr/ko/dealers/stellaautomobiles',
    'maserati-granturismo': 'https://www.maserati.com/kr/ko/models/granturismo',
    'maserati-grancabrio': 'https://www.maserati.com/kr/ko/models/grancabrio',
    'maserati-mcpura': 'https://www.maserati.com/kr/ko/models/mcpura',
    'maserati-gt2': 'https://www.maserati.com/kr/ko/models/gt2-stradale',
    'lotus-emira': 'https://www.lotuscars.com/ko-KR/emira',
    'lotus-price': 'https://www.lotuscars.co.kr/NEWS/?bmode=view&idx=144342095',
    'porsche-lineup': 'https://www.porsche.com/korea/ko/models/911/',
    'porsche-new-stock': 'https://finder.porsche.com/kr/ko-KR/s/carrera',
    'benz-price': 'https://www.mercedes-benz.co.kr/passengercars/models/price-list.html',
    'benz-cle': 'https://www.mercedes-benz.co.kr/passengercars/models/coupe/cle/overview.html',
    'bentley-gt': 'https://bentleyseoul.com/model/continental-gt/',
    'rolls-spectre': 'https://www.rolls-roycemotorcars.com/ko_KR/showroom/spectre.html',
    'hyundai-lineup': 'https://www.hyundai.com/kr/ko/e/api/product/car/catalog-price',
    'kia-lineup': 'https://www.kia.com/kr/vehicles/sedan',
    'genesis-lineup': 'https://www.genesis.com/kr/ko/models.html',
}


def fetch(item):
    name, url = item
    path = OUTPUT / 'sources' / f'{name}.json'
    if path.exists():
        return json.loads(path.read_text(encoding='utf-8'))
    row = {'id': name, 'url': url, 'checked_on': '2026-10-28'}
    try:
        request = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(request, timeout=15) as response:
            data = response.read()
            row['final_url'] = response.geturl()
        (OUTPUT / 'sources' / f'{name}.raw').write_bytes(data)
        row.update(sha256=hashlib.sha256(data).hexdigest(), bytes=len(data))
        if data.startswith(b'%PDF'):
            row['pages'] = [{'page': i + 1, 'text': p.extract_text() or ''}
                            for i, p in enumerate(PdfReader(io.BytesIO(data)).pages)]
            row['text'] = '\n'.join(p['text'] for p in row['pages'])
        else:
            soup = BeautifulSoup(data, 'html.parser')
            row['tables'] = [[[c.get_text(' ', strip=True) for c in r.find_all(['td', 'th'])]
                              for r in t.find_all('tr')] for t in soup.find_all('table')]
            for tag in soup(['script', 'style', 'nav', 'footer', 'header']):
                tag.decompose()
            row['text'] = soup.get_text('\n', strip=True)
        row['status'] = 'EXTRACTED'
    except Exception as error:
        row.update(status='UNAVAILABLE', error=str(error))
    path.write_text(json.dumps(row, ensure_ascii=False, indent=2), encoding='utf-8')
    return row


def main():
    (OUTPUT / 'sources').mkdir(parents=True, exist_ok=True)
    with concurrent.futures.ThreadPoolExecutor(max_workers=6) as pool:
        rows = list(pool.map(fetch, SOURCES.items()))
    summary = [{k: v for k, v in r.items() if k not in ('pages', 'text', 'tables')} for r in rows]
    (OUTPUT / 'retrieval.json').write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps(summary, ensure_ascii=False), flush=True)


if __name__ == '__main__':
    main()
