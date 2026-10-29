# 국내 공식 쿠페·오픈카 검토 스냅샷

검토일: 2026-10-28. 국내·해외 브랜드를 모두 대상으로 국내 공식 판매 근거와 가격을 연결한 **11개 모델군, 22개 사양**이다. 전체 시장 목록을 완성했다는 뜻은 아니다.

- BMW: 2시리즈 쿠페/그란쿠페, 4시리즈 쿠페/그란쿠페/컨버터블, 8시리즈 그란쿠페, Z4 — 7개 모델군 13개 사양.
- MINI Cooper Convertible — 1개 모델군 3개 사양.
- Toyota GR86 — 1개 모델군 2개 사양.
- Maserati GranTurismo / GranCabrio — 2개 모델군 4개 사양.

가격 범위는 4,360만~3억 530만원이다. BMW는 국내 공식 2026년 10월 가격표, MINI는 국내 공식 가격·제원표, Toyota는 국내 공식 모델 자료, Maserati는 국내 공식 딜러의 2026년형 가격을 사용했다. 그란쿠페는 제조사 분류를 보존했으며 2도어라는 의미가 아니다. 쿠페형 SUV는 SUV로 유지한다.

`reviewed.json`에 검토 값과 보류 이유, `field-evidence.json`에 사양별 출처·누락 필드·확보한 원본 해시가 있다. 원문 다운로드는 `sources/`에 로컬 보관한다. 좌석 미확인 15개 사양, 길이 미확인 17개 사양은 null을 유지한다. 미확인 정원은 최소 인원이 지정된 추천/학습에 사용할 수 없다. 연비 누락은 기존 연료별 유지비 가정을 사용하므로 실제 스포츠카 유지비와 차이가 날 수 있다.

Porsche, Mercedes-Benz, Lotus, Ferrari, Lamborghini, Aston Martin, McLaren, Bentley, Rolls-Royce, Lexus, Ford 등은 현행 국내 가격과 정확한 판매 사양을 추가 확인해야 한다. 과거 가격이나 옵션 포함 재고 가격을 기본 가격으로 대입하지 않았다. 국내 브랜드도 확인 범위에 포함했으며 신규 독립 쿠페·오픈카로 연결할 현행 모델은 확보하지 못했다.

재현: `ml/.venv/Scripts/python.exe tools/data/vehicles/build_sports_catalog.py`.
공식 수집: `tools/data/vehicles/collect_sports_sources.py`. 웹 추출 보완 자료도 출처 기록에 포함한다.

이 자료는 학습 카탈로그 보강용이며 운영 DB를 수정하지 않는다.
