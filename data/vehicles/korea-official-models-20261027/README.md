# 국내 공식 모델군 1차 목록 — 2026-10-27

공식 출처를 확보한 24개 브랜드, 168개 모델군 행이다. 국내 시장 전체 전수 목록은 아니다.

## 검증 수준

- 국내 공식 메뉴·가격표·구성기 등재 확인: 149개
- 검색 색인으로만 확인하여 직접 재검증 필요: 7개
- 현지화 소개 메뉴 확인, 국내 계약 가능 여부 추가 확인 필요: 12개

공식 등재가 실시간 주문·재고·납기를 보장하지 않는다. 모델군별 최신 가격표와 국내 계약 가능 여부를 확인한 뒤 수집 대상으로 확정한다.

## 기존 카탈로그와 비교

기준은 round2 after.json의 308개 구성, 63개 모델군이다. 중복 대조 후 60개 행은 기존 모델군이며, 108개는 신규 모델군 후보다.

신규 후보는 국내 판매·가격·제원까지 확정한 DB 투입 데이터가 아니다. FAMILY_PRESENT 역시 해당 모델의 모든 트림·가격대가 확보됐다는 의미가 아니다.

## 중복 제거 결과

기존 56개 연결·112개 미연결에서 영문 대소문자와 한글 대응 4개를 추가 확인했다. 공식 원본 168개 행은 보존하고 신규 후보 파일에서 기존 모델을 제외했다.

|공식 목록 표기|기존 카탈로그|처리|
|---|---|---|
|GMC CANYON|GMC Canyon|대소문자 정규화|
|GMC SIERRA|GMC Sierra|대소문자 정규화|
|토요타 ALPHARD|토요타 알파드|명시적 영문·한글 별칭|
|토요타 SIENNA|토요타 시에나|명시적 영문·한글 별칭|

신규 108개 중 국내 공식 목록 확인은 91개이며, 나머지는 검색 색인·현지화 소개 수준으로 국내 판매 확인이 더 필요하다.

- `new-model-candidates.csv/json`: 기존 모델 제외 후 신규 수집 대상
- `existing-model-matches.csv/json`: 기존 모델 연결 및 대응 방식
- `name-aliases.json`: 검토한 이름 대응 규칙
- 공식 목록 내부에서 정규화된 동일 이름 또는 같은 기존 모델군으로 중복 연결되는 행은 없음.
- 브랜드를 넘어 이름을 합치거나 부분 문자열·유사도만으로 병합하지 않음.
- G70 Shooting Brake, BMW 투어링, 쿠페·컨버터블 및 GLC/GLE Coupe 등 차체 파생형은 유지. 무쏘 EV, Escalade IQ, iX3 등 별도 모델 식별도 유지. 원본 목록의 파생형 통합 기준은 아래 참조.

## 브랜드별 모델군과 공식 출처

|브랜드|행 수|모델군|공식 출처|
|---|---:|---|---|
|현대|14|아반떼, 쏘나타, 그랜저, 베뉴, 코나, 투싼, 싼타페, 팰리세이드, 캐스퍼, 스타리아, 넥쏘, 아이오닉 5, 아이오닉 6, 아이오닉 9|[공식 목록](https://www.hyundai.com/kr/ko/e/api/product/car/catalog-price)|
|기아|17|모닝, 레이, K5, K8, K9, 니로, 셀토스, 스포티지, 쏘렌토, 카니발, 타스만, EV3, EV4, EV5, EV6, EV9, PV5 패신저|[공식 목록](https://www.kia.com/kr/vehicles/rv)|
|제네시스|7|G70, G70 Shooting Brake, G80, G90, GV60, GV70, GV80|[공식 목록](https://www.genesis.com/kr/ko/models.html)|
|KG모빌리티|6|티볼리, 토레스, 액티언, 렉스턴 뉴 아레나, 무쏘, 무쏘 EV|[공식 목록](https://web.kg-mobility.com/app/estimate/getCarTopModelList.do)|
|르노코리아|3|아르카나, 그랑 콜레오스, 필랑트|[공식 목록](https://www.renault.co.kr/ko/model/model_list.jsp)|
|쉐보레|2|트랙스 크로스오버, 트레일블레이저|[공식 목록](https://www.chevrolet.co.kr/)|
|GMC|4|ACADIA, CANYON, HUMMER EV SUV, SIERRA|[공식 목록](https://www.gmckorea.co.kr/)|
|캐딜락|2|ESCALADE, ESCALADE IQ|[공식 목록](https://www.cadillac.co.kr/purchase/onlineshop/index.gm)|
|BMW|24|1시리즈, 2시리즈 쿠페, 2시리즈 그란쿠페, 2시리즈 액티브 투어러, 3시리즈, 3시리즈 투어링, 4시리즈 쿠페, 4시리즈 그란쿠페, 4시리즈 컨버터블, 5시리즈, 5시리즈 투어링, 7시리즈, 8시리즈 그란쿠페, Z4, X1, X2, X3, X4, X5, X6, X7, XM, iX, iX3|[공식 목록](https://www.bmw.co.kr/content/dam/bmw/marketKR/bmw_co_kr/Pricelist/pricelist_oct2026.pdf.asset.1792129034710.pdf)|
|메르세데스-벤츠|22|A-Class Hatch, CLA Sedan, CLA Coupe, C-Class, E-Class, EQE, S-Class, GLA, GLB, GLC, GLC Coupe, GLE, GLE Coupe, GLS, EQE SUV, EQS SUV, G-Class, CLE Coupe, CLE Cabriolet, AMG GT Coupe, AMG GT 4-Door Coupe, SL Roadster|[공식 목록](https://www.mercedes-benz.co.kr/passengercars/models.html)|
|아우디|11|A3, A5, A6, A8, Q3, Q5, Q7, Q8, Q4 e-tron, A6 e-tron, e-tron GT|[공식 목록](https://www.audi.co.kr/ko/models/)|
|폭스바겐|5|Golf, Atlas, Touareg, ID.4, ID.5|[공식 목록](https://www.volkswagen.co.kr/ko/models.html)|
|MINI|4|Cooper, Cooper Convertible, Countryman, Aceman|[공식 목록](https://www.mini.co.kr/ko_KR/home/Product-Information-KR.html)|
|볼보|8|EX30, EX90, ES90, XC40, XC60, XC90, S90, V60 Cross Country|[공식 목록](https://www.volvocar.co.kr/l/volvo-brochure/)|
|토요타|7|RAV4, CAMRY, CROWN, HIGHLANDER, ALPHARD, SIENNA, GR86|[공식 목록](https://www.toyota.co.kr/build-my-car/)|
|BYD|5|DOLPHIN, ATTO 3, SEAL, SEALION 7, SEALION 6 DM-i|[공식 목록](https://www.bydauto.kr/index)|
|지커|1|7X|[공식 목록](https://www.zeekrlife.com/ko-kr/)|
|푸조|4|308, 408, 3008, 5008|[공식 목록](https://www.epeugeot.co.kr/car-selector/peugeot-range.html)|
|지프|3|GRAND CHEROKEE L, WRANGLER, GLADIATOR|[공식 목록](https://www.jeep.co.kr/)|
|로터스|3|Eletre, Emira, Emeya|[공식 목록](https://www.lotuscars.com/ko-KR)|
|벤틀리|4|Bentayga, Flying Spur, Continental GT, Continental GTC|[공식 목록](https://www.bentleymotors.com/kr/ko/models.html)|
|롤스로이스|4|Phantom, Ghost, Cullinan, Spectre|[공식 목록](https://www.rolls-roycemotorcars.com/seoul/ko_KR/showroom.html)|
|마세라티|5|Grecale, GranTurismo, GranCabrio, MCPURA, GT2 Stradale|[공식 목록](https://www.maserati.com/kr/ko/models)|
|람보르기니|3|Revuelto, Urus, Temerario|[공식 목록](https://www.lamborghini.com/ko-en)|

## 미완료 범위

- 렉서스: 국내 구성기 본문을 추출하지 못함. ES 외 모델을 기억에 의존해 채우지 않음
- 테슬라: 국내 홈페이지 본문 추출 불가. 주문 가능한 국내 모델 전수 확인 필요
- 포드·링컨: 국내 공식 사이트가 flak.co.kr로 이동; 동적 라인업 추출 미완료
- 랜드로버: Range Rover·Defender·Discovery 상위 브랜드 메뉴까지 확인. 하위 판매 모델 재검증 필요
- 폴스타: 2·3·4·5 소개 메뉴는 확인. 소개와 현재 국내 주문 가능 모델 구분 미완료
- 포르쉐: 국내 전체 모델·차체 파생형 전수 목록 정규화 미완료
- 혼다: 국내 구매 가능 전체 모델 목록 최종 교차 검증 미완료
- 페라리: 공식 라인업 접근 시 확인 화면으로 추출 불가
- 애스턴마틴·맥라렌: 국내 공식 판매사 모델 목록 출처 추가 확보 필요

## 통합·제외 기준

- 공식 사이트 등재는 실시간 재고·계약 가능·납기 보장이 아니다. 국내 가격표/구성기가 확보된 모델부터 후속 검수한다.
- 기본 모델명 단위의 목록이다. 하이브리드·GT·N·M·긴 휠베이스·한정판을 별도 모델 수로 부풀리지 않는다.
- 현대 코나/캐스퍼 및 제네시스 G80/GV70 전동화 파생형, KG 토레스 EVX는 기존 카탈로그 모델군 기준으로 통합한다.
- BMW i4는 4시리즈 그란쿠페, i5는 5시리즈, i7은 7시리즈, iX1/iX2는 X1/X2에 통합. 별도 플랫폼 iX 및 신형 iX3는 분리한다. M5 Touring은 5시리즈 투어링으로 표시한다.
- 차체가 다른 파생형은 필요한 경우 별도 행으로 유지한다. 목록 수준이 브랜드별로 달라 전시장 모델 수의 엄밀한 브랜드 간 비교에 사용하지 않는다.
- 트럭·버스·특장차·화물 전용 PBV는 제외한다. 승용 스타리아 및 PV5 패신저는 포함한다.
- 가격·좌석·연료·차체 enum을 추측해 채우지 않는다. 이 목록은 DB 투입 데이터가 아닌 후속 가격·제원 수집 대상 목록이다.
- 가격 상한은 적용하지 않는다. 1억원 초과 모델도 동일하게 포함한다. 국내 시장 전체의 확정 전수 목록이 아니라 출처를 확보한 1차 목록이다.

## 다음 검수

1. 미완료 브랜드의 국내 주문 가능 모델과 현재 가격표를 확보한다.
2. 모델군별 차체·연료·좌석·최저/최고 가격을 공식 제원표로 확인한다.
3. 기존 모델명을 수동 대응한 뒤 차체 × 가격대의 실제 빈 구간을 계산한다.
4. 빈 구간을 채우는 모델·트림부터 가격·제원을 확보해 DB 추가 대상으로 검수한다.

이번 작업은 목록 파일만 생성한다. DB·추천 조건·학습 모델은 변경하지 않는다.
