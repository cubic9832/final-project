"""Extract numeric trim prices and certified efficiency configurations separately.

No cross-product between price trims and efficiency variants is generated.
"""

import json
import re
from pathlib import Path

ROOT = (Path(__file__).resolve().parents[3] / 'data/vehicles')
AMOUNT = r'(?:\d{1,3}(?:,\d{3}){2}|\d{1,3},\d{3}만)'
TRIMS = ['Modern','Premium','Exclusive','Inspiration','Calligraphy','Smart','H-Pick',
         'N Line','Black Exterior','Prestige','Signature','트렌디','프레스티지','시그니처',
         'GT-Line','X-Line','에어','어스','라이트','롱레인지','스탠다드','기본 모델',
         '모던','프리미엄','익스클루시브','인스퍼레이션','캘리그래피','스마트','모던 플러스',
         'LS DELUXE','Redline','ACTIV','RS','Premier','techno','iconic','esprit Alpine',
         'étoile','에뚜알','테크노','아이코닉','에스프리 알핀','에스','S','블랙','Lounge',
         '투어러','카고','프리미엄 초이스','베스트 셀렉션','트렌디','마스터즈','플래티넘',
         '노블레스','노블레스 라이트','아웃도어','그래비티','하이리무진','GT','블랙 에디션',
         '기본','스마트 초이스','에센셜','디 에센셜','슈팅 브레이크']
TRIM_RE = re.compile(r'^(?:' + '|'.join(re.escape(t) for t in sorted(TRIMS,key=len,reverse=True))
                     + r'|[A-Z]{1,3}\d(?:\s*플러스)?)(?:\s+\dWD|\s*\([^\d\n]{0,35}\))?$')


def clean(text):
    text=text.replace('\x07',' ').replace('\t',' ').replace('\u00a0',' ')
    return re.sub(r'(?<=\d)\s*\.\s*(?=\d)', '.',text)


def amount(value):
    return int(value.replace(',','').replace('만','')) * (10000 if '만' in value else 1)


def engine(text):
    text = clean(text)
    found = re.search(r'(?:가솔린|디젤|LPG|LPi|GTe|G)(?:\s*|\s*터보\s*)(\d\.\d)(?:\s*(?:터보|T-GDI|GDi|GTe|하이브리드|LET))*',text,re.I)
    if found:
        label=found.group(0).strip()
        if '하이브리드' in text[:220] and '하이브리드' not in label:
            label += ' 하이브리드'
        return label
    found=re.search(r'\d\.\d\s*(?:터보\s*)?(?:가솔린\s*(?:터보)?|하이브리드|LPG|디젤)',text)
    if found:
        return found.group(0).strip()
    found=re.search(r'(?:(\d\.\d)\s*GTe|GTe\s*(\d\.\d))',text)
    if found:
        return '가솔린 '+(found.group(1) or found.group(2))+(' 하이브리드' if '하이브리드' in text[:300] else '')
    return ''


def fuel(label, model=''):
    text=label+' '+model
    if '하이브리드' in text or 'Hybrid' in text or 'HYBRID' in text:
        return 'HYBRID'
    if any(x in text for x in ['Electric','Electrified','EV','아이오닉','일렉트릭']):
        return 'ELECTRIC'
    if '넥쏘' in text:
        return 'HYDROGEN'
    if '디젤' in text:
        return 'DIESEL'
    if any(x in text for x in ['LPG','LPi','LPI']):
        return 'LPG'
    if '가솔린' in text or 'GTe' in text or re.search(r'G\d\.\d',text):
        return 'GASOLINE'
    return ''


def source_model(default, text, brand):
    if brand=='KG모빌리티':
        header=' '.join(text.splitlines()[:5])
        if any(x in header.upper() for x in ['MUSSO','VAN']):
            return None
        for token,name in [('TORRES HYBRID','토레스 하이브리드'),('TORRES EVX','토레스 EVX'),
                           ('ACTYON HYBRID','액티언 하이브리드'),('TORRES','토레스'),('ACTYON','액티언'),
                           ('REXTON','렉스턴 뉴 아레나'),('TIVOLI','티볼리')]:
            if token in header.upper():
                return name
        return None
    if brand=='제네시스':
        header=' '.join(text.splitlines()[:7])
        found=re.search(r'GENESIS\s+([A-Za-z0-9 ]{2,45})',header,re.I)
        if found:
            name=found.group(1).split('모델')[0].strip()
            name=re.sub(r'\s+',' ',name)
            name=re.sub(r'hyb\s*rid','Hybrid',name,flags=re.I)
            compact=re.sub(r'\s+','',name.casefold())
            if 'hybrid' in compact:
                return 'GV80 Black Hybrid' if 'black' in compact else 'GV80 Hybrid'
            known=['G90 Long Wheel Base Black','G90 Long Wheel Base','GV80 Coupe Black','GV80 Coupe',
                   'Electrified G80','Electrified GV70','GV60 Magma','G80 Black','G90 Black','GV80 Black',
                   'G70 Shooting Brake','G70 Black','G70','G80','G90','GV60','GV70','GV80']
            for item in sorted(known,key=len,reverse=True):
                if compact.startswith(re.sub(r'\s+','',item.casefold())):
                    return item
    return default


def parse_prices(model, doc, pages):
    result=[]
    for page in pages:
        text=clean(page['text'])
        name=source_model(model['model'],text,model['brand'])
        if not name or ('카고' in text[:200] or '밴' in text[:130]):
            continue
        lines=[line.strip() for line in text.splitlines()]
        page_engine=engine(' '.join(lines[:7]))
        if not page_engine:
            headers=[line for line in lines if '단위' in line and any(x in line for x in ['가솔린','디젤','LPi','하이브리드'])]
            page_engine=engine(' '.join(headers))
        previous_engine=''
        previous_wheel=None
        known_trims={}
        for i,line in enumerate(lines):
            money=re.search(AMOUNT,line)
            if not money or '(' in line[money.end():] or '[' in line or '▶' in line:
                continue
            prefix=line[:money.start()].strip()
            lookback=' '.join(lines[max(0,i-5):i])
            trim=''
            if prefix and TRIM_RE.fullmatch(prefix):
                trim=prefix
            elif prefix and i and TRIM_RE.fullmatch(lines[i-1]+' '+prefix):
                trim=lines[i-1]+' '+prefix
            elif not prefix:
                # Only short label-only rows immediately before the amount qualify.
                labels=[]
                for prior in reversed(lines[max(0,i-5):i]):
                    if not prior:
                        continue
                    if re.fullmatch(r'\([^)]{1,30}\)',prior):
                        labels.insert(0,prior)
                        continue
                    if TRIM_RE.fullmatch(prior):
                        trim=prior
                    break
                if not trim:
                    # Wrapped English trim labels such as LS / DELUXE and Black / Exterior.
                    for width in [2,3,4]:
                        joined=' '.join(lines[max(0,i-width):i])
                        if TRIM_RE.fullmatch(joined):
                            trim=joined
                            break
            if not trim or not 10000000 <= amount(money.group()) <= 400000000:
                continue
            # End the price cell at the first equipment bullet/inheritance row.
            end=i+1
            while end<len(lines) and end<i+10 and not re.match(r'^[•●〮・▶]',lines[end]):
                end+=1
            cluster='\n'.join(lines[i:end])
            amounts=[]
            for cell in lines[i:end]:
                if re.search(r'\d\s*\(',cell):
                    continue  # Supply price plus VAT, never the payable price.
                amounts.extend(amount(x) for x in re.findall(AMOUNT,cell))
            before=amount(money.group())
            after=None
            tax_benefit=bool(re.search(r'세제\s*혜택\s*(?:적용\s*)?후',cluster) or
                re.search(r'세제\s*혜택\s*(?:적용\s*)?전\s*판매가격',text))
            if len(amounts)>1 and tax_benefit:
                after=amounts[-1]
            block_lines=[]
            for block_line in lines[end:min(len(lines),end+100)]:
                if (TRIM_RE.fullmatch(block_line) and block_lines) or re.match(r'^.{1,35}\s+'+AMOUNT+r'$',block_line):
                    break
                block_lines.append(block_line)
            block='\n'.join(block_lines)
            block_engine=engine((cluster+' '+block)[:900])
            powertrain=page_engine or block_engine or previous_engine
            if block_engine and not page_engine:
                previous_engine=block_engine
            exterior=re.search(r'(?:외관|외장)(?:\s*사양)?\s*[:：]\s*([^•●〮・▶]+)',block)
            exterior_text=exterior.group(1) if exterior else ''
            wheel_match=re.search(r'(\d{2})(?:인치|["”″])[^\n,.]{0,35}(?:휠|타이어)',exterior_text)
            if not wheel_match:
                wheel_match=re.search(r'R(\d{2})\s*타이어',exterior_text)
            if not wheel_match:
                exterior_note=re.search(r'※\s*[^\n]{0,50}외장\s*디자인\s*적용\s*부위([^※]{0,700})',block)
                if exterior_note:
                    wheel_match=re.search(r'R(\d{2})\s*(?:국산\s*)?타이어',exterior_note.group(1))
            wheel=int(wheel_match.group(1)) if wheel_match else None
            wheel_basis='해당 트림 외관 기본품목' if wheel else ''
            parent=re.search(r'(?m)^\s*▶?\s*([^\n]{1,35}?)\s*기본\s*품목\s*(?:및|외)',block)
            aliases={'Modern':'모던','Premium':'프리미엄','Exclusive':'익스클루시브',
                     'Inspiration':'인스퍼레이션','Smart':'스마트','Calligraphy':'캘리그래피'}
            def trim_key(label):
                label=re.sub(r'\([^)]*\)','',label).strip()
                return re.sub(r'\s+','',aliases.get(label,label))
            if not wheel and parent and not any(term in exterior_text for term in ['전용 외장','특화 외장']):
                inherited=known_trims.get(trim_key(parent.group(1)))
                if inherited:
                    wheel=inherited
                    wheel_basis='가격표의 '+parent.group(1).strip()+' 기본품목 상속'
            known_trims[trim_key(trim)]=wheel
            if wheel_match:
                previous_wheel=wheel
            if model['brand']=='제네시스' and trim=='기본 모델':
                powertrain=block_engine or powertrain
            year=re.search(r'\b(20\d{2})(?:년형|\s+[A-Z가-힣])|\b(\d{2})MY\b',text[:400])
            model_year=int(year.group(1)) if year and year.group(1) else (2000+int(year.group(2)) if year else None)
            result.append({'brand':model['brand'],'model':name,'model_year':model_year,'trim':trim,
                'powertrain':powertrain,'fuel':fuel(powertrain,name),'price_won':after if tax_benefit else before,
                'price_before_tax_benefit_won':before if tax_benefit else None,
                'price_after_tax_benefit_won':after,'price_basis':('세제혜택 후' if after else '세제혜택 후 가격 확인 필요') if tax_benefit else '표시 판매가격',
                'default_wheel_inches':wheel,'wheel_basis':wheel_basis,'source_url':doc['url'],'source_page':page['page'],
                'source_file_key':doc.get('postFileKey',''),'checked_on':'2026-10-14',
                'price_evidence':cluster,'equipment_evidence':block[:1800],
                'verification':'자동 구조 추출; 기본사양 연결 검증 대상'})
    return result


def parse_inline_efficiency(model,doc,pages):
    rows=[]
    for page in pages:
        text=clean(page['text'])
        name=source_model(model['model'],text,model['brand'])
        if model['brand']=='KG모빌리티':
            for start,end,owner in [(10,13,'렉스턴 뉴 아레나'),(14,17,'렉스턴 써밋'),(18,21,'액티언'),
                (22,25,'액티언 하이브리드'),(26,29,'토레스'),(30,33,'토레스 하이브리드'),
                (38,41,'토레스 EVX'),(46,53,'티볼리')]:
                if start<=page['page']<=end: name=owner
        if not name:
            continue
        lines=text.splitlines()
        for i,line in enumerate(lines):
            combined=re.search(r'복합(?:연비)?\s*[:：]?\s*(\d+(?:\.\d+)?)\s*km\s*/\s*([ℓLl]|kWh|kg)',line,re.I)
            city=re.search(r'도심(?:주행|연비)?\s*[:：]?\s*(\d+(?:\.\d+)?)\s*km',line)
            highway=re.search(r'고속도로(?:주행|연비)?\s*[:：]?\s*(\d+(?:\.\d+)?)\s*km',line)
            if not combined or not city or not highway:
                continue
            label=line[:combined.start()].strip()
            context=' '.join(lines[max(0,i-4):i+1])
            powertrain=engine(label) or engine(context[:220])
            unit='km/L' if combined.group(2).lower() in ['ℓ','l'] else 'km/'+combined.group(2)
            drive=re.search(r'\b(2WD|4WD|AWD|FWD|RWD)\b',label+' '+context)
            wheels=re.search(r'(\d{2}(?:\s*[/,]\s*\d{2})*)\s*(?:인치|["”″])',label)
            if model['brand']=='KG모빌리티':
                if not powertrain:
                    powertrain=engine(' '.join(lines[max(0,i-7):i]))
                if not drive:
                    drive=re.search(r'\b(2WD|4WD|AWD)\b',' '.join(lines[max(0,i-5):i]))
            cc=re.search(r'배기량\s*[:：]?\s*([\d,]+)\s*cc',line,re.I)
            weight=re.search(r'공차중량\s*[:：]?\s*([\d,]+)\s*kg',line,re.I)
            row={'brand':model['brand'],'model':name,'powertrain':powertrain,'fuel':fuel(powertrain,name),
                'configuration':label,'drive':drive.group(1) if drive else '',
                'wheel_inches':wheels.group(1).replace(' ','') if wheels else '',
                'combined_efficiency':float(combined.group(1)),'city_efficiency':float(city.group(1)),
                'highway_efficiency':float(highway.group(1)),'efficiency_unit':unit,
                'displacement_cc':int(cc.group(1).replace(',','')) if cc else None,
                'curb_weight_kg':int(weight.group(1).replace(',','')) if weight else None,
                'source_url':doc['url'],'source_page':page['page'],'checked_on':'2026-10-14',
                'evidence':line,'verification':'수치·단위 명시 원문 추출'}
            rows.append(row)
    return rows


def parse_kia_efficiency(model,doc,pages):
    rows=[]
    for page in pages:
        text=clean(page['text'])
        marker=re.search(r'정부\s*신고\s*연비',text)
        if not marker:
            continue
        table=text[marker.start():]
        table=table.split('※ 위 연비')[0]
        city_first=bool(re.search(r'도심(?:\([^)]+\))?\s*고속도로(?:\([^)]+\))?\s*복합',table[:500]))
        lines=[x.strip() for x in table.splitlines()]
        powertrain='';drive='';cc=None;seats=None
        for i,line in enumerate(lines):
            e=engine(line+' '+(' '.join(lines[i+1:i+3]) if len(line)<25 else ''))
            if e and ('인치' not in line) and len(line)<40:
                if e!=powertrain: cc=None
                powertrain=e
            d=re.search(r'\b(2WD|4WD|AWD|FWD|RWD)\b',line)
            if d: drive=d.group(1)
            s=re.search(r'(\d{1,2})인승',line)
            if s: seats=int(s.group(1))
            match=re.search(r'(\d{2}(?:\s*[/,]\s*\d{2})*)인치\s*타이어\s*(\([^)]*\))?\s+(\d+(?:\.\d+)?)\s+(\d+(?:\.\d+)?)\s+(\d+(?:\.\d+)?)',line)
            if not match:
                continue
            following=' '.join(lines[i+1:i+5])
            next_cc=re.match(r'([1-6],\d{3})\b',following)
            if next_cc and re.match(r'([1-6],\d{3})\s*(?:자동|[4-8]단|DCT|CVT)',following):
                cc=int(next_cc.group(1).replace(',',''))
            wheels=match.group(1).replace(' ','');note=match.group(2) or ''
            # Kia Niro uses city / highway / combined; other inspected price tables use combined first.
            a,b,c=map(float,match.group(3,4,5))
            combined,city,highway=(c,a,b) if city_first else (a,b,c)
            rows.append({'brand':'기아','model':model['model'],'powertrain':powertrain,'fuel':fuel(powertrain,model['model']),
                'configuration':powertrain+' '+drive+' '+(str(seats)+'인승 ' if seats else '')+wheels+'인치 '+note,'drive':drive,'wheel_inches':wheels,'seating_capacity':seats,
                'combined_efficiency':combined,'city_efficiency':city,'highway_efficiency':highway,'efficiency_unit':'km/L',
                'displacement_cc':cc,'curb_weight_kg':None,'source_url':doc['url'],'source_page':page['page'],
                'checked_on':'2026-10-14','evidence':line,'verification':'표 열 순서 반영 추출'})
    return rows


def parse_tabular_efficiency(model,doc,pages):
    rows=[]
    for page in pages:
        text=clean(page['text'])
        if not ('연비' in text and ('정부' in text or '복합' in text)):
            continue
        current_model=model['model'];powertrain='';drive=''
        for line in text.splitlines():
            line=line.strip()
            if model['brand']=='제네시스' and re.fullmatch(r'(?:G\d{2}|GV\d{2})(?:\s*Black)?',line):
                current_model=line
            e=engine(line)
            if e and len(line)<65:
                powertrain=e
            if 'hybrid E-Tech' in line:
                powertrain='하이브리드 E-Tech'
            d=re.search(r'\b(2WD|4WD|AWD)\b',line)
            if d: drive=d.group(1)
            if model['brand']=='제네시스':
                # Paired slash values are deliberately omitted until each subvariant is split.
                if '/' in line: continue
                match=re.search(r'^(\d{2})[″”"]\s+([\d,]+)\s+자동\s*\d단\s+\d\s+\d{2,3}\s+(\d+\.\d+)\s+(\d+\.\d+)\s+(\d+\.\d+)\s*$',line)
                if not match: continue
                wheel,weight,city,highway,combined=match.groups()
                cc=None
            else:
                match=re.search(r'(.+?)\s+(\d+\.\d+)\s+(\d+\.\d+)\s+(\d+\.\d+)\s+\d{2,3}\s+([\d,]+)\s+([\d,]+)\s+',line)
                if not match: continue
                label,combined,city,highway,cc,weight=match.groups()
                wm=re.search(r'(\d{2}(?:[/]\d{2})*)["”″]',label)
                wheel=wm.group(1) if wm else ''
            rows.append({'brand':model['brand'],'model':current_model,'powertrain':powertrain,
                'fuel':fuel(powertrain,current_model),'configuration':powertrain+' '+drive+' '+wheel+'인치',
                'drive':drive,'wheel_inches':wheel,'combined_efficiency':float(combined),
                'city_efficiency':float(city),'highway_efficiency':float(highway),'efficiency_unit':'km/L',
                'displacement_cc':int(cc.replace(',','')) if cc else None,
                'curb_weight_kg':int(weight.replace(',','')),
                'source_url':doc['url'],'source_page':page['page'],'checked_on':'2026-10-14',
                'evidence':line,'verification':'표 열 순서 반영 추출; 다중값 행 제외'})
    return rows


def parse_kia_electric(model,doc,pages):
    rows=[]
    for page in pages:
        text=clean(page['text'])
        if '정부 신고 에너지' not in text or 'km/kWh' not in text: continue
        table=text.split('정부 신고 에너지',1)[1].split('※ 위 에너지')[0]
        variant='';drive=''
        for line in table.splitlines():
            line=line.strip()
            if '스탠다드' in line: variant='스탠다드'
            elif re.search(r'롱\s*레인지',line): variant='롱레인지'
            d=re.search(r'\b(2WD|4WD|AWD)\b',line)
            if d: drive=d.group(1)
            m=re.search(r'(\d{2})인치(?:\s*타이어)?\s*(\([^)]*\))?\s+(\d{3})\s+(\d{3})\s+(\d{3})\s+(\d\.\d)\s+(\d\.\d)\s+(\d\.\d)',line)
            if not m: continue
            wheel,note,range_combined,range_city,range_highway,combined,city,highway=m.groups()
            rows.append({'brand':'기아','model':model['model'],'powertrain':variant,'fuel':'ELECTRIC',
                'configuration':variant+' '+drive+' '+wheel+'인치 '+(note or ''),'drive':drive,'wheel_inches':wheel,
                'combined_efficiency':float(combined),'city_efficiency':float(city),'highway_efficiency':float(highway),
                'efficiency_unit':'km/kWh','range_combined_km':int(range_combined),'range_city_km':int(range_city),
                'range_highway_km':int(range_highway),'displacement_cc':None,'curb_weight_kg':None,
                'source_url':doc['url'],'source_page':page['page'],'checked_on':'2026-10-14',
                'evidence':line,'verification':'표 열 순서 반영 추출'})
    return rows


def powertrain_key(label):
    size=re.search(r'(\d\.\d)',label)
    return (size.group(1) if size else '', '터보' in label or 'T-GDI' in label, '하이브리드' in label)


def join_details(prices,efficiency):
    rows=[]
    for price in prices:
        row=dict(price)
        candidates=[]
        if price['default_wheel_inches'] and price['powertrain']:
            for spec in efficiency:
                if spec['brand']!=price['brand'] or spec['model']!=price['model'] or spec['fuel']!=price['fuel']: continue
                if powertrain_key(spec['powertrain'])!=powertrain_key(price['powertrain']): continue
                if str(price['default_wheel_inches']) not in re.findall(r'\d{2}',str(spec['wheel_inches'])): continue
                if any(term in spec['configuration'] for term in ['빌트인 캠','밴','스포츠 패키지']): continue
                if spec.get('seating_capacity') and spec['seating_capacity']!=price.get('seating_capacity'): continue
                candidates.append(spec)
        if len(candidates)==1:
            spec=candidates[0]
            for key in ['drive','combined_efficiency','city_efficiency','highway_efficiency','efficiency_unit',
                        'displacement_cc','curb_weight_kg','range_combined_km']:
                row[key]=spec.get(key)
            row['efficiency_source_url']=spec['source_url'];row['efficiency_source_page']=spec['source_page']
            row['join_status']='엔진·연료·기본 휠 조건에서 연비 사양 1건 연결'
        else:
            row['join_status']='연결 보류: 기본 휠·엔진 또는 연비 사양 확인 필요' if not candidates else '연결 보류: 구동 방식 등 복수 사양 존재'
        rows.append(row)
    return rows


def main():
    models=json.loads((ROOT/'official-model-manifest.json').read_text(encoding='utf-8'))['models']
    prices=[];efficiency=[];seen_docs=set()
    for model in models:
        for doc in model['documents']:
            if doc.get('status')!='extracted' or doc['kind'] not in ['price','shared-price']:
                continue
            key=doc['extractedPath']
            if key in seen_docs: continue
            seen_docs.add(key)
            pages=json.loads((ROOT/key).read_text(encoding='utf-8')).get('pages',[])
            prices.extend(parse_prices(model,doc,pages))
            efficiency.extend(parse_inline_efficiency(model,doc,pages))
            if model['brand']=='기아':
                efficiency.extend(parse_kia_efficiency(model,doc,pages))
                efficiency.extend(parse_kia_electric(model,doc,pages))
            if model['brand'] in ['제네시스','르노코리아']:
                efficiency.extend(parse_tabular_efficiency(model,doc,pages))
    # Deduplicate copied source variants, retaining the first documented occurrence.
    unique_prices={}
    for row in prices:
        key=tuple(row[k] for k in ['brand','model','model_year','trim','powertrain','price_won'])
        unique_prices.setdefault(key,row)
    unique_efficiency={};rejected_efficiency=[]
    for row in efficiency:
        combined,city,highway=(row[k] for k in ['combined_efficiency','city_efficiency','highway_efficiency'])
        if not (0<min(combined,city,highway) and min(city,highway)<=combined<=max(city,highway)):
            rejected_efficiency.append({**row,'rejection_reason':'연비 열 배치 또는 병합 셀 재확인 필요'})
            continue
        key=tuple(row[k] for k in ['brand','model','powertrain','configuration','combined_efficiency','efficiency_unit'])
        unique_efficiency.setdefault(key,row)
    prices=list(unique_prices.values());efficiency=list(unique_efficiency.values())
    result={'trim_prices':prices,'efficiency_configurations':efficiency,'vehicle_details':join_details(prices,efficiency),
            'rejected_efficiency_rows':rejected_efficiency}
    (ROOT/'normalized-vehicle-details.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps({k:len(v) for k,v in result.items()}))


if __name__=='__main__':
    main()
