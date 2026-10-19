# 국내 신차 데이터 수집

2026-10-14에 확인한 현대·기아·제네시스·KG모빌리티·르노코리아·쉐보레의 국내 판매 사이트 자료다. 국내 생산 여부로 구분한 데이터는 아니다. 중고차, 상용 트럭·버스, 택시·통학 전용 모델은 제외한다. 승용과 밴이 한 가격표에 함께 있으면 원자료에는 밴 내용이 남아 있으므로 정규화할 때 제외해야 한다.

## 파일

- `COLLECTION.md`: 브랜드별 범위와 모델별 추출 성공·실패 현황.
- `official-model-manifest.json`: 공식 모델 표기, 원문 URL, 자료 유형, 추출 파일 경로, 원자료 SHA-256.
- `extracted/*.json`: 공식 PDF의 페이지별 텍스트 및 공식 웹페이지의 텍스트·표. **원자료 추출본이며 바로 학습하거나 계산할 수 있는 정규화 테이블은 아니다.**
- `official-vehicle-evidence.json`: 가격·연비·전비 관련 원문 위치와 주변 문맥. 옵션 가격·공급가액·세제혜택 전후 가격을 자동 확정하지 않는다.
- `domestic-new-vehicles-2026-10-14.json`: 앞서 확인한 셀토스·니로 11개 사양의 초기 계산 예제. 전체 수집본과 구분한다.

## 재현

Python과 `requirements.txt`의 라이브러리를 준비한 뒤 저장소 루트에서 실행한다.

```powershell
python -m pip install -r data/vehicles/requirements.txt
python -m tools.data.vehicles.probe_sources
python -m tools.data.vehicles.collect_official_vehicles
python -m tools.data.vehicles.build_collection_report
```

네트워크 접근이 필요하다. 제조사별로 순차 요청하고 문서 요청 사이에 간격을 둔다. `probe_sources.py`가 저장하는 HTML/JSON 원문은 `sources/`에 임시 보관하며 Git에서 제외한다. JavaScript 앱 코드나 로그인 데이터는 수집하지 않는다. 모델 목록과 문서 경로는 2026-10 스냅샷 기준이므로 다른 달의 재수집에는 월별 파일명과 확인일을 갱신해야 한다.

기존 성공 자료를 유지하고 실패 자료를 다시 확인하려면 다음을 실행한다.

```powershell
python -m tools.data.vehicles.collect_official_vehicles --resume
python -m tools.data.vehicles.build_collection_report
```

`--resume`은 저장된 스냅샷의 누락 복구용이다. 성공 자료의 가격 갱신에는 새로 수집하는 첫 번째 절차를 사용한다. 실패 응답은 0원이나 가상 제원으로 대체하지 않는다.

## 계산용 데이터로 변환할 때

한 행의 식별 단위는 제조사·모델 세대·연식·트림·파워트레인·구동 방식·휠·연비에 영향을 주는 선택 사양이다. 문서의 발행월을 연식으로 간주하지 않는다.

1. 가격표의 판매가격을 옵션 가격·공급가액과 분리하고 세제혜택 기준을 기록한다.
2. 기본 휠과 구동 방식에 맞는 연비/전비를 연결한다. 빌트인 캠 등에 따른 차이를 보존한다.
3. 가솔린·디젤·LPG의 `km/L`, 전기차의 `km/kWh`, 수소차의 단위를 구분한다.
4. 같은 브랜드의 구형/신형 모델과 판매 예정 모델을 계약 가능한 현행 모델로 자동 취급하지 않는다.
5. 원문 페이지·확인일을 연결하고, 수치와 사양 조합을 검증한 행만 DB에 넣는다.

현재 `normalizedSpecifications`가 비어 있는 것은 미검증 상태를 의미한다. 자료 수집 성공과 사양 연결 검증을 구분하기 위해 앱 DB에는 자동 반영하지 않았다. 개인 재무 가상 데이터나 머신러닝 학습 정답은 이 차량 원자료에 포함하지 않는다.

## 세부 수치 추출 CSV

`normalize_vehicle_details.py`는 공식 가격표 원문에서 판매가격·엔진·기본 휠과 인증 연비 사양을 별도로 추출한다. 실행 시 `normalized-vehicle-details.json`을 갱신한다.

- `csv/domestic-vehicle-details.csv`: 트림 판매가격과 엔진·연료·기본 휠 조건에서 연비 사양이 한 건으로 좁혀지는 경우에만 연결한 결과. `가격_연비연결상태`를 확인한다.
- `csv/domestic-trim-prices.csv`: 판매가격, 세제혜택 전후 가격, 파워트레인, 기본 휠, 원문 근거. 옵션 추가금과 공급가액은 판매가격으로 사용하지 않는다.
- `csv/domestic-efficiency-specifications.csv`: 구동·휠·배기량·연비·전비·전기차 주행거리별 사양. 니로·카니발 등의 표 열 순서를 반영한다.

공란은 미확인 또는 미적용 값이며 0이 아니다. 공식 자료에서 세제혜택 후 가격이 안내 예정이면 그 가격을 계산하지 않는다. 기본품목 상속은 가격표에 명시된 상위 트림을 기준으로 처리하며, 특화 외장 디자인의 휠 주석을 먼저 적용한다. 구동·좌석·선택 사양이 여러 개인 경우 연비를 임의 연결하지 않는다.

전체 행을 사람이 검수한 완성본은 아니다. 자동 추출 범위 밖의 모델·트림, 병합된 표 셀, 제네시스의 추가 엔진 선택금액, 옵션별 조합은 추가 검증이 필요하다. 원문에서 직접 확인된 수치와 자동 사양 연결을 구분한다. `normalized-vehicle-details.json`의 `rejected_efficiency_rows`는 연비 열 배치가 명확하지 않아 CSV에서 제외한 행이다.

파서 검증 명령:

```powershell
python -m unittest tools.data.vehicles.test_normalize_vehicle_details
python -m tools.data.vehicles.normalize_vehicle_details
```
