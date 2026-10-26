"""Reviewed manufacturer facts that need model/trim-specific joins."""


def reviewed_specifications(vehicle):
    model, trim = vehicle.model, vehicle.trim
    updates, evidence, corrections = {}, [], {}

    def add(values, url, configuration, note, **extra):
        updates.update(values)
        for field in values:
            evidence.append(dict(field=field, source_url=url,
                                 selected_configuration=configuration, basis=note, **extra))

    if model == 'ES':
        add({'efficiency':18.3 if 'AWD' in trim else 19.4},
            'https://www.lexus.co.kr/models/ES-350h/', trim+' 235/55R19',
            'Korean manufacturer model-page specification data; FWD and AWD distinguished',
            source_asset='https://www.lexus.co.kr/libs/1.0.0-20261021091558-3e1e05b5/model.es350h.detail.data.js?v=1.0.0-20261021091558-3e1e05b5')
    if model == 'XC60':
        add({'efficiency':11.7 if trim.startswith('T8') else 10.7},
            'https://www.volvocar.co.kr/l/volvo-brochure/pdf/MY26-XC60.pdf?ver=20251208',
            trim+(' 20인치' if 'Ultra' in trim else ' 19인치'),
            'MY26 Korean brochure; T8 uses certified gasoline consumption only, electric savings not assumed',
            source_page=9 if trim.startswith('T8') else 6 if 'Ultra' in trim else 3)
        if trim.startswith('T8'):
            add({'fuel':'HYBRID','original_fuel':'PHEV',
                 'source_note':'PHEV; gasoline-mode 11.7 km/L; certified electric mode 3.5 km/kWh. Charging savings excluded.'},
                evidence[-1]['source_url'],trim,'Official electric/gasoline powertrain; repair gasoline-only classification')
            corrections['fuel']='GASOLINE'
            if vehicle.source_note is not None:
                corrections['source_note']=vehicle.source_note
    if vehicle.brand == 'BMW' and model == '5시리즈' and trim.startswith('530i'):
        add({'efficiency':11.1},
            'https://www.bmw.co.kr/content/bmw/marketKR/bmw_co_kr/ko/all-models/5-series/sedan/bmw-5-series-sedan-overview.html',
            '530i xDrive G60','Current Korean manufacturer model-specific fuel-economy FAQ')
    if vehicle.brand == 'BMW' and model == 'X3':
        url='https://www.bmw.co.kr/ko/all-models/x-series/x3/bmw-x3.html'
        value=10.9
        if '20d' in trim:
            value=14.0
            url='https://www.press.bmwgroup.com/korea/article/detail/T0446603KO/bmw-코리아-4세대-완전변경-bmw-뉴-x3’-공식-출시'
        elif '30 ' in trim:
            url='https://www.press.bmwgroup.com/korea/article/detail/T0453922KO/bmw-코리아-강력한-성능과-첨단-사양-갖춘-뉴-x3-30-xdrive-m-스포츠-패키지-프로’-출시'
        add({'efficiency':value,'seats':5,'seat_options':[5],
             'seats_source_url':url,'seats_status':'official-reference'},url,
            trim+' G45','Korean official launch/model specifications; diesel and gasoline separated')
    if vehicle.brand == 'BMW' and model == 'X1':
        url='https://www.press.bmwgroup.com/korea/article/detail/T0412647KO/bmw-코리아-프리미엄-소형-sav-뉴-x1-및-뉴-ix1-공식-출시?language=ko'
        add({'efficiency':14.6,'length_mm':4500,'space_source_url':url},url,
            'U11 sDrive18d 18인치 전륜구동',
            '2023 Korean launch basic-configuration reference; catalog model year unspecified',
            reference_year=2023)
    if vehicle.brand == 'BMW' and model == 'X4':
        url='https://www.press.bmwgroup.com/korea/article/detail/T0354632KO/bmw-코리아-뉴-x3-및-뉴-x4-국내-공식-출시'
        add({'efficiency':12.3,'length_mm':4750,'space_source_url':url},url,
            'G02 xDrive20d','Korean G02 facelift launch configuration reference; not a new 2026 certification',
            reference_year=2021)
    if vehicle.brand == 'BMW' and model in ('3시리즈','3시리즈 투어링'):
        url='https://www.press.bmwgroup.com/united-kingdom/article/attachment/T0442576EN_GB/624814'
        add({'length_mm':4713,'space_source_url':url,'seats':5,'seat_options':[5],
             'seats_source_url':url,'seats_status':'official-body-reference'},url,
            'G21 320d Touring' if '투어링' in model else 'G20 320d',
            '2024 manufacturer same-generation international body/seating reference; not Korean efficiency evidence',reference_year=2024)
    if vehicle.brand == 'BMW' and model=='X5':
        url='https://www.bmw.co.il/content/dam/bmw/marketIL/bmw_co_il/all_models/bmw-x5-g05/39251_Mifrat_BMW_X5.pdf.asset.1752060008798.pdf'
        add({'length_mm':4935,'space_source_url':url},url,'G05 LCI xDrive30d 7인승',
            '2025 manufacturer same-generation body reference; foreign fuel test values not imported')
    seating_sources={
        'X1':'https://www.bmwusa.com/vehicles/x-models.html',
        '5시리즈':'https://www.press.bmwgroup.com/usa/article/attachment/T0418778EN_US/624323',
        'X4':'https://www.bmw.co.id/content/dam/bmw/marketID/bmw_co_id/Brochures/G02-LCI_Spec-card_NEW-X4-230224.pdf.asset.1677757906906.pdf',
    }
    if vehicle.brand=='BMW' and model in seating_sources:
        url=seating_sources[model]
        add({'seats':5,'seat_options':[5],'seats_source_url':url,'seats_status':'official-body-reference'},
            url,model+' 5인승','Manufacturer same-generation body seating reference; foreign efficiency not imported')
    if model == '캐스퍼':
        url='https://casper.hyundai.com/wcontents/repn-car/catalog/AX06/AX_CASPER_price.pdf'
        add({'efficiency':13.8 if trim=='인스퍼레이션' else 14.3,'length_mm':3595,
             'space_source_url':url,'seats':4,'seat_options':[4],
             'seats_source_url':'https://www.hyundaimotorgroup.com/ko/amp/CONT0000000000002519',
             'seats_status':'official-reference'},url,
            '가솔린 1.0 자연흡기 4단 자동 '+('17인치' if trim=='인스퍼레이션' else '15인치'),
            'Manufacturer same-generation basic engine/wheel reference; original 2027 price preserved',
            source_page=4, reference_scope='same-generation configuration, not 2027 price evidence')
    if model == '캐스퍼 일렉트릭':
        url='https://casper.hyundai.com/vehicles/electric/spec'
        add({'seats':4,'seat_options':[4],'seats_status':'official-reference',
             'seats_source_url':'https://certified.hyundai.com/p/goods/goodsDetail.do?goodsNo=HAX260908032019'},
            'https://certified.hyundai.com/p/goods/goodsDetail.do?goodsNo=HAX260908032019',
            '캐스퍼 일렉트릭 4인승','Manufacturer certified-used same-generation body seating reference')
        if trim=='라운지':
            add({'efficiency':5.2},url,'49kWh 17인치 라운지, 루프 바스켓 미적용',
                'Official efficiency table plus Lounge standard 17-inch equipment',
                equipment_source='https://casper.hyundai.com/wcontents/repn-car/catalog/AX05/AX_CASPER_Electric_price.pdf')
    if model in ('GV80 Hybrid','GV80 Black Hybrid'):
        url='https://www.genesis.com/wsvc/kr/api/v2/download-center/pdfview'
        add({'length_mm':4950,'space_source_url':url},url,model+' SUV',
            'Model-specific official price-document dimension table',source_page=11,
            extracted_path='extracted/e11be71ded044515.json')
    if model=='E-Class' and trim=='E 200 EXCLUSIVE':
        url='https://www.mercedes-benz.co.kr/passengercars/brand/news-events/news-story/2026/news-20260424.html'
        add({'length_mm':4955,'space_source_url':url},url,trim+' 2026 한국 사양',
            'Korean exact-trim launch supersedes earlier overseas body reference')
        corrections['length_mm']=4949
    return updates, evidence, corrections
