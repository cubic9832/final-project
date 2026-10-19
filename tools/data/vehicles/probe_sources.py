import json
import argparse
import re
import urllib.request
from pathlib import Path

SOURCES = {
    'hyundai': 'https://www.hyundai.com/kr/ko/e/vehicles/catalog-price-download',
    'kia': 'https://www.kia.com/kr/vehicles/sedan',
    'genesis': 'https://www.genesis.com/kr/ko/sitemap.html',
    'kgm': 'https://www.kg-mobility.com/',
    'renault': 'https://www.renault.co.kr/',
    'chevrolet': 'https://www.chevrolet.co.kr/',
    'kia-rv': 'https://www.kia.com/kr/vehicles/rv',
    'kia-ev': 'https://www.kia.com/kr/vehicles/ev',
    'kia-pbv': 'https://www.kia.com/kr/vehicles/pbv',
    'kia-catalog': 'https://www.kia.com/kr/vehicles/catalog-price',
    'genesis-catalog': 'https://www.genesis.com/kr/ko/support/download-center/genesis-models.html',
    'renault-catalog': 'https://www.renault.co.kr/ko/side/catalog_download.jsp',
    'renault-models': 'https://www.renault.co.kr/ko/model/model_list.jsp',
    'chevrolet-catalog': 'https://www.chevrolet.co.kr/e-catalog-price-list',
    'chevrolet-prices': 'https://www.chevrolet.co.kr/finance/type-price',
    'kgm-download': 'https://web.kg-mobility.com/app/display/getDownloadCenterList.do',
    'kgm-models': 'https://web.kg-mobility.com/app/display/getPlpModelList.do',
    'hyundai-catalog-data': 'https://www.hyundai.com/kr/ko/e/api/product/car/catalog-price',
    'hyundai-models-data': 'https://www.hyundai.com/kr/ko/e/api/product/car/representative-cars?searchYn=Y',
    'casper': 'https://casper.hyundai.com/vehicles/highlight',
    'casper-electric': 'https://casper.hyundai.com/vehicles/electric/highlight',
    'chevrolet-trailblazer-modal': 'https://www.chevrolet.co.kr/content/experience-fragments/chevrolet/as/kr/ko/partials/e-catalog-price-list/modal-trailblazer/master.html',
    'chevrolet-trax-modal': 'https://www.chevrolet.co.kr/content/experience-fragments/chevrolet/as/kr/ko/partials/e-catalog-price-list/modal-traxcrossover/master.html',
}

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--only', nargs='*')
    args = parser.parse_args()
    root = (Path(__file__).resolve().parents[3] / 'data/vehicles') / 'sources'
    root.mkdir(exist_ok=True)
    for brand, url in SOURCES.items():
        if args.only and brand not in args.only:
            continue
        try:
            request = urllib.request.Request(url, headers={'User-Agent': 'VehicleResearch/1.0'})
            with urllib.request.urlopen(request, timeout=25) as response:
                content = response.read().decode('utf-8', errors='replace')
            (root / f'{brand}.html').write_text(content, encoding='utf-8')
            links = sorted(set(re.findall(r'(?:href|src)=["\']([^"\']+)', content)))
            selected = [link for link in links if '.pdf' in link.lower() or (('/vehicles/' in link or '/models/' in link) and not any(term in link for term in ['represent', 'members', 'kia-connect']))]
            print(json.dumps({'brand': brand, 'size': len(content), 'links': selected}, ensure_ascii=True))
        except Exception as error:
            print(json.dumps({'brand': brand, 'error': str(error)}))

if __name__ == '__main__':
    main()
