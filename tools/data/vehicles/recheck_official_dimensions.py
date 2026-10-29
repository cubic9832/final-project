"""Re-fetch existing official brochures; reuse text only for identical PDF hashes."""
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
from pathlib import Path
import re
from urllib.request import Request,urlopen

ROOT=Path(__file__).resolve().parents[3]
OUTPUT=ROOT/'data/vehicles/web-recheck-20261028'
LABELS={'length_mm':r'전\s*장','width_mm':r'전\s*폭','height_mm':r'전\s*고',
    'wheelbase_mm':r'(?:축\s*간\s*거\s*리|축\s*거|휠\s*베\s*이\s*스)'}
BOUNDS={'length_mm':(2500,6000),'width_mm':(1300,2300),'height_mm':(900,2600),'wheelbase_mm':(1800,4000)}


def fetch(item):
    url,expected=item
    try:
        with urlopen(Request(url,headers={'User-Agent':'Mozilla/5.0'}),timeout=20) as response:
            body=response.read(40_000_001)
        actual=hashlib.sha256(body).hexdigest()
        return {'url':url,'expected_sha256':expected,'actual_sha256':actual,
            'status':'unchanged' if actual==expected and body.startswith(b'%PDF') else 'changed-or-not-pdf'}
    except Exception as error:
        return {'url':url,'expected_sha256':expected,'status':'unavailable','error':type(error).__name__}


def dimensions(document):
    values={}
    for key,label in LABELS.items():
        found=set()
        for page in document['pages']:
            for match in re.finditer(label+r'\s*(?:\(\s*mm\s*\))?\s*([\d,]{4,6})(?![\d,])',page['text'],re.I):
                number=int(match[1].replace(',',''))
                if BOUNDS[key][0]<=number<=BOUNDS[key][1]:
                    found.add(number)
        if len(found)==1:
            values[key]=found.pop()
    return values


def main():
    read=lambda p:json.loads(p.read_text(encoding='utf-8'))
    manifest=read(ROOT/'data/vehicles/official-model-manifest.json')['models']
    originals=read(ROOT/'data/vehicles/complete-specifications-20261028/vehicles.json')
    families={(x['brand'],x['model']) for x in originals}
    docs={}
    for model in manifest:
        if (model['brand'],model['model']) not in families:
            continue
        for doc in model['documents']:
            if doc['kind']=='catalog' and doc.get('extractedPath') and doc.get('sha256'):
                docs[(doc['url'],doc['sha256'])]=doc
    with ThreadPoolExecutor(max_workers=4) as pool:
        checks=list(pool.map(fetch,docs))
    status={(x['url'],x.get('expected_sha256')):x for x in checks}
    reviews=[];decisions=[]
    for model in manifest:
        key=(model['brand'],model['model'])
        if key not in families:
            continue
        available=[]
        for doc in model['documents']:
            if (doc['url'],doc.get('sha256')) not in docs:
                continue
            check=status[(doc['url'],doc['sha256'])]
            if check['status']!='unchanged':
                continue
            path=ROOT/'data/vehicles'/doc['extractedPath']
            values=dimensions(read(path))
            original_lengths={r['specifications']['length_mm']['value'] for r in originals if (r['brand'],r['model'])==key and r['specifications']['length_mm']['status']!='estimated'}
            # A known-length contradiction means generation/body identity is unresolved.
            if 'length_mm' not in values or original_lengths and not any(abs(n-values['length_mm'])<=10 for n in original_lengths):
                continue
            available.append({'publisher':model['brand'],'origin_id':model['brand'],
                'official':True,'url':doc['url'],'verification':'page-reviewed','compatible':True,
                'conditions':'동일 URL의 공식 PDF 재다운로드 해시 일치; 원장 전장과 차체 일치 확인; 지역/옵션 차이 가능',
                'evidence_type':'reported-specification','values':values,
                'document_sha256':doc['sha256'],'extracted_path':doc['extractedPath'],
                'extracted_sha256':hashlib.sha256(path.read_bytes()).hexdigest()})
        decisions.append({'brand':key[0],'model':key[1],'status':'matched-official-document' if available else 'no-unchanged-compatible-document'})
        if available:
            reviews.append({'selector':{'brand':key[0],'model':key[1]},
                'scope':'재검토 공식 카탈로그의 단일값 차체 치수; 원본 재무/정원 검증은 유지','samples':available})
    OUTPUT.mkdir(parents=True,exist_ok=True)
    for name,data in [('official-fetch-audit.json',{'checks':checks,'families':decisions}),
        ('official-dimension-reviews.json',{'reviews':reviews})]:
        (OUTPUT/name).write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps({'documents':len(checks),'unchanged':sum(c['status']=='unchanged' for c in checks),
        'families_checked':len(decisions),'families_matched':len(reviews),
        'dimensions':sum(len(r['samples'][0]['values']) for r in reviews)},ensure_ascii=False))


if __name__=='__main__':
    main()
