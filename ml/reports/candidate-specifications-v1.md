# 차량 제원 보완 및 재학습 결과

작업 브랜치: `ml/test`. main 브랜치, 원본 가구·선택 데이터, 기존 가격 CSV 및 이전 모델 파일은 수정하지 않았다. 새 제원은 차량 ID·브랜드·모델·트림·가격·연료를 대조하는 별도 보완 파일로 적용한다.

현재 추천 대상은 **84개 모델, 281개 사양**이다.

| 항목 | 보완 전 누락 | 보완 후 누락 |
|---|---:|---:|
| 연비·전비 | 204 | 0 |
| 전장 | 129 | 0 |
| 좌석 수 또는 공식 정원 선택지 | 13 | 0 |

좌석 단일 값이 비어 있던 18개 중 5개는 이미 여러 정원 선택지가 있던 차량이다. 이 5개를 좌석 정보 자체가 없는 사례로 계산하지 않았다. 기존에 입력받은 좌석 정보 251개 사양을 이번 작업으로 전부 독립 검증했다는 의미는 아니다. 이전 좌석 입력과 공식 자료가 충돌한 14개는 공식 정원으로 보정된 상태와 변경 이력을 유지한다.

## 구성과 출처

- 현대·기아·제네시스·KGM·르노 등의 모델별 공식 가격표·제원표를 연결했다. 전기차는 km/kWh, 나머지는 km/L로 구분한다.
- 엔진·구동·휠이 특정되지 않은 행은 사용자가 승인한 방식대로 기본 구성을 명시했다. 같은 연비를 갖는 여러 인증 구성은 그 조건들을 함께 기록했다.
- 수입차의 전장은 국내 개별 트림 자료가 없을 때 같은 세대의 제조사 해외 차체 자료를 참조했다. 해외 WLTP 연비를 국내 공인연비로 섞지 않았다. BMW 3시리즈의 4,713mm 등 해외 차체 참조값은 국내 표기와 수 mm 차이가 날 수 있다.
- BMW 디젤, K5 LPG, 쏘렌토 하이브리드는 한국에너지공단 공개 조회 결과를 추가 확보했다. 인증번호·인증일·구동방식·타이어·인승을 보존한다. 같은 모델명 중 최신 일치 인증 구성을 명시적으로 선택한다. 예: 320d 기본 18인치 15.2km/L, 320d Touring 14.4km/L, X5 7인승 11.4km/L.
- E 200 EXCLUSIVE 전장은 국내 2026년 공식 발표의 4,955mm로 해외 차체 참조값 4,949mm를 보정했다. 이전 값이 예상과 다른 경우에는 자동 덮어쓰지 않는다.
- XC60 T8은 플러그인 하이브리드로 바로잡았다. 현재 연료 분류에서는 HYBRID로 평가하고 원래 종류 PHEV를 함께 표시한다. 유지비는 공식 휘발유 기준 11.7km/L를 사용하며 전기 주행 비율과 충전 절감 효과를 가정하지 않는다.

**정확한 기본 사양 인증값이 미확정인 2개는 별도 표시한다.**

| 차량 | 사용한 참조값 | 한계 |
|---|---:|---|
| K5 LPG 트렌디 | 9.7km/L | 공개된 PE 16인치 인증은 빌트인 캠 장착 조건이다. 기본 미장착 값으로 확정하지 않는다. |
| BMW X4 xDrive20d M 스포츠 | 12.5km/L | 최신 공개 기본 인증 타이어는 18인치다. M 스포츠의 정확한 기본 휠 사양과 일치한 값으로 확정하지 않는다. |

이 2개는 `efficiency_reference_only=true`, 비용 응답의 `efficiency_estimated=true`를 유지한다. 화면에도 참조 연비임을 표시한다. 참조 구성에 들어간 선택품목이 기존 차량 가격에 포함되었다는 뜻이 아니다. 나머지 기본 구성 선택 역시 실제 계약 차량의 옵션 확인을 대체하지 않는다.

## 적용과 검증

제원 적용을 학습과 추론에 공통으로 연결하고 새 모델을 `ml/outputs/models/candidate-retrained/20261022-specifications-v1`에 저장했다. 이전 모델은 보존한다. 학습 프로필 600개, 검증 150개, 평가 200개이며 17개 모델은 학습에서 보류했다. 새 평가의 합성 기준 NDCG@3은 0.996684이다. 제원 변경으로 평가 효용도 달라졌으므로 이전 보고서의 숫자와 단순 비교하지 않는다.

독립 재무 프로필 300개, 차량 가격보다 1원 부족하거나 정확히 일치하는 경계, 연료·소득 변경을 합친 **865건에서 2,214개 추천**을 검사했다. 구매 현금 초과·최소 월 여유자금 미달·부적격 추천·동일 모델 중복·가용 후보 누락은 **0건**이었다. 118건은 재무 조건상 추천할 차량이 없어 추천 없음으로 반환했다.

관련 Python 테스트 24개와 프론트엔드 빌드가 통과했다. 실제 프론트엔드 프록시의 추천 요청에서도 새 모델과 계산 기준 구성을 확인했다.

## 파일

- 전체 적용 카탈로그: `data/vehicles/candidate-catalog-specifications-v1.json`
- 차량별 변경·구성·출처·인증 이력: `data/vehicles/candidate-specifications-v1.json`
- 수집 근거: `data/vehicles/sources/specification-pages-20261022/`
- 검증 결과: `ml/reports/candidate-specifications-v1-audit.json`
- 생성: `ml/.venv/Scripts/python.exe tools/data/vehicles/build_candidate_specifications.py`
- 검증: `ml/.venv/Scripts/python.exe tools/data/vehicles/verify_candidate_specifications.py --run ml/outputs/models/candidate-retrained/20261022-specifications-v1`
- 정부 인증 원문 재수집: `python tools/data/vehicles/collect_certified_efficiency.py --output <새 버전 디렉터리>` (BeautifulSoup 필요)

공식 근거: [한국에너지공단 공개 조회](https://min24.energy.or.kr/trans_hp/AHP/HP_03/HP_03_01_010.do), [볼보 MY26 XC60 제원](https://www.volvocar.co.kr/l/volvo-brochure/pdf/MY26-XC60.pdf?ver=20251208), [렉서스 ES 350h](https://www.lexus.co.kr/models/ES-350h/). 나머지 출처는 차량별 보완 파일에 기록했다.
