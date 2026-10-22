from tools.data.households.paths import SYNTHETIC_ROOT

"""Save the public price documents used for this imported-car snapshot."""
import hashlib
import json
import urllib.request
from pathlib import Path

ROOT=SYNTHETIC_ROOT / 'imported-owners'
SOURCES={
 'bmw-pricelist.pdf':'https://www.bmw.co.kr/content/dam/bmw/marketKR/bmw_co_kr/Pricelist/PRICELIST_JUNE2026.pdf.asset.1781249167044.pdf',
 'mercedes-e200.html':'https://www.mercedes-benz.co.kr/passengercars/brand/news-events/news-story/2026/news-20260424.html',
 'lexus-es.html':'https://www.lexus.co.kr/build-your-car/?model=es350h',
 'volvo-xc60.html':'https://www.volvocars.com/kr/news/culture/20250804-New-XC60-Officially-Launched/',
 'tesla-secondary-carnoon.html':'https://www.carnoon.co.kr/newcar/vehicle/11738'
}


def main():
    folder=ROOT/'sources';folder.mkdir(exist_ok=True)
    records=[]
    for name,url in SOURCES.items():
        try:
            request=urllib.request.Request(url,headers={'User-Agent':'Mozilla/5.0'})
            with urllib.request.urlopen(request,timeout=40) as response:
                content=response.read();final=response.geturl()
            if name.endswith('.pdf') and not content.startswith(b'%PDF'):raise ValueError('Not PDF')
            (folder/name).write_bytes(content)
            records.append({'file':name,'url':url,'final_url':final,'bytes':len(content),'sha256':hashlib.sha256(content).hexdigest(),'status':'downloaded','source_level':'secondary' if name.startswith('tesla') else 'manufacturer'})
        except Exception as error:
            records.append({'file':name,'url':url,'status':'not_downloaded','error':str(error)})
    (ROOT/'source-manifest.json').write_text(json.dumps(records,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(records,ensure_ascii=False))


if __name__=='__main__':main()
