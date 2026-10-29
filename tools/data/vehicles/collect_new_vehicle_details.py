"""Collect public manufacturer pages and asset candidates without changing ML snapshots."""
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
from pathlib import Path
import re
from urllib.parse import urljoin, urlsplit
from urllib.request import Request, urlopen

from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parents[3]
OUTPUT = ROOT / 'data/vehicles/new-model-details-20261028'
PAGES = {
    'bmw-lineup': 'https://www.bmw.co.kr/ko/all-models.html',
    'mini-convertible': 'https://www.mini.co.kr/ko_KR/home/range/mini-convertible.html',
    'toyota-gr86': 'https://www.toyota.co.kr/models/gr86/',
    'maserati-granturismo': 'https://www.maserati.com/kr/ko/models/granturismo',
    'maserati-grancabrio': 'https://www.maserati.com/kr/ko/models/grancabrio',
    'porsche-911': 'https://models.porsche.com/ko-KR/model-start/911',
    'ferrari-lineup': 'https://www.ferrari.com/en-EN/auto/car-range',
    'lamborghini-temerario': 'https://www.lamborghini.com/en-en/models/temerario',
    'lamborghini-revuelto': 'https://www.lamborghini.com/en-en/models/revuelto',
}


def collect(item):
    slug, url = item
    directory = OUTPUT / 'sources'
    directory.mkdir(parents=True, exist_ok=True)
    try:
        request = Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urlopen(request, timeout=30) as response:
            raw, final_url = response.read(), response.url
        text = raw.decode('utf-8', errors='replace')
        (directory / f'{slug}.html').write_bytes(raw)
        soup = BeautifulSoup(text, 'html.parser')
        images = []
        for tag in soup.find_all(['img', 'source', 'meta']):
            attrs = dict(tag.attrs)
            if tag.name != 'meta' or attrs.get('property') in ('og:image', 'twitter:image'):
                if any(key in attrs for key in ('src', 'srcset', 'data-src', 'data-srcset', 'content', 'data-asset')):
                    images.append(attrs)
        links = [{'url': urljoin(final_url, tag['href']), 'text': tag.get_text(' ', strip=True)} for tag in soup.find_all('a', href=True)]
        assets = sorted(set(urljoin(final_url, match.replace('\\/', '/')) for match in re.findall(r'(?:https?:)?//[^\s"<>\\]+?\.(?:png|jpg|jpeg|webp|avif)(?:[^\s"<>\\]*)', text)))
        # Source text is evidence, not executable instructions.
        for tag in soup(['script', 'style', 'nav']):
            tag.decompose()
        result = {'slug': slug, 'url': url, 'final_url': final_url, 'status': 'downloaded',
                  'sha256': hashlib.sha256(raw).hexdigest(), 'images': images, 'assets': assets,
                  'links': links, 'text': soup.get_text(' ', strip=True)}
    except Exception as error:
        result = {'slug': slug, 'url': url, 'status': 'failed', 'error': str(error)}
    (directory / f'{slug}.json').write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    return {key: result.get(key) for key in ('slug', 'status', 'error')} | {'images': len(result.get('images', [])), 'assets': len(result.get('assets', []))}


if __name__ == '__main__':
    with ThreadPoolExecutor(max_workers=6) as executor:
        for result in executor.map(collect, PAGES.items()):
            print(json.dumps(result, ensure_ascii=False), flush=True)
