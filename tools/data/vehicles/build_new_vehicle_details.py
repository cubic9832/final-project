"""Publish display-only, source-backed specifications without rewriting ML snapshots."""
import hashlib
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
DATA = ROOT / 'data/vehicles/new-model-details-20261028'
SOURCE = DATA / 'sources'


def read(path):
    return json.loads(path.read_text(encoding='utf-8'))


def ax_text(path):
    return re.findall(r'^\s*\d+ text (.+)$', path.read_text(encoding='utf-8'), re.M)


def pairs(values, labels):
    # Some pages repeat a label in the highlight and detailed body table.
    result = []
    for label in labels:
        matches = [values[i + 1] for i, text in enumerate(values[:-1]) if text == label]
        unique = list(dict.fromkeys(matches))
        if len(unique) == 1:
            result.append({'label': label, 'value': unique[0]})
        elif unique:
            result.append({'label': label, 'value': ' / '.join(unique), 'status': 'source-conflict'})
    return result


PORSCHE_CODES = {'Carrera GTS': '992142', 'Carrera 4 GTS': '992442',
    'Carrera GTS Cabriolet': '992342', 'Carrera 4 GTS Cabriolet': '992642',
    'Targa 4 GTS': '992542', 'GT3': '992812', 'GT3 with Touring Package': '992822',
    'Spirit 70': '992352', 'Turbo S': '992452', 'Turbo S Cabriolet': '992652'}
PORSCHE_LABELS = ['Length', 'Width', 'Width (with mirrors)', 'Wheelbase',
    'Height (PASM)', 'Height (PASM Sport Suspension)', 'Height (PASM -10 DIN)',
    'Height (PASM -20 DIN)', 'Height, steel suspension (PASM DIN)', 'Displacement',
    'Number of cylinders', 'Power combined (PS)', 'Power combined (kW)', 'Power (PS)',
    'Power (kW)', 'Max. torque', 'Torque combined', 'Transmission', 'Top speed',
    'Acceleration 0 - 100 km/h with Sport Chrono Package', 'Acceleration 0 - 100 km/h',
    'Luggage compartment volume, front', 'Open luggage compartment volume (behind front seats)',
    'Maximum load', 'Turning circle']

# Values transcribed from the saved official Korean model pages. Missing values
# stay missing; for example M440i's torque is not copied into a 420i record.
BMW = {
    'M240i xDrive 쿠페 프로': ('bmw-2-coupe', [('엔진', '직렬 6기통 가솔린 터보'), ('최고 출력', '387 PS / 285 kW'), ('0–100 km/h', '4.3 s'), ('변속기', '8단 스텝트로닉 스포츠'), ('구동', 'xDrive 사륜구동'), ('국내 복합연비', '9.6 km/L')]),
    'M2 쿠페': ('bmw-2-coupe', [('엔진', '직렬 6기통 가솔린 터보'), ('최고 출력', '480 PS / 353 kW'), ('최대 토크', '61.2 kg·m'), ('0–100 km/h', '4.0 s'), ('최고 속도', '250 km/h'), ('변속기', '8단 M 스텝트로닉 스포츠'), ('구동', '후륜구동'), ('국내 복합연비', '8.5 km/L')]),
    '220 그란 쿠페 M 스포츠 디자인': ('bmw-2-gran-coupe', [('최고 출력', '204 PS / 150 kW'), ('0–100 km/h', '7.3 s'), ('최고 속도', '250 km/h'), ('국내 복합연비', '12.3 km/L')]),
    '420i 쿠페 M 스포츠 프로': ('bmw-4-coupe', [('최고 출력', '190 PS / 140 kW')]),
    'M440i xDrive 쿠페 프로': ('bmw-4-coupe', [('최고 출력', '392 PS / 288 kW'), ('최대 토크', '520 Nm'), ('0–100 km/h', '4.5 s'), ('최고 속도', '250 km/h'), ('국내 복합연비', '11.4 km/L')]),
    'M4 컴페티션 M xDrive': ('bmw-m4-coupe', [('엔진', '직렬 6기통 가솔린 터보'), ('최고 출력', '530 PS / 390 kW'), ('최대 토크', '650 Nm'), ('0–100 km/h', '3.5 s'), ('최고 속도', '250 km/h'), ('국내 복합연비', '8.1 km/L')]),
    '420i 그란 쿠페 M 스포츠 프로': ('bmw-4-gran-coupe', [('최고 출력', '190 PS / 140 kW'), ('최대 토크', '31.6 kg·m'), ('0–100 km/h', '7.9 s'), ('최고 속도', '235 km/h'), ('국내 복합연비', '11.8 km/L')]),
    'i4 eDrive40 그란 쿠페 M 스포츠': ('bmw-i4', [('최고 출력', '340 PS / 250 kW'), ('0–100 km/h', '5.6 s'), ('최고 속도', '190 km/h'), ('국내 인증 주행거리', '432 km'), ('국내 복합전비', '4.7 km/kWh')]),
    '420i 컨버터블 M 스포츠': ('bmw-4-convertible', [('최고 출력', '190 PS / 140 kW'), ('최대 토크', '31.6 kg·m'), ('0–100 km/h', '8.2 s'), ('최고 속도', '236 km/h'), ('국내 복합연비', '12.3 km/L')]),
    'M4 컴페티션 M xDrive 컨버터블': ('bmw-m4-convertible', [('최고 출력', '530 PS / 390 kW'), ('최대 토크', '650 Nm')]),
    'M850i xDrive 그란 쿠페 M 퍼포먼스': ('bmw-8-gran-coupe-release', [('엔진', 'V8 가솔린 터보'), ('최고 출력', '530 PS'), ('최대 토크', '76.5 kg·m'), ('0–100 km/h', '3.9 s'), ('변속기', '8단 스텝트로닉 스포츠 자동')]),
    'sDrive20i M 스포츠': ('bmw-z4', [('엔진', '직렬 4기통 가솔린 터보'), ('최고 출력', '197 PS / 145 kW'), ('최대 토크', '320 Nm'), ('0–100 km/h', '6.8 s'), ('최고 속도', '241 km/h'), ('국내 복합연비', '10.7 km/L')]),
    'M40i': ('bmw-z4', [('엔진', '직렬 6기통 가솔린 터보'), ('최고 출력', '387 PS / 285 kW'), ('0–100 km/h', '4.1 s')]),
}


def model_details(vehicle, ferrari):
    brand, model, trim = (vehicle[key] for key in ('brand', 'model', 'trim'))
    notes, groups, files = [], [], []
    if brand == 'Porsche':
        code = PORSCHE_CODES[trim]
        source = SOURCE / f'porsche-{code}-specs.txt'
        values = ax_text(source)
        if not values or values[0] != '911 ' + trim:
            raise ValueError(f'Incorrect Porsche panel: {trim}')
        fields = pairs(values, PORSCHE_LABELS)
        url = f'https://www.porsche.com/korea/ko/models/911/configure/#technical-data-{code}'
        files = [source]
        notes = ['한국 공식 구성기의 EU/WLTP 참조 제원입니다. 국내 공인 연비나 기본 정원으로 대입하지 않습니다.', 'PASM 높이와 Sport Chrono 가속 조건을 원문대로 구분합니다. 출력이 중복·충돌하면 해당 항목을 확정값으로 쓰지 않습니다.']
    elif brand == 'Ferrari':
        table = ferrari[model]
        groups = table['technical_groups']
        fields = [{'label': group['name'] + ' · ' + item['label'], 'value': item['value']}
                  for group in groups for item in group['items'] if item.get('value')]
        url = table['source_url']
        files = [DATA / ('ferrari-roma-tables.json' if model == 'Roma Spider' else 'ferrari-technical-tables.json')]
        notes = ['제조사 공식 딜러의 국제 사양 참조입니다. 국내 주문 가능 여부·공식 신차 가격·공인 연비 확인과는 별개입니다.', '요약 카드와 기술 제원 표가 다를 때 기술 제원 표를 보존합니다.']
        if model == 'Roma Spider':
            notes.append('공식 딜러에서 Past Models로 분류되어 있어 현행 국내 신차 주문 가능으로 표시하지 않습니다.')
    elif brand == 'BMW':
        slug, values = BMW[trim]
        source = SOURCE / f'{slug}-browser.json'
        page = read(source)
        url, files = page['url'], [source]
        fields = [{'label': label, 'value': value} for label, value in values]
        notes = ['공식 한국 페이지에 공개된 해당 엔진·트림 사양입니다. 미확인 차체 치수·정원은 다른 트림에서 복사하지 않습니다.']
        if trim == 'M440i xDrive 쿠페 프로':
            notes.append('원문 토크 520 Nm와 괄호의 55.1 kg·m가 서로 환산되지 않아 Nm 원문만 표시합니다.')
        if trim == 'sDrive20i M 스포츠':
            notes.append('0–100 km/h는 모델 제원 표 6.8초와 FAQ 6.6초가 달라 제원 표를 표시합니다.')
        if trim == '420i 쿠페 M 스포츠 프로':
            url = 'https://www.press.bmwgroup.com/korea/article/detail/T0444401KO/'
            notes.append('출력은 부분변경 국내 출시 공식 보도자료로 교차 확인했습니다.')
    elif brand == 'MINI':
        index = {'C Classic': 0, 'S Favoured': 1, 'JCW': 2}[trim]
        values = [('배기량', '1,998 cc'), ('최고 출력', ['163 PS / 120 kW', '204 PS / 150 kW', '231 PS / 170 kW'][index]),
                  ('최대 토크', ['25.5 kg·m', '30.6 kg·m', '38.8 kg·m'][index]),
                  ('변속기', '7단 스텝트로닉 더블 클러치' + (' 스포츠' if index == 2 else '')),
                  ('0–100 km/h', ['8.2 s', '6.9 s', '6.4 s'][index]), ('최고 속도', ['220 km/h', '237 km/h', '245 km/h'][index]),
                  ('전장 / 전폭 / 전고', '3,880 / 1,745 / 1,430 mm'), ('휠베이스', '2,495 mm'), ('정원', '4명'),
                  ('트렁크 용량', '160–215 L'), ('공차중량', ['1,410 kg', '1,425 kg', '1,445 kg'][index]),
                  ('국내 복합연비', ['12.0 km/L', '12.2 km/L', '11.8 km/L'][index])]
        fields = [{'label': label, 'value': value} for label, value in values]
        url = 'https://minikr.co.kr/2023/pdf-cta/images/MINI-COOPER-CONVERTIBLE-Specification.pdf'
        files = [SOURCE / 'mini-spec.pdf', SOURCE / 'mini-spec-review.png']
    elif brand == '토요타':
        fields = [{'label':label, 'value':value} for label,value in [('배기량','2,387 cc'), ('엔진','수평대향 4기통 가솔린'), ('최고 출력','231 PS'), ('최대 토크','25.5 kg·m'), ('변속기','6단 수동'), ('구동','후륜구동'), ('전장','4,265 mm'), ('정원','4명'), ('국내 복합연비','9.5 km/L')]]
        url = 'https://www.toyota.co.kr/download/model/GR86_spec.pdf'
        files = [SOURCE / 'toyota-gr86.json']
    elif brand == '마세라티':
        power = '550' if '550' in trim else '490'
        slug = 'grancabrio' if model == 'GranCabrio' else 'granturismo'
        source = SOURCE / f'maserati-{slug}-{power}-specs.txt'
        values = source.read_text(encoding='utf-8').splitlines()
        fields = pairs(values, ['전장','미러 포함 전폭','미러 제외 전폭','높이','휠베이스','프런트 트랙','리어 트랙','타이어 사이즈(전)','타이어 사이즈(후)','배기량','엔진 타입','최대 출력','최대 속도','가속'])
        url = f'https://www.maserati.com/kr/ko/models/{slug}'
        files = [source]
        notes = ['공식 한국 페이지의 2026년형 490PS/550PS 사양을 각각 확인했습니다. 유럽 효율 등급을 국내 공인 연비로 쓰지 않습니다.']
    elif brand == 'Lamborghini':
        source = SOURCE / f'lamborghini-{model.lower()}-full-specs.txt'
        values = ax_text(source)
        labels = {
            'MAX POWER (COMBINED ICE+EE)': '시스템 합산 출력', 'MAX POWER @ RPM (ICE)': '엔진 최고 출력',
            'MAX TORQUE @ RPM (ICE)': '엔진 최대 토크', 'MAX. POWER (KW/CV)': '엔진 최고 출력',
            'MAX. TORQUE': '엔진 최대 토크', 'WIDTH (EXCLUDING MIRRORS)': '전폭 (미러 제외)',
            'WIDTH (INCLUDING MIRRORS)': '전폭 (미러 포함)', 'OVERALL WIDTH (EXCLUDING MIRRORS)': '전폭 (미러 제외)',
            'OVERALL WIDTH (INCLUDING MIRRORS)': '전폭 (미러 포함)', 'OVERALL LENGTH': '전장', 'OVERALL HEIGHT': '전고',
            'ACCELERATION 0-100 KM/H (0-62 MPH)': '0–100 km/h', 'ACCELERATION 0-100 KM/H': '0–100 km/h',
            'ENGINE': '엔진', 'DISPLACEMENT': '배기량', 'TRANSMISSION': '변속기 방식', 'GEARBOX': '기어 단수',
            'CLUTCH': '클러치', 'TOP SPEED': '최고 속도', 'MAX SPEED': '최고 속도', 'WHEELBASE': '휠베이스',
            'LENGTH': '전장', 'HEIGHT': '전고', 'DRY WEIGHT': '건조중량',
        }
        fields = []
        for value in values:
            prefix = next((label for label in sorted(labels,key=len,reverse=True) if value.startswith(label+' ')), None)
            if prefix:
                fields.append({'label':labels[prefix], 'value':value[len(prefix)+1:]})
            elif value.startswith('MY27:') and fields and fields[-1]['label'] == '건조중량':
                fields[-1]['value'] += ' / '+value
        url = 'https://www.lamborghini.com/en-en/models/' + ('temerario' if model == 'Temerario' else 'revuelto-models/revuelto')
        files = [source]
        notes = ['제조사 국제 제원입니다. 연료 소비량은 접속 지역별로 달라 국내 공인 연비로 사용하지 않습니다.', '건조중량·배터리에 MY26/MY27 차이가 있어 원문을 함께 보존했습니다.']
    else:
        raise ValueError((brand, model))
    return {**{key: vehicle.get(key) for key in ('id','brand','model','trim','year','body_type','fuel')},
            'checked_on': '2026-10-28', 'display_only': True, 'source_url': url,
            'scope': '트림별 공개 제원; 국제 참조 사양과 국내 인증 사양은 각 항목·주석 참조',
            'fields': fields, 'technical_groups': groups, 'notes': notes,
            'source_files': [{'file': str(file.relative_to(ROOT)).replace('\\','/'),
                              'sha256': hashlib.sha256(file.read_bytes()).hexdigest()} for file in files]}


def main():
    catalog = read(ROOT / 'data/households/synthetic/lifestyle-million-20261028/catalog.json')
    vehicles = [v for v in catalog if v['id'].startswith(('SPORT-', 'research-'))]
    ferrari = {r['model']:r for r in read(DATA / 'ferrari-technical-tables.json')}
    roma = read(DATA / 'ferrari-roma-tables.json')[0]
    ferrari['Roma Spider'] = {'technical_groups':roma['technicalSpecificationGroups'], 'source_url':'https://www.ferrarisouthbay.com/new-vehicles/roma-spider'}
    rows = [model_details(v, ferrari) for v in vehicles]
    if len(rows) != 41 or len({(r['brand'],r['model']) for r in rows}) != 23:
        raise ValueError('New model scope changed')
    payload = {'checked_on':'2026-10-28', 'purpose':'display-only-source-backed-specifications', 'vehicles':rows}
    encoded = json.dumps(payload,ensure_ascii=False,indent=2)+'\n'
    (DATA / 'vehicle-details.json').write_text(encoded,encoding='utf-8')
    display = {**payload, 'vehicles':[{key:value for key,value in row.items() if key not in ('technical_groups','source_files')} for row in rows]}
    (ROOT / 'front/src/features/vehicle/newVehicleDetails.json').write_text(json.dumps(display,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'configurations':len(rows),'models':23,'fields':sum(len(r['fields']) for r in rows)}))


if __name__ == '__main__':
    main()
