"""Download official, public household statistics without an API credential."""

import hashlib
import json
import urllib.parse
import urllib.request
from pathlib import Path

from bs4 import BeautifulSoup

ROOT = (Path(__file__).resolve().parents[3] / 'data/households')
BOK_PAGE = 'https://www.bok.or.kr/portal/bbs/B0000501/view.do?nttId=10094917&menuNo=201264'
EXPENDITURE_PDF = 'https://sri.kostat.go.kr/boardDownload.es?bid=214&list_no=443727&seq=1'


def download(url):
    request = urllib.request.Request(url, headers={'User-Agent': 'HouseholdStatisticsResearch/1.0'})
    with urllib.request.urlopen(request, timeout=45) as response:
        return response.read(), response.geturl(), response.headers.get('Content-Type', '')


def main():
    sources = ROOT / 'sources'
    sources.mkdir(parents=True, exist_ok=True)
    page, _, _ = download(BOK_PAGE)
    soup = BeautifulSoup(page, 'html.parser')
    excel = next(anchor for anchor in soup.find_all('a', href=True)
                 if '.xlsx' in anchor.get_text())
    url = urllib.parse.urljoin(BOK_PAGE, excel['href'])
    manifest = []
    for name, source_url, expected in [
        ('household-finance-welfare-2025.xlsx', url, b'PK'),
        ('household-income-expenditure-2025-q4.pdf', EXPENDITURE_PDF, b'%PDF'),
    ]:
        content, final_url, content_type = download(source_url)
        if not content.startswith(expected):
            raise ValueError(f'{name}: unexpected response {content_type}')
        (sources / name).write_bytes(content)
        manifest.append({'filename': name, 'sourceUrl': source_url, 'finalUrl': final_url,
                         'landingPageUrl': BOK_PAGE if name.endswith('.xlsx') else EXPENDITURE_PDF,
                         'checkedOn': '2026-10-14', 'sha256': hashlib.sha256(content).hexdigest(),
                         'sizeBytes': len(content), 'contentType': content_type,
                         'dataLevel': '가구 집계 통계표',
                         'microdata': False})
        print(json.dumps({'file': name, 'bytes': len(content), 'url': source_url}, ensure_ascii=True))
    (ROOT / 'source-manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding='utf-8')


if __name__ == '__main__':
    main()
