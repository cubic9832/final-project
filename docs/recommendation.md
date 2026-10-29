# 재무 진단 결과에서 클릭할 때만 차량 추천

현재 기본 번들은 `preference-cohorts/20261028-v6-web-recheck`이다. 웹 재검토를 통과한 추정 항목만 교체했으며, UI는 `cross-site-reported`(3곳 이상 제원 교차 확인)와 `cross-site-measured`(3곳 이상 실측 교차 확인)를 공식/추정 상태와 구분한다. 항목별 출처 링크와 확인 범위를 표시한다. [웹 재검토 기록](../data/vehicles/web-recheck-20261028/README.md)에 근접성·중복 출처·측정 조건 기준을 기록했다. 아래 v4 기록은 이전 버전이다.

현재 기본 번들은 `preference-cohorts/20261028-v4-complete`이다. 차량 상세에는 28개 공통 제원과 `estimated`/`official-reference`/`catalog-reference`/`visual-review` 상태를 함께 반환한다. 구매 추천의 `lifestyleEvidence.specifications`, 조사 차량의 `specifications`에서 확인한다. 전장 등 표시·취향용 추정값과 원본 재무·필수 정원 검증은 분리한다. [제원 보완 기록](../data/vehicles/complete-specifications-20261028/README.md)을 참고한다.

`ml/test`의 현재 기본 모델은 `controlled-cohort-ranker-v1`이다. 같은 재무 조건에서 선호를 바꾼 합성 비교군으로 학습하며, [모델 교체 보고서](../ml/outputs/reports/preference-cohorts-20261028/README.md)에 적용 범위를 기록했다. `researchSuggestions`는 취향 전용 조사 차량이며 `financialEligible=null`이고 구매 비용·구매 가능 추천에 포함하지 않는다. 현재 UI는 브랜드 선호를 전송하지 않는다. API에서 이 모델에 브랜드 선호를 전달하면 400 Problem Details로 거절한다.

> `ml/test` 브랜치는 [candidate-v2 실험](../ml/vehicle_matching/README.md)에 연결되어 있다. 이 브랜치에서는 재무 진단 4단계, 원 단위 v2 요청, 차량별 비용 검증과 추천 카드를 사용한다. 아래 5단계·20라벨·v1 관련 설명은 기존 hhc 구현 기록이다.

## 동작

기존 재무 진단 5단계 입력 화면과 헤더·메뉴를 유지한다. 입력 필드나 독립 추천 메뉴·입력 화면을 추가하지 않는다.

```text
기존 재무 진단 → 입력 확인 → 기존 종합 분석 결과
                                ↓ 추천 차량 확인하기 클릭
                          ML API 요청 → 별도 추천 결과 페이지
```

종합 결과 페이지에 진입하는 것만으로 요청하지 않는다. 클릭 전에는 추천 결과가 없고, 클릭 시에만 로딩 안내·중복 클릭 방지·추론을 수행한다. 성공하면 `/financial/recommendations`로 이동해 추천 카드를 보여준다. 실패하면 기존 진단 결과와 입력을 유지하며 같은 버튼으로 다시 시도한다. 필요한 기존 값이 비어 있으면 상태 안내를 표시하고 임의 프로필로 요청하지 않는다.

추천 페이지는 라우터 상태로 전달받은 진단값과 추천 결과를 사용하며 진입 시 추론을 다시 요청하지 않는다. 진단값 없이 주소로 직접 접근하면 재무 진단으로 이동한다. 분석 결과로 돌아가기와 진단 조건 수정 버튼은 기존 입력값을 유지한다.

## 차량 이미지

추천 카드의 `labelCode`(OWN001–OWN020)에 맞춰 전면 사선 예시 이미지 20종을 연결했다. 공식 사진을 imagegen으로 편집해 배경과 바닥 그림자를 제거했으며, 투명 무손실 WebP 1536×1024 규격으로 통일했다. 차량의 비율을 유지하면서 최대 표시 영역을 1306×666으로 맞추고 하단 기준선을 820px에 정렬했다. 편집본은 `front/public/images/recommendations/cutouts/`, 라벨별 `src`·`alt` 매핑은 `front/src/features/vehicle/recommendationImages.js`에 둔다. 정적 파일은 프런트 빌드에 포함되며 제조사 사이트에 이미지 요청을 보내지 않는다.

카드는 이미지 전체가 잘리지 않도록 `object-fit: contain`으로 표시한다. 이미지가 없거나 로드에 실패하면 기존 준비 중 표시를 사용한다. 라벨별 로컬 배경 제거 이미지를 우선 사용하고, 등록되지 않은 라벨만 API의 `imageUrl`을 사용한다. 화면 하단에서 실제 연식·트림·색상과 다를 수 있는 예시임을 안내한다.

선정 원본과 출처·해상도·해시는 [이미지 수집 기록](../data/vehicles/official-image-review/front-three-quarter/README.md)과 같은 폴더의 `manifest.json`에 보관했다. 원본은 유지하며 카드에는 배경 제거 편집본을 사용한다. ES 이미지는 현재 ES 350h다. 이미지 재사용 허락은 별도로 확인하지 않은 상태다.

## 실행

저장소 루트의 첫 번째 PowerShell:

```powershell
& ./ml/.venv/Scripts/python.exe -m pip install -e "./ml[serve,test]"
& ./ml/.venv/Scripts/python.exe -m recommender train --segment all-cars
./ml/serve.ps1
```

이미 financial-ui-v1 모델을 학습했다면 학습 명령은 생략한다. 별도 터미널에서 `npm --prefix front run dev`를 실행한다. `/financial`에서 진단을 마친 뒤 마지막 페이지의 추천 차량 확인하기를 누른다.

## 기존 진단과 모델의 연결

추천 카드는 브랜드·차명·차체·차급, 추천 사유와 모델 예측 확률을 표시한다. `buildRecommendationDetails.js`가 진단 이용목적·연간 주행거리·추천 순위를 바탕으로 조건 요약과 차체별 참고 설명을 구성한다. 차량 특징 설명은 화면의 규칙 기반 안내이며 모델의 개별 특성 기여도 설명은 아니다. 가격·연료·연비는 추천 API에 없어 임의로 표시하지 않는다.

모델은 현재 UI 항목에 맞춰 재학습했다. 나이·성별·직업·가구원·세전 연봉·추가 자산·실제 저축액을 새로 요구하지 않는다.

| 진단값 | 모델 입력 |
| --- | --- |
| 월 실수령액+기타 정기 소득 | 월 실수령소득 |
| 사용 가능 예금 | 현금성 자산 |
| 월 주거비 | 월 주거비 |
| 고정 지출+생활비+별도 교통비+통신비 | 월 기타 생활소비 |
| 대출 상세 잔액 합계 | 차량 구매 전 대출 잔액 |
| 1단계 현재 대출 월 상환액 | 차량 구매 전 월 상환액 |
| 연간 주행거리·주 이용목적 | 동일 값과 목적 코드 |

선택 항목을 비워두면 기존 UI의 계산처럼 0으로 취급한다. 최초의 미입력 대출 행도 빈 행으로 처리하지만, 일부를 입력하고 잔액만 빠진 대출은 보완 안내를 한다. 만 원을 원으로 변환하며 목표 저축액·연체정보·신용점수 등 모델이 사용하지 않는 입력을 반영했다고 표시하지 않는다. 예산 계산의 기존 수식도 유지한다.

국내·수입차 통합 20개 라벨의 단일 모델을 사용한다. 별도의 차량 구분 UI는 추가하지 않는다. 모델 확률은 구매 적합도나 구매 가능 확률이 아니다. 실제 가격·트림 DB 매칭이나 예산 필터링은 아직 포함하지 않는다.

## API

Vite 개발 프록시는 POST `/api/v1/recommendations`만 127.0.0.1:8001로 보낸다. 나머지 API는 기존 Spring으로 전달한다. 본문은 `{segment: "all-cars", profile, k: 3}`이고 profile은 `ml/examples/profile.json`의 스키마다.

성공은200과 `{success: true, data: {segment, modelVersion, recommendations}}`다. 차량 항목은 labelCode·model·body·grade·probability다. 실패는 application/problem+json이며 입력400·모델 사용 불가503·내부 오류500을 구분한다. 이 기능은 프로필을 파일·DB·localStorage에 저장하지 않는다.

서버는 시작할 때 `ml/outputs/models/financial-ui-v1/all-cars`의 최신 모델을 읽는다. 이전 17항목 모델은 사용하지 않으며 입력 스키마 검사로 호환되지 않는 모델을 거부한다. 운영에서는 Vite 프록시 대신 웹 서버·게이트웨이에 경로를 설정해야 한다.

## 검증

프런트 테스트는 단위 변환·기존 필수값·빈 대출 행·부채와 생활비 중복 방지를 확인한다. ML 테스트는 통합 데이터 20개 라벨과 구매 전 월상환액의 누수 방지를 포함한다. 브라우저에서 기존 입력 5단계를 완료하고 추천 버튼 클릭 후 별도 페이지에 실제 추천 3대와 이미지 대체 영역이 표시되는 것을 확인했다.
