"""Download public purchase-study files through the publisher's download form."""
import hashlib
import http.cookiejar
import json
import urllib.parse
import urllib.request
from pathlib import Path

from bs4 import BeautifulSoup

ROOT = (Path(__file__).resolve().parents[3] / 'data/purchase-patterns')
PAGE = 'https://consumerinsight.co.kr/dataverse_detail.aspx?cate=0&id=2025120112&keyFlag=0&schFlag=0&type=0&viewFlag=1'
DOCUMENTS = {
    'carcharts-introduction.pdf': 'https://carcharts.carisyou.net/manual/CarChartsIntroduce(20241007).pdf',
    'carcharts-manual.pdf': 'https://carcharts.carisyou.net/manual/CarChartsManual(20241007_v2.8).pdf',
    'consumerinsight-custom-data.pdf': 'https://www.consumerinsight.co.kr/up_files/2024_데이터바우처_홍보자료_신차초기반응.pdf',
}


def escaped_url(url):
    return urllib.parse.quote(url, safe=':/?=&%()')


def main():
    folder = ROOT / 'sources'
    folder.mkdir(parents=True, exist_ok=True)
    opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(http.cookiejar.CookieJar()))
    opener.addheaders = [('User-Agent', 'Mozilla/5.0')]
    manifest = []
    def save(name, content, source_url, response, category):
        (folder / name).write_bytes(content)
        record = {'filename': name, 'source_url': source_url, 'final_url': response.geturl(),
                  'bytes': len(content), 'sha256': hashlib.sha256(content).hexdigest(),
                  'content_type': response.headers.get('Content-Type'), 'category': category,
                  'checked_on': '2026-10-14'}
        manifest.append(record)
        print(json.dumps(record, ensure_ascii=True))
    for seq, stem in [(0, 'consumerinsight-2024-raw'), (1, 'consumerinsight-2024-codebook')]:
        with opener.open(PAGE, timeout=45) as response:
            actual_page = response.geturl()
            soup = BeautifulSoup(response.read(), 'html.parser')
        form = soup.find('form')
        values = {item['name']: item.get('value', '') for item in form.find_all('input', attrs={'name': True})
                  if item.get('type', '').lower() == 'hidden'}
        values['ctl00$ContentPlaceHolder1$hidFileSeq'] = str(seq)
        values['__EVENTTARGET'] = 'ctl00$ContentPlaceHolder1$hidbtnDownload'
        values['ctl00$ContentPlaceHolder1$hidbtnDownload'] = 'Download'
        request = urllib.request.Request(urllib.parse.urljoin(actual_page, form.get('action', actual_page)),
                                         data=urllib.parse.urlencode(values).encode(), headers={'Referer': actual_page})
        try:
            with opener.open(request, timeout=60) as response:
                content = response.read()
                if not content.startswith((b'PK', b'$FL2', b'$FL3')):
                    (folder / (stem + '-response.html')).write_bytes(content)
                    print(json.dumps({'not_downloaded': stem, 'response_type': response.headers.get('Content-Type')}))
                    continue
                disposition = response.headers.get('Content-Disposition', '')
                extension = '.xlsx' if '.xlsx' in disposition.lower() else '.sav' if '.sav' in disposition.lower() else '.zip'
                save(stem + extension, content, PAGE, response, 'raw_data' if seq == 0 else 'codebook')
        except Exception as error:
            print(json.dumps({'not_downloaded': stem, 'error': str(error)}))
    for name, url in DOCUMENTS.items():
        try:
            with opener.open(escaped_url(url), timeout=60) as response:
                content = response.read()
                if not content.startswith(b'%PDF'): raise ValueError('Not a PDF response')
                save(name, content, url, response, 'service_document_not_dataset')
        except Exception as error:
            print(json.dumps({'not_downloaded': name, 'error': str(error)}))
    (ROOT / 'source-manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding='utf-8')


if __name__ == '__main__':
    main()
