"""Make source-linked contact sheets for explicit whole-catalog visual review."""
import hashlib
import json
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[3]
OUTPUT = ROOT/'data/vehicles/full-trait-evidence-20261028'


def read(path):
    return json.loads(path.read_text(encoding='utf-8'))


def main():
    catalog = read(ROOT/'data/households/synthetic/preference-cohorts-training-20261028/catalog.json')
    manifests = read(ROOT/'data/vehicles/recommendation-images-v2/manifest.json')+read(ROOT/'data/vehicles/new-model-details-20261028/image-manifest.json')
    lookup = {(r['brand'],r['model']):r for r in manifests}
    own = read(ROOT/'data/vehicles/official-image-review/front-three-quarter/manifest.json')['vehicles']
    own = {r['labelCode']:r for r in own}
    from tools.data.vehicles.build_recommendation_images import EXISTING
    records = []
    for number,key in enumerate(sorted({(r['brand'],r['model']) for r in catalog}),1):
        entry = lookup.get(key)
        if entry is None:
            raise ValueError(key)
        path = ROOT/'front/public'/entry['src'].lstrip('/')
        original = own.get(EXISTING.get('::'.join(key)),{})
        records.append({'number':number,'brand':key[0],'model':key[1],
            'image_path':path.relative_to(ROOT).as_posix(),
            'image_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),
            'source_url':entry.get('source_page') or original.get('sourcePage'),
            'source_image_url':entry.get('source_image_url') or original.get('imageUrl'),
            'scope':'representative-family-image; trim/generation differences possible'})
    OUTPUT.mkdir(parents=True,exist_ok=True)
    (OUTPUT/'visual-review-index.json').write_text(json.dumps(records,ensure_ascii=False,indent=2),encoding='utf-8')
    font = ImageFont.truetype('C:/Windows/Fonts/malgun.ttf',15)
    for offset in range(0,len(records),20):
        canvas = Image.new('RGB',(1280,1250),'white')
        draw = ImageDraw.Draw(canvas)
        for index,row in enumerate(records[offset:offset+20]):
            x,y = (index%4)*320,(index//4)*250
            with Image.open(ROOT/row['image_path']) as source:
                image = source.convert('RGBA')
                image.thumbnail((310,205))
                canvas.paste(image,(x+(320-image.width)//2,y+(205-image.height)//2),image)
            draw.text((x+8,y+208),f"{row['number']:03d} {row['brand']}",fill='black',font=font)
            draw.text((x+8,y+230),row['model'],fill='black',font=font)
        canvas.save(OUTPUT/f'visual-contact-{offset//20+1}.png')
    print(json.dumps({'model_families':len(records),'sheets':(len(records)+19)//20}))


if __name__=='__main__':
    main()
