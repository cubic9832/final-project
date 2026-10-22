# 실제 DB 스키마

`src/main/resources/db/migration/V1__create_schema.sql`은 제공된 CreditCompass Auto ERD의 15개 테이블을 MySQL 8.0용으로 작성한 파일입니다.

## 적용

스키마는 [Flyway](https://documentation.red-gate.com/fd)로 버전 관리합니다. Spring Boot를 시작하면 `application.yml`의 datasource DB(`final_sample`)에 `db/migration`의 SQL이 버전 순서대로 자동 적용되고, 적용 이력은 `flyway_schema_history` 테이블에 기록됩니다. 수동으로 실행할 필요가 없습니다.

- 스키마를 변경할 때는 `V{다음 번호}__{설명}.sql` 파일을 추가합니다. 예: `V3__add_vehicle_color.sql`
- 이미 적용된 파일은 수정하지 않습니다. 내용이 바뀌면 체크섬 불일치로 서버가 시작되지 않습니다.
- `V2__create_company_sample.sql`은 기존 종목 API 예제용 `company` 테이블과 샘플 데이터입니다.
- `V3__seed_vehicles.sql`은 현대·기아 제조사와 공식 가격표 기반 차량 14건을 추가합니다.
- `V5__add_vehicle_specs_and_seed_domestic.sql`은 차량 제원 컬럼을 추가하고 국내 제조사 트림 244건을 넣습니다.
- 로컬 Docker DB를 처음 상태로 되돌리려면 저장소 루트에서 `./dev.sh reset`을 실행합니다.

## ERD 반영

단일 식별 PK는 AUTO_INCREMENT, 입력 하위 1:1 테이블은 snapshot_id 공유 PK, 관심 차량은 (user_id, vehicle_id) 복합 PK입니다. email, 제조사명, 모델 버전, 분석별 추천 차량 및 추천 순서의 UNIQUE를 반영했습니다. FK 인덱스는 InnoDB가 생성합니다.

## 명시되지 않은 부분의 가정

- 식별자와 필수 연결은 NOT NULL, 대부분 입력 및 계산 결과는 NULL 허용. 초안과 처리 중 결과를 보존합니다.
- 비회원 입력은 input_snapshots.user_id=NULL. 회원 비밀번호는 NOT NULL이며 비회원 users 행은 만들지 않습니다.
- users의 `not_member / Field / Type` 행은 자료형과 물리명이 없는 미완성 항목으로 판단하여 제외했습니다.
- 삭제/수정 참조 정책은 MySQL 기본 RESTRICT이며 이력 삭제를 전파하지 않습니다.
- 생성 시각은 CURRENT_TIMESTAMP, 수정 시각은 ON UPDATE CURRENT_TIMESTAMP를 사용합니다.
- role/status/code 값 목록, 금액/신용점수 범위, 배열 JSON 구조는 정의되지 않아 임의 CHECK를 추가하지 않았습니다.
- purchase_plans 소유자와 연결된 입력 소유자가 같은지는 서비스에서 검증해야 합니다. 단순 FK만으로는 보장되지 않습니다.
- 이전 snapshot 연결도 같은 소유자인지, 순환하지 않는지 서비스 검증이 필요합니다.

V1은 테이블 구조만 제공합니다. 기존 종목 API를 차량 분석 API로 전환하는 작업은 포함하지 않습니다.

## 차량 기본 데이터

V3은 아반떼 하이브리드 5개, 모닝 4개, 레이 4개, K5 1개 트림을 추가합니다. 서버를 재시작하면 기존 DB에도 한 번 적용됩니다. 제조사 ID를 조회해 연결하고 동일 제조사·차명·트림·연식·신차 상태·연료의 기존 행은 건너뜁니다. 기존 행을 갱신하지 않습니다.

2026-10-13에 확인한 제조사 공식 가격표의 스냅샷이며 실매물이 아니므로 `is_example=TRUE`입니다. 가격은 원 단위의 옵션 없는 기본 판매가(하이브리드는 세제혜택 후)이며 취득세·등록비·탁송료는 제외합니다. 연비는 기본 휠 크기, 빌트인 캠 미선택 기준의 복합연비(`km/L`)입니다. 휠 크기는 `trim_name`에 명시합니다. V3의 이미지 주소는 NULL이며 V4에서 공식 사이트의 모델 대표 이미지 URL을 채웁니다. 레이와 K5의 연식은 확인 자료에 명시되지 않아 NULL로 둡니다. 모닝의 2027년형은 [공식 출시 안내](https://www.hyundaimotorgroup.com/ko/news/kia-2027-morning-launch)에서 확인했습니다.

| 모델 | 가격·연비 출처 |
| --- | --- |
| 아반떼 하이브리드 (2026년형) | [현대 공식 가격표](https://www.hyundai.com/contents/repn-car/catalog/avante-hybrid-2026-price.pdf) |
| 모닝 | [기아 공식 가격표](https://www.kia.com/content/dam/kwp/kr/ko/vehicles/pdf/price/price_morning.pdf) |
| 레이 | [기아 공식 가격표](https://www.kia.com/content/dam/kwp/kr/ko/vehicles/pdf/price/price_ray.pdf) |
| K5 | [기아 공식 가격표](https://www.kia.com/content/dam/kwp/kr/ko/vehicles/pdf/price/price_k5.pdf) |

각 행에 `source_name`, `source_url`을 보관합니다. 출처 URL의 내용은 이후 바뀔 수 있습니다. 가격·사양을 갱신할 때는 기존 V3을 편집하지 말고 새 마이그레이션을 추가합니다.

시드에서 사용하는 코드: `condition_code=NEW`(신차), `class_code=MINI/COMPACT_SEDAN/MIDSIZE_SEDAN`(경차/준중형 세단/중형 세단), `fuel_code=GASOLINE/HYBRID`(가솔린/하이브리드). 이는 이번 시드의 코드 규약이며 V1의 DB 제약으로 강제하지 않습니다.

`GET /api/v1/vehicles`는 제조사를 조인한 DB 차량 전체 목록을 가격·ID 오름차순으로 반환합니다. 응답은 `{ "success": true, "data": [...], "meta": null, "error": null }`이며 각 차량은 DB 필드의 camelCase 이름과 `brand`(제조사명)를 포함합니다. `price`는 원, `efficiencyValue`는 `efficiencyUnit` 기준입니다. 조회 실패는 HTTP 500과 `application/problem+json`으로 응답합니다.

프론트엔드는 이 API를 한 번 조회해 검색·상세·비교·시뮬레이션에서 공유하며, 원을 만 원으로 변환하고 ID를 문자열로 사용합니다. 기존 정적 차량 목록은 제거했습니다. 현재 비용 계산이 가솔린 단가를 사용하므로 가솔린·하이브리드 중 양수 가격과 `km/L` 연비가 있는 차량만 화면에서 제공합니다. 전기차·LPG 등은 연료별 비용 계산 지원 후 연결해야 합니다. 로딩·오류(재시도)·빈 목록을 구분하며 API 실패 시 정적 데이터로 대체하지 않습니다. 개발 중에는 Vite의 `/api` 프록시가 백엔드 8080 포트로 전달하고, 배포 환경에서는 동일 경로를 백엔드로 라우팅해야 합니다.

## 차량 이미지

`V4__add_vehicle_image_urls.sql`은 기존 시드의 비어 있는 `image_url`에 공식 제조사 이미지 주소를 추가합니다. 이미지는 다운로드하거나 저장소에 추가하지 않고 브라우저에서 URL로 표시합니다. 목록·상세·비교 화면이 API의 `imageUrl`을 사용하며 로딩 실패 시 일러스트로 대체합니다. 같은 모델의 트림은 대표 이미지를 공유하므로 실제 트림·연식·색상과 차이가 있을 수 있습니다.

주소 확인 페이지: [모닝](https://www.kia.com/kr/vehicles/morning/features), [레이](https://www.kia.com/kr/vehicles/ray/features), [K5](https://www.kia.com/kr/vehicles/k5/features), [아반떼 하이브리드](https://org1.hyundai.com/kr/ko/brand/brandstory/heritage/2023-the-new-avante-hybrid).

## 국내 차종 확장

`V5__add_vehicle_specs_and_seed_domestic.sql`은 `vehicles`에 아래 컬럼을 추가합니다. 기존 14건은 이 값을 NULL로 둡니다.

| 컬럼 | 의미 |
| --- | --- |
| `powertrain` | 엔진·파워트레인. 같은 트림의 배기량·엔진을 구분하며 중복 판정에 포함합니다. |
| `displacement_cc` | 배기량(cc). 연비 사양이 연결된 행만 채웁니다. |
| `city_efficiency`, `highway_efficiency` | 도심·고속도로 연비 또는 전비. 단위는 `efficiency_unit`을 공유합니다. |
| `wheel_size_inch` | 연비와 가격이 기준한 기본 휠 크기(인치) |
| `price_before_incentive` | 세제혜택 전 가격(원). 판매가와 다를 때만 저장합니다. |

시드 기준은 2026-10-14에 확인한 국내 제조사 가격표와 연비표를 트림 단위로 맞춘 자료입니다. 그 원본 CSV는 V5에 반영한 뒤 저장소에서 제거했습니다. 판매가격과 연료 코드가 있는 트림 244건을 넣습니다. 같은 제조사·모델·트림·연식·연료·파워트레인에서 가격만 다른 행은 연비가 연결된 행을 우선하고, 그래도 같으면 더 낮은 기본가 한 건만 남깁니다. 판매가가 없거나 연료가 비어 있는 행은 제외합니다.

기존 V3과 겹치는 표기는 다시 넣지 않습니다. 모닝은 CSV 가격이 공식 시드와 달라 모델 전체를 제외합니다. 레이는 기존과 같은 가격 4트림을 제외합니다. K5는 프레스티지 1.6 터보 29,730,000원만 제외하고 나머지 트림을 추가합니다. 아반떼 하이브리드는 CSV에 판매가가 없어 기존 5트림만 유지합니다. 제조사는 제네시스, 르노코리아, KG모빌리티, 쉐보레를 없으면 추가합니다. `condition_code=NEW`, `is_example=TRUE`이며 이미지 주소는 만들지 않습니다. 동일 제조사·차명·트림·파워트레인·연식·신차·연료가 있으면 건너뜁니다.

`price`는 표시 판매가입니다. 가격 기준이 세제혜택 후인 행은 혜택이 반영된 금액입니다. 차급은 CSV에 없어 모델 기준으로 부여하며 DB CHECK로 강제하지 않습니다.

| 차급 코드 | 모델 |
| --- | --- |
| `MINI` | 레이 EV |
| `SUBCOMPACT_SUV` | 베뉴, 코나 계열, 셀토스, 니로, 티볼리, 트랙스 크로스오버, 트레일블레이저, 아르카나, EV3, GV60 |
| `COMPACT_SEDAN` | 디 올 뉴 아반떼, 디 올 뉴 아반떼 Hybrid |
| `COMPACT_SUV` | 투싼 계열, 스포티지, 토레스 계열, 액티언 계열, EV4, 넥쏘, GV70, Electrified GV70 |
| `MIDSIZE_SEDAN` | K5, 쏘나타 디 엣지 계열, G70, 더 뉴 아이오닉 6 |
| `MIDSIZE_SUV` | 싼타페 계열, 쏘렌토, 그랑 콜레오스, 아이오닉 5, EV5, EV6, GV80 계열, 렉스턴 뉴 아레나 |
| `LARGE_SUV` | 팰리세이드 계열, EV9, 아이오닉 9 |
| `FULLSIZE_SEDAN` | 그랜저 계열, K8, K9, G80, G90, Electrified G80 |
| `MPV` | 카니발 계열, 스타리아 계열, 필랑트 |

목록 API는 새 컬럼을 `powertrain`, `displacementCc`, `priceBeforeIncentive`, `cityEfficiency`, `highwayEfficiency`, `wheelSizeInch`로 함께 반환합니다. 화면은 가솔린·하이브리드이면서 양수 가격과 `km/L` 복합연비가 있는 차만 보여 주므로, 전기·LPG·수소·디젤과 연비가 없는 트림은 DB에만 있습니다. 카드 트림 문구에는 파워트레인을 붙이고, 상세에는 값이 있을 때만 혜택 전 가격, 배기량, 도심·고속도로 연비를 표시합니다.
