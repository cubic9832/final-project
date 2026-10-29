"""Collect full-car alternatives from already inspected official pages."""
from concurrent.futures import ThreadPoolExecutor
import json
from build_new_vehicle_assets import DATA, download, save
from collect_remaining_vehicle_assets import ROWS

def main():
    rows = [dict(zip(('slug', 'brand', 'model', 'source_url', 'image_url'), row)) for row in ROWS if row[0].startswith('porsche')]
    urls = ['https://a.storyblok.com/f/322327/1720x1210/260571d076/cz25w12ix0011-911-carrera-gts-front.png',
            'https://a.storyblok.com/f/322327/1720x1210/00b18f3472/cz25w13ix0011-911-carrera-gts-cabrio-front.png',
            'https://a.storyblok.com/f/322327/1720x1210/4f744126bb/911-targa-4-gts-front.png']
    for row, url in zip(rows, urls):
        row['slug'] += '-full'
        row['image_url'] = url
    mini = json.loads((DATA/'sources/mini-browser-images.json').read_text(encoding='utf-8'))
    url = next(i['src'] for i in mini if 'stage-wide.webp.asset' in i['src'])
    rows.append({'slug':'mini-convertible','brand':'MINI','model':'Cooper Convertible','source_url':ROWS[2][3], 'image_url':url.replace('www.mini.co.kr','mini.co.kr')})
    with ThreadPoolExecutor(max_workers=4) as pool:
        results = list(pool.map(download, rows))
    save('alternative-image-downloads.json', results)
    for r in results:
        print({k:r.get(k) for k in ('slug','status','width','height','transparent','error')}, flush=True)

if __name__ == '__main__':
    main()
