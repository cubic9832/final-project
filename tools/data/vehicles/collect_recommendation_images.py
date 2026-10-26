"""Collect model-specific official source photos; never synthesize car identities."""
import concurrent.futures
import hashlib
import io
import json
from pathlib import Path
import urllib.parse
import urllib.request

from PIL import Image

ROOT=Path(__file__).resolve().parents[3]
OUTPUT=ROOT/'data/vehicles/recommendation-images-v2'


def source_plan():
    """Only download the reviewed front three-quarter sources used by the UI."""
    return json.loads((OUTPUT / 'reviewed-sources.json').read_text(encoding='utf-8'))


def download(row):
    try:
        url=urllib.parse.quote(row['image_url'],safe=':/?=&%,-._')
        request=urllib.request.Request(url,headers={'User-Agent':'Mozilla/5.0'})
        raw=urllib.request.urlopen(request,timeout=25).read()
        image=Image.open(io.BytesIO(raw));image.load()
        extension={'PNG':'png','JPEG':'jpg','WEBP':'webp','AVIF':'avif'}[image.format]
        path=OUTPUT/'sources'/f"{row['slug']}.{extension}"
        path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(raw)
        alpha=image.convert('RGBA').getchannel('A')
        return dict(row,file=str(path.relative_to(ROOT)),width=image.width,height=image.height,
                    transparent=alpha.getextrema()[0]<255,sha256=hashlib.sha256(raw).hexdigest(),status='downloaded')
    except Exception as error:return dict(row,status='failed',error=str(error))


if __name__=='__main__':
    OUTPUT.mkdir(parents=True,exist_ok=True)
    with concurrent.futures.ThreadPoolExecutor(max_workers=6) as pool:rows=list(pool.map(download,source_plan()))
    (OUTPUT/'download-results.json').write_text(json.dumps(rows,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps([{k:r.get(k) for k in ('model','slug','width','height','transparent','status','error')} for r in rows],ensure_ascii=False))
