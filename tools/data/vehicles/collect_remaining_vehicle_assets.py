"""Download selected public manufacturer/dealer images with source provenance."""
from concurrent.futures import ThreadPoolExecutor
from build_new_vehicle_assets import DATA, download, save

ROWS = [
    ('bmw-8-gran-coupe', 'BMW', '8시리즈 그란쿠페', 'https://www.bmw.co.kr/ko/more-bmw/exclusive-models.html', 'https://bmw.scene7.com/is/image/BMW/gkl_lp_8er-gran-coupe_exterior_0725%3A3to2?fit=constrain%2C1&fmt=webp-alpha&wid=1493'),
    ('bmw-z4-front', 'BMW', 'Z4', 'https://www.bmw.co.kr/ko/all-models/z-series/z4-roadster/bmw-z4-roadster.html', 'https://bmw.scene7.com/is/image/BMW/g29-roadster_intro%3A16to7?fit=constrain%2C1&fmt=webp-alpha&wid=2560'),
    ('mini-convertible', 'MINI', 'Cooper Convertible', 'https://www.mini.co.kr/ko_KR/home/range/mini-cooper-convertible.html', 'https://www.mini.co.kr/content/dam/MINI/common/Range/new-generation/cooper/convertible/bodytype-hub/mini-F67-exterior.webp'),
    ('maserati-granturismo', '마세라티', 'GranTurismo', 'https://www.maserati.com/kr/ko/models/granturismo', 'https://maserati.scene7.com/is/image/maserati/maserati/worldwide/models/granturismo/model-pages/base-trim/granturismo-blue-overview-desktop.jpg?$1800x2000$&fit=constrain'),
    ('maserati-grancabrio', '마세라티', 'GranCabrio', 'https://www.maserati.com/kr/ko/models/grancabrio', 'https://maserati.scene7.com/is/image/maserati/maserati/worldwide/models/grancabrio/model-pages/gracabrio-trim-dark-green-front-left-view-desktop.jpg?$1800x2000$&fit=constrain'),
    ('porsche-911-coupe', '포르쉐', '911 쿠페', 'https://www.porsche.com/korea/ko/models/911/carrera-models/911-carrera-gts/', 'https://a.storyblok.com/f/322327/664x484/2d16934fc8/cz25w12ox0005-911-carrera-gts-side.jpg'),
    ('porsche-911-cabriolet', '포르쉐', '911 카브리올레', 'https://www.porsche.com/korea/ko/models/911/carrera-cabriolet-models/911-carrera-gts-cabriolet/', 'https://a.storyblok.com/f/322327/3840x1236/6eab0364b4/cz25w13ox0005-911-carrera-gts-cabrio-driving.jpg'),
    ('porsche-911-targa', '포르쉐', '911 타르가', 'https://www.porsche.com/korea/ko/models/911/targa-models/911-targa-4-gts/', 'https://a.storyblok.com/f/322327/1496x1986/94d202d361/cz25w16ox0001-911-targa-4-gts-side.jpg'),
    ('ferrari-roma-spider', '페라리', 'Roma Spider', 'https://www.ferraribeverlyhills.com/articles/discover-a-new-chapter-with-the-ferrari-roma-spider', 'https://vrrb-prod-s3.s3.us-west-1.amazonaws.com/strapi/xlarge_Pulls_00_14_59_03_Still005_8aae0fb020.jpg'),
]

if __name__ == '__main__':
    rows = [dict(zip(('slug', 'brand', 'model', 'source_url', 'image_url'), row)) for row in ROWS]
    with ThreadPoolExecutor(max_workers=6) as pool:
        results = list(pool.map(download, rows))
    save('remaining-image-downloads.json', results)
    for result in results:
        print({key: result.get(key) for key in ('slug', 'status', 'width', 'height', 'transparent', 'error')}, flush=True)
