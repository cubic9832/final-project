"""Join archived official evidence without guessing unspecified configurations."""
import hashlib
import json
import re
import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / 'ml'))
from vehicle_matching.api import load_service
from reviewed_specifications import reviewed_specifications


def build():
    service = load_service(ROOT / 'ml/experiments/candidate-v2', apply_specification_updates=False)
    normalized = json.loads((ROOT/'data/vehicles/normalized-vehicle-details.json').read_text(encoding='utf-8'))
    manifest = json.loads((ROOT/'data/vehicles/official-model-manifest.json').read_text(encoding='utf-8'))
    manifest = {(r['brand'],r['model']):r for r in manifest['models']}
    identities = {}
    for r in normalized['trim_prices']:
        parts = [r['brand'],r['model'],str(r.get('model_year') or ''),r['trim'],r['powertrain'],str(r.get('default_wheel_inches') or '')]
        vid = 'V-' + hashlib.sha256(json.dumps(parts,ensure_ascii=False).encode()).hexdigest()[:16]
        identities[vid] = r
    # Manually reviewed dimension-table values, not model-name size assumptions.
    dimensions = {'K5':(4905,15),'K8':(5050,15),'K9':(5140,18),'셀토스':(4430,28),
                  '쏘렌토':(4815,29),'카니발':(5155,14),'카니발 하이리무진':(5155,10),
                  'EV3':(4300,16),'EV3 GT':(4310,4),'EV4':(4730,13),'EV4 GT':(4730,4),
                  'EV6':(4695,11),'EV6 GT':(4695,4),'EV9':(5010,20),'EV9 GT':(5015,4)}
    kgm = {'렉스턴 뉴 아레나':(4850,56),'액티언':(4740,57),'액티언 하이브리드':(4740,57),
           '토레스':(4705,58),'토레스 하이브리드':(4705,57),'토레스 EVX':(4715,58),'티볼리':(4255,59)}
    imported=json.loads((ROOT/'data/vehicles/quality-imported-length-evidence.json').read_text(encoding='utf-8'))['vehicles']
    rows=[]
    for v in service.vehicles:
        updates={};evidence=[]
        # Drop preliminary automatic matches using built-in camera variants.
        if any(e.get('field')=='efficiency' and any('빌트인' in c.get('configuration','') for c in e.get('variants',[])) for e in evidence):
            updates.pop('efficiency',None); evidence=[e for e in evidence if e.get('field')!='efficiency']
        if v.efficiency is None:
            updates.pop('efficiency', None)
            evidence=[e for e in evidence if e.get('field')!='efficiency']
        r=identities.get(v.id)
        configs=[]
        if r:
            for c in normalized['efficiency_configurations']:
                if (c['brand'],c['model'],c['fuel']) != (v.brand,v.model,v.fuel):continue
                if c['efficiency_unit'] != ('km/kWh' if v.fuel=='ELECTRIC' else 'km/L'):continue
                # Do not infer engine identity from a fuel or model name alone.
                engine_a=re.search(r'\d\.\d',r['powertrain'])
                engine_b=re.search(r'\d\.\d',c['powertrain'])
                if engine_a and (not engine_b or engine_a.group()!=engine_b.group()):continue
                if not r.get('default_wheel_inches') or str(r['default_wheel_inches'])!=c['wheel_inches']:continue
                if v.fuel=='ELECTRIC' and r['powertrain'] and r['powertrain'] not in c['powertrain']:continue
                # Only join within the exact price source, avoiding another year's catalog.
                if c['source_url'] != r['source_url']:continue
                if '빌트인' in c['configuration']:continue
                configs.append(c)
            values={c['combined_efficiency'] for c in configs}
            if v.efficiency is None and len(values)==1:
                updates['efficiency']=next(iter(values))
                evidence.append({'field':'efficiency','source_url':configs[0]['source_url'],'source_page':configs[0]['source_page'],
                                 'basis':'exact engine, fuel, default wheel, source; all matched variants have identical efficiency',
                                 'variants':configs})
        # New official HTML rows keep tire/engine conditions in the same record.
        slug_map={'K5':'k5','K8':'k8','K9':'k9','셀토스':'seltos','스포티지':'sportage','쏘렌토':'sorento',
                  '카니발':'carnival','카니발 하이리무진':'carnival-hi-limousine','모닝':'morning','레이':'ray','니로':'niro'}
        slug=slug_map.get(v.model, v.model.lower().replace(' ','-') if v.model.startswith('EV') else '')
        html_path=ROOT/'data/vehicles/sources/specification-pages-20261022'/f'{slug}.json'
        html_matches=[]
        if v.brand=='기아' and html_path.is_file():
            page_data=json.loads(html_path.read_text(encoding='utf-8'))
            for parts in page_data.get('efficiency_rows',[]):
                label=parts[0]
                fuel='ELECTRIC' if 'km/kWh' in ' '.join(parts) else 'HYBRID' if '하이브리드' in label else 'LPG' if any(t in label for t in ('LPG','LPI','LPi')) else 'DIESEL' if '디젤' in label else 'GASOLINE'
                if fuel!=v.fuel:continue
                match=re.search(r'복합\s*:\s*(\d+(?:\.\d+)?)',' '.join(parts[1:2]))
                if not match:continue
                if ('빌트인' in label and '미적용' not in label):continue
                if r:
                    a=re.search(r'\d\.\d',r['powertrain']);b=re.search(r'\d\.\d',label)
                    if a and (not b or a.group()!=b.group()):continue
                    wheel=re.search(r'(\d{2})인치',label)
                    if r.get('default_wheel_inches') and (not wheel or int(wheel.group(1))!=r['default_wheel_inches']):continue
                    if v.fuel=='ELECTRIC':
                        battery=next((b for b in ('스탠다드','롱레인지') if b in r['powertrain'] or b in v.trim),None)
                        if battery and battery not in label:continue
                html_matches.append({'configuration':label,'combined_efficiency':float(match.group(1)),
                                     'source_url':page_data['source_url'],'evidence':parts})
            values={x['combined_efficiency'] for x in html_matches}
            if v.efficiency is None and len(values)==1:
                updates['efficiency']=next(iter(values))
                evidence=[e for e in evidence if e['field']!='efficiency']
                evidence.append({'field':'efficiency','basis':'official HTML, fuel/engine/default-wheel matches with identical values',
                                 'source_url':page_data['source_url'],'variants':html_matches})
        if v.efficiency is None and 'efficiency' not in updates:
            options=html_matches[:]
            if not options:
                for c in normalized['efficiency_configurations']:
                    if (c['brand'],c['model'])!=(v.brand,v.model):continue
                    if c['fuel'] != v.fuel:
                        model_fuels={x.fuel for x in service.vehicles if (x.brand,x.model)==(v.brand,v.model)}
                        if c['fuel'] or model_fuels!={v.fuel}:continue
                    if c['efficiency_unit']!=('km/kWh' if v.fuel=='ELECTRIC' else 'km/L'):continue
                    if r:
                        a=re.search(r'\d\.\d',r['powertrain']);b=re.search(r'\d\.\d',c['powertrain'])
                        if a and b and a.group()!=b.group():continue
                        if a and not b and (not c.get('displacement_cc') or abs(float(a.group())-c['displacement_cc']/1000)>.06):continue
                        wheel_values=re.findall(r'\d{2}',str(c['wheel_inches']))
                        wheel_values += re.findall(r'(\d{2})\s*(?:[\"″]|인치)',c.get('evidence',''))
                        if r.get('default_wheel_inches') and wheel_values and str(r['default_wheel_inches']) not in wheel_values:continue
                    if '빌트인' in c['configuration'] or '스포츠 패키지' in c['configuration'] or '밴' in c['configuration']:continue
                    if v.fuel=='HYBRID' and not any(t in c['powertrain']+' '+c['configuration'] for t in ('하이브리드','HEV','Hybrid')):continue
                    options.append(c)
            def default_key(c):
                label=c['configuration']
                wheel=re.search(r'(\d{2})(?:인치|[\"″])',label)
                return ('4WD' in label or 'AWD' in label, '롱레인지' in label,
                        int(wheel.group(1)) if wheel else 99, label)
            if options:
                selected=min(options,key=default_key)
                updates['efficiency']=selected['combined_efficiency']
                evidence.append({'field':'efficiency','source_url':selected['source_url'],
                                 'basis':'user-authorized explicit default configuration; prefer base drive and basic wheel, no paid camera/sport options',
                                 'selected_configuration':selected['configuration'],'variants':options})
        item=manifest.get((v.brand,v.model))
        if item is None and v.model in ('GV80 Hybrid','GV80 Black Hybrid'):item=manifest.get(('제네시스','GV80'))
        dim=dimensions.get(v.model) if v.brand=='기아' else kgm.get(v.model) if v.brand=='KG모빌리티' else None
        if v.length_mm is None and dim and item:
            length,page=dim
            if v.model=='EV3' and 'GT-Line' in v.trim:length=4310
            docs=[d for d in item['documents'] if d.get('extractedPath') and (v.brand=='KG모빌리티' or d['kind']=='catalog')]
            for doc in docs:
                pages=json.loads((ROOT/'data/vehicles'/doc['extractedPath']).read_text(encoding='utf-8'))['pages']
                text=next((p['text'] for p in pages if p['page']==page),'')
                if f'{length:,}' not in text or not re.search(r'전\s*장',text):continue
                updates.update(length_mm=length,space_source_url=doc['url'])
                evidence.append({'field':'length_mm','source_url':doc['url'],'source_page':page,'extracted_path':doc['extractedPath'],
                                 'basis':'model-specific dimension-table column reviewed','value':length})
                break
        if v.length_mm is None and 'length_mm' not in updates:
            ref=next((x for x in imported if (x['brand'],x['model'])==(v.brand,v.model)),None)
            if ref:
                updates.update(length_mm=ref['length_mm'],space_source_url=ref['source_url'])
                evidence.append({'field':'length_mm','source_url':ref['source_url'],'quote':ref['quote'],
                                 'scope':ref['scope'],'basis':'manufacturer body reference, not Korean trim certification'})
        # Genesis price documents explicitly distinguish SUV and coupe dimensions.
        if v.length_mm is None and v.brand=='제네시스' and item and v.model in ('G70','G70 Shooting Brake','GV80','GV80 Coupe'):
            length=4685 if v.model.startswith('G70') else 4965 if v.model=='GV80 Coupe' else 4950
            for doc in item['documents']:
                if doc['kind']!='price' or not doc.get('extractedPath'):continue
                pages=json.loads((ROOT/'data/vehicles'/doc['extractedPath']).read_text(encoding='utf-8'))['pages']
                for page in pages:
                    if re.search(r'전\s*장',page['text']) and f'{length:,}' in page['text']:
                        updates.update(length_mm=length,space_source_url=doc['url'])
                        evidence.append({'field':'length_mm','source_url':doc['url'],'source_page':page['page'],
                                         'basis':'model-specific price-document dimension table'})
                        break
        if v.length_mm is None and v.brand=='르노코리아' and v.model in ('아르카나','필랑트') and item:
            length=4570 if v.model=='아르카나' else 4915
            for doc in item['documents']:
                if doc['kind']!='price' or not doc.get('extractedPath'):continue
                pages=json.loads((ROOT/'data/vehicles'/doc['extractedPath']).read_text(encoding='utf-8'))['pages']
                page=next((p for p in pages if re.search(r'전장\s*\(mm\)\s*'+f'{length:,}',p['text'])),None)
                if page:
                    updates.update(length_mm=length,space_source_url=doc['url'])
                    evidence.append({'field':'length_mm','source_url':doc['url'],'source_page':page['page'],
                                     'basis':'model-specific dimension table'})
        # Reviewed base configurations in the archived official price documents.
        manual = {
            'Electrified G80':(4.4,'AWD 19인치',6), 'Electrified GV70':(4.5,'AWD 19인치',6),
            'GV70':(9.8,'가솔린 2.5 터보 2WD 19인치',6),
            'GV80 Coupe':(8.2,'가솔린 2.5 터보 AWD 5인승 20인치',7),
            'G80 Black':(9.4,'가솔린 2.5 터보 AWD 20인치',7),
            'G90 Long Wheel Base':(8.2,'가솔린 3.5 터보 48V AWD 20인치',10),
            'G90 Long Wheel Base Black':(8.2,'가솔린 3.5 터보 48V AWD 20인치',10),
            '토레스 EVX':(4.7,'2WD 18인치 승용',39),
            'GV80 Hybrid':(11.6,'가솔린 2.5 터보 하이브리드 2WD 5인승 19인치 일반타이어',11),
            'GV80 Black Hybrid':(10.5,'가솔린 2.5 터보 하이브리드 AWD 5인승 22인치',11),
            '더 뉴 스타리아 Electric':(3.9,'투어러 11인승 17인치',2),
            '더 뉴 스타리아 라운지 Electric':(3.9,'라운지 7인승 17인치',3),
            '더 뉴 스타리아 리무진 Electric':(3.9,'리무진 6인승 17인치',3),
            '더 뉴 아이오닉 6':(6.3,'Standard 2WD 18인치',4),
        }
        if v.efficiency is None and v.model in manual:
            efficiency, configuration, source_page=manual[v.model]
            document=next((doc for doc in (item or {}).get('documents',[]) if doc['kind'] in ('price','shared-price') and doc.get('extractedPath')),None)
            if document:
                updates['efficiency']=efficiency
                evidence=[e for e in evidence if e['field']!='efficiency']
                evidence.append({'field':'efficiency','source_url':document['url'],'source_page':source_page,
                                 'extracted_path':document['extractedPath'],'selected_configuration':configuration,
                                 'basis':'user-authorized explicit base configuration; manually reviewed official table'})
        if v.efficiency is None and v.brand=='BMW' and v.model=='5시리즈':
            efficiency=14.7 if v.trim.startswith('523d') and 'xDrive' not in v.trim else 12.1 if v.trim.startswith('520i') else None
            if efficiency:
                updates['efficiency']=efficiency
                evidence.append({'field':'efficiency','source_url':'https://www.bmw.co.kr/content/bmw/marketKR/bmw_co_kr/ko/all-models/5-series/sedan/bmw-5-series-sedan-overview.html',
                                 'basis':'official model-specific Korean fuel-economy FAQ, base configuration','selected_configuration':v.trim})
        if v.model=='캐스퍼 일렉트릭':
            url='https://casper.hyundai.com/vehicles/electric/spec'
            updates.update(length_mm=3845 if v.trim=='크로스' else 3825,space_source_url=url)
            evidence.append({'field':'length_mm','source_url':url,'basis':'current dimension table; Cross length distinguished'})
            if v.trim in ('프리미엄','인스퍼레이션','크로스'):
                updates['efficiency']={'프리미엄':5.8,'인스퍼레이션':5.6,'크로스':5.1}[v.trim]
                evidence.append({'field':'efficiency','source_url':url,'basis':'base battery, standard wheel, no optional roof basket',
                                 'selected_configuration':{'프리미엄':'42kWh 15인치','인스퍼레이션':'49kWh 15인치','크로스':'49kWh 17인치 루프바스켓 미적용'}[v.trim]})
        if v.efficiency is None and v.model=='코나 Electric' and item:
            wheel=r.get('default_wheel_inches') if r else None
            efficiency=4.7 if v.trim=='N Line' else 4.8 if wheel==19 else 5.5
            updates['efficiency']=efficiency
            doc=next(d for d in item['documents'] if d['kind']=='price')
            evidence.append({'field':'efficiency','source_url':doc['url'],'source_page':4,'extracted_path':doc['extractedPath'],
                             'selected_configuration':('Long Range N Line 19인치' if v.trim=='N Line' else 'Long Range 19인치' if wheel==19 else 'Standard/Long Range 17인치'),
                             'basis':'official table, basic drive; 17-inch battery variants share efficiency'})
        if v.efficiency is None and v.model=='아이오닉 5' and item:
            updates['efficiency']=4.7 if v.trim=='N Line' else 5.1
            doc=next(d for d in item['documents'] if d['kind']=='price')
            evidence.append({'field':'efficiency','source_url':doc['url'],'source_page':4,'extracted_path':doc['extractedPath'],
                             'selected_configuration':'N Line 2WD 20인치 빌트인 캠' if v.trim=='N Line' else 'Standard 2WD 19인치',
                             'basis':'user-authorized base drive/battery configuration; maker-certified table'})
        if v.efficiency is None and v.model=='G70' and r and '3.3' in r['powertrain']:
            updates['efficiency']=9.1
            doc=next(d for d in item['documents'] if d['kind']=='price')
            evidence.append({'field':'efficiency','source_url':doc['url'],'source_page':7,'extracted_path':doc['extractedPath'],
                             'selected_configuration':'가솔린 3.3 터보 2WD 19인치 올시즌','basis':'official engine-specific table'})
        if v.efficiency is None and v.model=='Model Y':
            updates['efficiency']=5.4 if 'Long Range' in v.trim else 5.6
            evidence.append({'field':'efficiency','source_url':'https://www.tesla.com/ko_kr/support/range-calculator-ref',
                             'selected_configuration':v.trim,'basis':'Korean certified consumption table, Premium 5-seat versions'})
        if v.efficiency is None and v.model=='E-Class' and v.trim=='E 200 EXCLUSIVE':
            updates.update(efficiency=12.3,length_mm=4955,space_source_url='https://www.mercedes-benz.co.kr/passengercars/brand/news-events/news-story/2026/news-20260424.html')
            evidence.append({'field':'efficiency','source_url':updates['space_source_url'],'basis':'2026 Korean exact-trim launch specifications'})
            evidence.append({'field':'length_mm','source_url':updates['space_source_url'],'basis':'Korean exact-trim body length supersedes overseas body reference'})
        reviewed, reviewed_evidence, corrections = reviewed_specifications(v)
        for key,value in reviewed.items():
            if getattr(v,key) is None or key in corrections or key in ('source_note','original_fuel') or (key=='seat_options' and not v.seat_options):
                updates[key]=value
                evidence=[entry for entry in evidence if entry['field']!=key]
                evidence.extend(entry for entry in reviewed_evidence if entry['field']==key)
        # Public Korean Energy Agency registrations retain certification identity.
        query_key={'3시리즈':'320d','3시리즈 투어링':'320d','X5':'x5','X1':'x1','X4':'x4',
                   'K5':'k5','쏘렌토':'sorento'}.get(v.model)
        if query_key and v.efficiency is None:
            agency_path=ROOT/'data/vehicles/sources/specification-pages-20261022'/f'kea-{query_key}.json'
            agency=json.loads(agency_path.read_text(encoding='utf-8'))
            candidates=[]
            for entry in agency['rows']:
                name=entry['MODL_NM']
                if v.brand=='BMW':
                    target={'3시리즈':'BMW 320d','3시리즈 투어링':'BMW 320d Touring','X1':'BMW X1 sDrive18d','X4':'BMW X4 xDrive20d'}.get(v.model)
                    if v.model=='X5':
                        if not name.startswith('BMW X5 xDrive30d') or entry['MAN_NUMB']!=7:continue
                    elif name!=target:continue
                elif v.model=='K5':
                    if v.fuel!='LPG' or entry['FUEL_KIND_CD']!='2' or 'PE' not in name:continue
                    wheel=r.get('default_wheel_inches') if r else (18 if v.trim=='시그니처' else 16 if v.trim=='트렌디' else 17)
                    if f'{wheel}인치' not in name:continue
                elif v.model=='쏘렌토':
                    if v.fuel!='HYBRID' or not all(t in name for t in ('HEV','PE','2WD','5인','19인치','통합')):continue
                candidates.append(entry)
            if candidates:
                entry=max(candidates,key=lambda c:(c['INJUNG_DT'] or '',c['RECP_NO']))
                updates['efficiency']=entry['TOTAL_MILEAGE']
                evidence=[e for e in evidence if e['field']!='efficiency']
                configuration=f"{entry['MODL_NM']} / {entry['RUN_GB_NM']} / {entry['MAN_NUMB']}인승 / {entry['FRONT_TIRE_SIZE'] or '인증 모델명 참조'}"
                evidence.append({'field':'efficiency','source_url':agency['source_url'],
                                 'selected_configuration':configuration,'registration_id':entry['RECP_NO'],
                                 'certified_on':entry['INJUNG_DT'],'source_file':str(agency_path.relative_to(ROOT)),
                                 'basis':'latest matching public Korean certification; explicit base configuration',
                                 'registration':entry})
                if v.seats is None and not v.seat_options:
                    updates.update(seats=entry['MAN_NUMB'],seat_options=[entry['MAN_NUMB']],
                                   seats_source_url=agency['source_url'],seats_status='official-reference')
                reference_only=(v.model=='K5' and '빌트인캠' in entry['MODL_NM']) or (v.model=='X4' and 'M 스포츠' in v.trim)
                if reference_only:
                    updates['efficiency_reference_only']=True
                    updates['source_note']='기본 사양의 정확한 인증값 미확정: '+configuration+' 인증값을 유지비 비교용 참조값으로 사용. 선택품목 장착·가격 포함을 의미하지 않음.'
                    if v.source_note is not None:corrections['source_note']=v.source_note
        efficiency_evidence=next((e for e in reversed(evidence) if e['field']=='efficiency'),None)
        if efficiency_evidence:
            configuration=efficiency_evidence.get('selected_configuration')
            if not configuration:
                variants=efficiency_evidence.get('variants',[])
                configuration=' / '.join(dict.fromkeys(c['configuration'] for c in variants)) or None
            if configuration:updates['default_configuration']=configuration
        rows.append({'id':v.id,'brand':v.brand,'model':v.model,'trim':v.trim,'price':v.price,'fuel':v.fuel,
                     'corrections':corrections,
                     'updates':updates,'evidence':evidence,'matching_efficiency_variants':html_matches or configs,
                     'unresolved': [key for key in ('efficiency','length_mm','seats') if getattr(v,key) is None and key not in updates and not (key=='seats' and v.seat_options)]})
    output=ROOT/'data/vehicles/candidate-specifications-v1.json'
    output.write_text(json.dumps({'checked_on':'2026-10-22','vehicles':rows},ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps({'records':len(rows),'updated':sum(bool(r['updates']) for r in rows),
                      'efficiency_added':sum('efficiency' in r['updates'] for r in rows),
                      'length_added':sum('length_mm' in r['updates'] for r in rows)},ensure_ascii=False))

if __name__=='__main__':build()
