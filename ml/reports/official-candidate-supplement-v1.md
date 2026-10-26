# 공식 출처 기반 추천 후보 보강 v1

작업 브랜치: ml/test. main·원본 CSV·학습 데이터·모델 체크포인트는 수정하지 않음.

기존 265개 사양/76개 모델 → 281개 사양/84개 모델. 16개 사양 추가, 신규 모델명 8개, 기존 BMW 5시리즈·X3의 디젤 사양 보강.

| 브랜드 | 모델 | 트림 | 연료 | 가격(원) | 출처 |
|---|---|---|---|---:|---|
| 현대 | 캐스퍼 | 스마트 | GASOLINE | 15,460,000 | [공식 자료](https://www.hyundaimotorgroup.com/ko/news/hyundai-motor-company-casper-electric-2027) |
| 현대 | 캐스퍼 | 디 에센셜 | GASOLINE | 17,920,000 | [공식 자료](https://www.hyundaimotorgroup.com/ko/news/hyundai-motor-company-casper-electric-2027) |
| 현대 | 캐스퍼 | 인스퍼레이션 | GASOLINE | 20,350,000 | [공식 자료](https://www.hyundaimotorgroup.com/ko/news/hyundai-motor-company-casper-electric-2027) |
| 현대 | 캐스퍼 일렉트릭 | 프리미엄 | ELECTRIC | 28,470,000 | [공식 자료](https://www.hyundaimotorgroup.com/ko/news/hyundai-motor-company-casper-electric-2027) |
| 현대 | 캐스퍼 일렉트릭 | 인스퍼레이션 | ELECTRIC | 32,120,000 | [공식 자료](https://www.hyundaimotorgroup.com/ko/news/hyundai-motor-company-casper-electric-2027) |
| 현대 | 캐스퍼 일렉트릭 | 크로스 | ELECTRIC | 34,120,000 | [공식 자료](https://www.hyundaimotorgroup.com/ko/news/hyundai-motor-company-casper-electric-2027) |
| 현대 | 캐스퍼 일렉트릭 | 라운지 | ELECTRIC | 34,570,000 | [공식 자료](https://www.hyundaimotorgroup.com/ko/news/hyundai-motor-company-casper-electric-2027) |
| 기아 | 레이 EV | 라이트 4인승 | ELECTRIC | 28,520,000 | [공식 자료](https://www.kia.com/kr/vehicles/ray-ev/price) |
| 기아 | 레이 EV | 에어 4인승 | ELECTRIC | 30,620,000 | [공식 자료](https://www.kia.com/kr/vehicles/ray-ev/price) |
| BMW | 3시리즈 | 320d | DIESEL | 63,500,000 | [공식 자료](https://www.bmw.co.kr/content/dam/bmw/marketKR/bmw_co_kr/Pricelist/PRICELIST_JUNE2026.pdf.asset.1781249167044.pdf) |
| BMW | 3시리즈 투어링 | 320d 투어링 | DIESEL | 66,000,000 | [공식 자료](https://www.bmw.co.kr/content/dam/bmw/marketKR/bmw_co_kr/Pricelist/PRICELIST_JUNE2026.pdf.asset.1781249167044.pdf) |
| BMW | 5시리즈 | 523d | DIESEL | 79,100,000 | [공식 자료](https://www.bmw.co.kr/content/dam/bmw/marketKR/bmw_co_kr/Pricelist/PRICELIST_JUNE2026.pdf.asset.1781249167044.pdf) |
| BMW | X1 | sDrive18d xLine | DIESEL | 60,400,000 | [공식 자료](https://www.bmw.co.kr/content/dam/bmw/marketKR/bmw_co_kr/Pricelist/PRICELIST_JUNE2026.pdf.asset.1781249167044.pdf) |
| BMW | X3 | 20d xDrive | DIESEL | 73,000,000 | [공식 자료](https://www.bmw.co.kr/content/dam/bmw/marketKR/bmw_co_kr/Pricelist/PRICELIST_JUNE2026.pdf.asset.1781249167044.pdf) |
| BMW | X4 | xDrive20d M 스포츠 | DIESEL | 83,400,000 | [공식 자료](https://www.bmw.co.kr/content/dam/bmw/marketKR/bmw_co_kr/Pricelist/PRICELIST_JUNE2026.pdf.asset.1781249167044.pdf) |
| BMW | X5 | xDrive30d xLine 7인승 | DIESEL | 119,200,000 | [공식 자료](https://www.bmw.co.kr/content/dam/bmw/marketKR/bmw_co_kr/Pricelist/PRICELIST_JUNE2026.pdf.asset.1781249167044.pdf) |

## 데이터 취급

- 확인일 2026-10-22. 제조사 가격표·보도자료에 명시된 가격 시점의 스냅샷이며 당일 출고·재고를 보장하지 않는다.
- 캐스퍼 2027년형은 2026-07-15 공식 발표 가격. 캐스퍼 일렉트릭은 친환경차 세제혜택 적용 후, 구매 보조금 차감 전 가격.
- 레이 EV는 공식 현재 가격 페이지의 4인승 라이트·에어. 밴은 제외. 연식은 별도 확인하지 않아 빈 값.
- BMW PDF 파일명은 June2026이지만 열람 본문에는 2026년 7월이라고 명시되어 이를 출처 기준으로 기록. 디젤 7개 사양, 연식 미확인.
- 쏘렌토 디젤은 과거 공식 자료에 있으나 현재 공식 가격 페이지에서 찾지 못해 추가 보류. 과거 판매 자료만으로 현재 판매를 단정하지 않는다.
- 미확인 연비·전장·좌석은 null 유지. 레이 EV만 4인승 가격표 기준 좌석 확인. 부족한 제원은 기존 서비스의 중립 점수·명시된 연료별 유지비 추정으로 처리한다.
- 실제 신규 차종 학습 사례를 생성하거나 재학습하지 않았다. 기존 쌍 비교 모델과 가중 정책에 신규 후보를 제공한다.

## 검증

- 기존 후보 보존·추가 병합 중복 방지·멱등성 테스트 통과.
- 예산·선호·월 유지비·카탈로그 통합 관련 17개 테스트 통과.
- 실제 서버 catalogCount=281 확인.
- 가용 현금 4,000만 원, 월소득 600만 원, 생활비 150만 원, 기존월상환 20만 원, 저축 100만 원, 연료 중요도 5, 전기 선호: 캐스퍼 일렉트릭(3,212만), 레이 EV(3,062만), EV3(3,995만). 모두 현금 한도 내.
- 2,000만 원 이하 후보에 캐스퍼 포함 확인. 디젤 중요도 조건에서 추가 디젤 후보가 추천에 포함되는지 검증.

추가 원본: data/vehicles/official-candidate-supplement-v1.json. 실행 응답: tmp/ml-test-servers/official-supplement-live.json.

남은 공백: 저예산 디젤은 이번 보강으로 해결하지 못함. 신규 후보의 공식 최신 연비·전장 확보가 후속 과제.
