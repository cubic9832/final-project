"""Archive public KEA search results without saving anonymous session tokens."""
import argparse
import hashlib
import http.cookiejar
import json
import urllib.parse
import urllib.request
from datetime import date
from pathlib import Path

from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parents[3]
SEARCH_URL = 'https://min24.energy.or.kr/trans_hp/AHP/HP_03/HP_03_01_010.do'
QUERIES = {'320d':'320d','x5':'X5 xDrive30d','x1':'X1 sDrive18d',
           'x4':'X4 xDrive20d','k5':'K5','sorento':'쏘렌토'}


def collect(output):
    output.mkdir(parents=True,exist_ok=True)
    session=urllib.request.build_opener(urllib.request.HTTPCookieProcessor(http.cookiejar.CookieJar()))
    page=session.open(SEARCH_URL,timeout=20).read().decode('utf-8')
    document=BeautifulSoup(page,'html.parser')
    token=document.select_one('meta[name=_csrf]')['content']
    header=document.select_one('meta[name=_csrf_header]')['content']
    for key,query in QUERIES.items():
        parameters={'P_PKG_NM':'AHP_03_01_010_L','P_PKG_AREA':'AHP','P_MODL_NM':query}
        request=urllib.request.Request('https://min24.energy.or.kr/trans_hp/cmn/AHP_L.do',
            data=urllib.parse.urlencode(parameters).encode(),
            headers={header:token,'Referer':SEARCH_URL,'User-Agent':'Mozilla/5.0'})
        raw=session.open(request,timeout=20).read()
        rows=json.loads(raw)['list']
        snapshot={'source_url':SEARCH_URL,'query':query,'checked_on':date.today().isoformat(),
                  'response_sha256':hashlib.sha256(raw).hexdigest(),'rows':rows}
        (output/f'kea-{key}.json').write_text(json.dumps(snapshot,ensure_ascii=False,indent=2),encoding='utf-8')
        print(f'{key}: {len(rows)} registrations')


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--output',type=Path,required=True,help='New versioned source directory')
    collect(parser.parse_args().output)
