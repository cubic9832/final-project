"""Cache public official sources for the reviewed new-model candidates."""

import argparse
import concurrent.futures
import hashlib
import io
import json
import re
import subprocess
from pathlib import Path
from urllib.parse import urljoin, urlparse

from bs4 import BeautifulSoup
from pypdf import PdfReader

ROOT = Path(__file__).resolve().parents[3]
OUTPUT = ROOT / 'data/vehicles/new-model-specifications-20261027'
CACHE = OUTPUT / 'sources'


def collect_one(request):
    url = request if isinstance(request, str) else request['url']
    post_key = None if isinstance(request, str) else request.get('post_file_key')
    key = hashlib.sha256((url + (post_key or '')).encode()).hexdigest()[:20]
    metadata_path = CACHE / f'{key}.json'
    if metadata_path.exists():
        return json.loads(metadata_path.read_text(encoding='utf-8'))
    raw_path = CACHE / f'{key}.raw'
    result = {'id': key, 'url': url, 'checked_on': '2026-10-27'}
    if post_key:
        result['post_file_key'] = post_key
    try:
        command = ['curl.exe', '--location', '--max-time', '22',
            '--silent', '--show-error', '--user-agent', 'Mozilla/5.0',
            '--output', str(raw_path), '--write-out', '%{http_code}\n%{url_effective}']
        if post_key:
            command += ['--data-urlencode', 'file_key=' + post_key]
        process = subprocess.run(command + [url],
            capture_output=True, text=True, timeout=27)
        status, _, final_url = process.stdout.partition('\n')
        if process.returncode or status != '200':
            raise ValueError(f'HTTP {status}: {process.stderr[:180]}')
        content = raw_path.read_bytes()
        result.update(final_url=final_url, sha256=hashlib.sha256(content).hexdigest(), bytes=len(content))
        if content.startswith(b'%PDF'):
            result['kind'] = 'PDF'
            result['pages'] = [{'page': index + 1, 'text': page.extract_text() or ''}
                               for index, page in enumerate(PdfReader(io.BytesIO(content)).pages)]
            result['text'] = '\n'.join(row['text'] for row in result['pages'])
            result['links'] = []
        else:
            soup = BeautifulSoup(content, 'html.parser')
            result['kind'] = 'HTML'
            result['links'] = [{'label': a.get_text(' ', strip=True), 'url': urljoin(final_url, a['href'])}
                               for a in soup.find_all('a', href=True)
                               if a['href'] and not a['href'].startswith(('#', 'javascript:', 'mailto:', 'tel:'))]
            result['tables'] = [[[cell.get_text(' ', strip=True) for cell in row.find_all(['td', 'th'])]
                                 for row in table.find_all('tr')] for table in soup.find_all('table')]
            result['structured_data'] = [a.get_text() for a in soup.find_all('script', type='application/ld+json')]
            result['pdf_links'] = sorted(set(urljoin(final_url, link.replace('&amp;', '&'))
                for link in re.findall(r'''[^\s"'<>]+\.pdf(?:\?[^\s"'<>]*)?''', str(soup))))
            for tag in soup(['script', 'style', 'noscript', 'svg', 'header', 'footer', 'nav']):
                tag.decompose()
            result['text'] = soup.get_text('\n', strip=True)
        result['status'] = 'EXTRACTED'
    except Exception as error:
        result.update(status='FETCH_FAILED', error=str(error))
    metadata_path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--urls', type=Path)
    args = parser.parse_args()
    CACHE.mkdir(parents=True, exist_ok=True)
    if args.urls:
        urls = json.loads(args.urls.read_text(encoding='utf-8'))
    else:
        candidates = json.loads((ROOT / 'data/vehicles/korea-official-models-20261027/new-model-candidates.json').read_text(encoding='utf-8'))
        urls = sorted({row['source_url'] for row in candidates} | {
            'https://www.mercedes-benz.co.kr/passengercars/models/price-list.html',
            'https://www.mercedes-benz.co.kr/passengercars/models/catalogue.html',
            'https://www.audi.co.kr/ko/customer-area/download-center/',
            'https://www.bmw.co.kr/ko/all-models.html',
            'https://www.genesis.com/kr/ko/support/download-center/genesis-models.html',
        })
    with concurrent.futures.ThreadPoolExecutor(max_workers=6) as pool:
        for result in pool.map(collect_one, urls):
            print(json.dumps({key: result[key] for key in ('id', 'url', 'status')}, ensure_ascii=False), flush=True)
    summaries = []
    for path in sorted(CACHE.glob('*.json')):
        row = json.loads(path.read_text(encoding='utf-8'))
        summaries.append({key: value for key, value in row.items() if key not in ('text', 'pages', 'tables', 'links', 'structured_data', 'pdf_links')})
    (OUTPUT / 'retrieval.json').write_text(json.dumps(summaries, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


if __name__ == '__main__':
    main()
