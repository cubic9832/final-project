# 실제 DB 스키마

`src/main/resources/db/migration/V1__create_schema.sql`은 제공된 CreditCompass Auto ERD의 15개 테이블을 MySQL 8.0용으로 작성한 파일입니다.

## 적용

스키마는 [Flyway](https://documentation.red-gate.com/fd)로 버전 관리합니다. Spring Boot를 시작하면 `application.yml`의 datasource DB(`final_sample`)에 `db/migration`의 SQL이 버전 순서대로 자동 적용되고, 적용 이력은 `flyway_schema_history` 테이블에 기록됩니다. 수동으로 실행할 필요가 없습니다.

- 스키마를 변경할 때는 `V{다음 번호}__{설명}.sql` 파일을 추가합니다. 예: `V3__add_vehicle_color.sql`
- 이미 적용된 파일은 수정하지 않습니다. 내용이 바뀌면 체크섬 불일치로 서버가 시작되지 않습니다.
- `V2__create_company_sample.sql`은 기존 종목 API 예제용 `company` 테이블과 샘플 데이터입니다.
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
