# 실제 DB 스키마

`schema.sql`은 제공된 CreditCompass Auto ERD의 15개 테이블을 MySQL 8.0용으로 작성한 파일입니다.

## 적용

MySQL Workbench에서 새 DB를 생성하고 `USE 새_DB명;`으로 선택한 뒤 `schema.sql`을 실행합니다. DB 이름은 아직 확정되지 않았으므로 파일에 고정하지 않았습니다. 기존 `final_sample`과 계정 권한, application.yml은 변경하지 않았습니다. Spring Boot 자동 초기화 파일 위치가 아닌 back/schema.sql에 두어 수동 실행하도록 했습니다.

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

이 SQL은 테이블 구조만 제공합니다. 기존 종목 API를 차량 분석 API로 전환하는 작업이나 실제 DB 적용은 포함하지 않습니다.
