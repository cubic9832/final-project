"""Prepare reviewed source assets and technical tables; never infer specifications."""
from concurrent.futures import ThreadPoolExecutor
import hashlib
import io
import json
from pathlib import Path
from urllib.parse import urljoin, quote
from urllib.request import Request, urlopen

from bs4 import BeautifulSoup
from PIL import Image

ROOT = Path(__file__).resolve().parents[3]
DATA = ROOT / 'data/vehicles/new-model-details-20261028'


def save(name, data):
    (DATA / name).write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def ferrari_records():
    soup = BeautifulSoup((DATA / 'sources/ferrari-dealer-lineup.html').read_text(encoding='utf-8'), 'html.parser')
    payload = json.loads(soup.find('script', id='__NEXT_DATA__').string)
    found = {}
    wanted = {'296-gtb': '296 GTB', '296-gts': '296 GTS', '12-cilindri': '12Cilindri',
              '12-cilindri-spider': '12Cilindri Spider', 'amalfi': 'Amalfi', 'amalfi-spider': 'Amalfi Spider'}

    def walk(value):
        if isinstance(value, dict):
            item = value.get('attributes', {})
            if isinstance(item, dict) and item.get('slug') in wanted:
                slug = item['slug']
                photo = item['listDisplay']['image']['data']['attributes']
                found[slug] = {'brand': 'Ferrari', 'model': wanted[slug], 'slug': 'ferrari-' + slug,
                    'source_url': 'https://www.ferrarisouthbay.com/new-vehicles/' + slug,
                    'source_kind': 'manufacturer-authorized-dealer-global-specifications',
                    'image_url': photo['url'], 'image_caption': photo['name'],
                    'technical_groups': item['technicalSpecificationGroups'],
                    'market': 'global-reference-not-Korean-homologation',
                    'note': 'Technical table only. Summary cards have conflicting acceleration/power units; do not copy summary cards.'}
            for child in value.values():
                walk(child)
        elif isinstance(value, list):
            for child in value:
                walk(child)
    walk(payload)
    records = list(found.values())
    save('ferrari-technical-tables.json', records)
    return records


def download(row):
    try:
        request = Request(quote(row['image_url'], safe=':/?=&%,-._()'), headers={'User-Agent': 'Mozilla/5.0'})
        with urlopen(request, timeout=30) as response:
            raw = response.read()
        image = Image.open(io.BytesIO(raw)); image.load()
        extension = {'PNG': 'png', 'JPEG': 'jpg', 'WEBP': 'webp', 'AVIF': 'avif'}[image.format]
        path = DATA / 'images' / f"{row['slug']}.{extension}"
        path.parent.mkdir(exist_ok=True)
        path.write_bytes(raw)
        alpha = image.convert('RGBA').getchannel('A')
        return {**row, 'file': path.relative_to(ROOT).as_posix(), 'status': 'downloaded',
                'width': image.width, 'height': image.height, 'transparent': alpha.getextrema()[0] < 255,
                'sha256': hashlib.sha256(raw).hexdigest()}
    except Exception as error:
        return {**row, 'status': 'failed', 'error': str(error)}


def main():
    rows = ferrari_records()
    bmw = json.loads((DATA / 'bmw-scene7-candidates.json').read_text(encoding='utf-8'))
    bmw_original = {r['slug']: r for r in json.loads((DATA / 'bmw-image-candidates.json').read_text(encoding='utf-8'))}
    rows += [{**bmw_original[r['slug']], **r} for r in bmw]
    for slug, brand, model in (('lamborghini-temerario', 'Lamborghini', 'Temerario'), ('lamborghini-revuelto', 'Lamborghini', 'Revuelto')):
        page = json.loads((DATA / 'sources' / f'{slug}.json').read_text(encoding='utf-8'))
        image = next(item['content'] for item in page['images'] if item.get('property') == 'og:image')
        rows.append({'slug': slug, 'brand': brand, 'model': model, 'source_url': page['url'], 'image_url': image})
    rows.append({'slug': 'toyota-gr86', 'brand': '토요타', 'model': 'GR86',
                 'source_url': 'https://www.toyota.co.kr/models/gr86/',
                 'image_url': 'https://www.toyota.co.kr/assets/img/model/gr86/models-gr86-exterior-1.webp'})
    with ThreadPoolExecutor(max_workers=8) as executor:
        results = list(executor.map(download, rows))
    save('image-downloads.json', results)
    for row in results:
        print(json.dumps({k: row.get(k) for k in ('slug', 'status', 'transparent', 'width', 'height', 'error')}), flush=True)


if __name__ == '__main__':
    main()
