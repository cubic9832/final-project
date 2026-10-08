-- CreditCompass Auto / MySQL 8.0 / utf8mb4
-- Run in an explicitly selected NEW database: USE your_database;
-- This script neither creates accounts nor changes the example final_sample DB.
-- ERD assumptions: required identifiers/FKs are NOT NULL; optional inputs/results are NULL.
-- No cascading deletes: history is retained via RESTRICT. Timestamps use CURRENT_TIMESTAMP.
-- users.not_member has no physical name/type in the ERD and is intentionally omitted.
-- Currency amounts are KRW; interest rates are percentages. Code vocabularies are not specified.

-- 회원 계정
CREATE TABLE users (
 -- 고유 식별자 (자동 증가 기본키)
 id BIGINT NOT NULL AUTO_INCREMENT PRIMARY KEY,
 -- 로그인 이메일
 email VARCHAR(255) NOT NULL,
 -- 비밀번호 해시값
 password_hash VARCHAR(255) NOT NULL,
 -- 회원 닉네임
 nick_name VARCHAR(50),
 -- 회원 역할 코드
 role VARCHAR(20) NOT NULL,
 -- 생성 시각 (현재 시각 자동 기록)
 created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
 -- 수정 시각 (변경 시 자동 갱신)
 updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
 -- 중복 방지: email 조합은 유일해야 함
 UNIQUE KEY uq_users_email (email)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 분석 입력 버전 이력
CREATE TABLE input_snapshots (
 -- 분석 입력 버전 ID
 snapshot_id BIGINT NOT NULL AUTO_INCREMENT PRIMARY KEY,
 -- 소유 회원 ID (입력 스냅샷에서는 비회원이면 NULL)
 user_id BIGINT NULL,
 -- 수정 전 입력 버전 ID (최초 입력이면 NULL)
 previous_snapshot_id BIGINT NULL,
 -- 처리 상태 코드 (값 목록은 별도 정의)
 status_code VARCHAR(20) NOT NULL,
 -- 예시 데이터 여부
 is_example BOOLEAN NOT NULL DEFAULT FALSE,
 -- 생성 시각 (현재 시각 자동 기록)
 created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
 -- 최종 입력 제출 시각
 submitted_at DATETIME NULL,
 -- 외래키: user_id → users.id 참조
 CONSTRAINT fk_snapshots_user FOREIGN KEY (user_id) REFERENCES users(id),
 -- 외래키: previous_snapshot_id → input_snapshots.snapshot_id 참조
 CONSTRAINT fk_snapshots_previous FOREIGN KEY (previous_snapshot_id) REFERENCES input_snapshots(snapshot_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 소득·지출·자산 입력
CREATE TABLE financial_profiles (
 -- 분석 입력 버전 ID
 snapshot_id BIGINT NOT NULL PRIMARY KEY,
 -- 월 실수령 소득 (원)
 monthly_net_income DECIMAL(15,2),
 -- 기타 월 정기소득 (원)
 monthly_other_income DECIMAL(15,2),
 -- 월 주거비 (원)
 monthly_housing_cost DECIMAL(15,2),
 -- 주거비 제외 월 고정지출 (원)
 monthly_fixed_expense DECIMAL(15,2),
 -- 월 생활비 (원)
 monthly_living_expense DECIMAL(15,2),
 -- 월 목표 저축액 (원)
 monthly_saving_goal DECIMAL(15,2),
 -- 보유 현금 및 예금 (원)
 available_cash DECIMAL(15,2),
 -- 차량 구매 예정 선수금 (원)
 planned_down_payment DECIMAL(15,2),
 -- 유지할 비상자금 (원)
 emergency_fund DECIMAL(15,2),
 -- 외래키: snapshot_id → input_snapshots.snapshot_id 참조
 CONSTRAINT fk_financial_snapshot FOREIGN KEY (snapshot_id) REFERENCES input_snapshots(snapshot_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 여러 건의 기존 대출
CREATE TABLE loan_inputs (
 -- 개별 기존 대출 입력 ID
 loan_input_id BIGINT NOT NULL AUTO_INCREMENT PRIMARY KEY,
 -- 분석 입력 버전 ID
 snapshot_id BIGINT NOT NULL,
 -- 대출 종류 코드
 loan_type_code VARCHAR(30),
 -- 대출 잔액 (원)
 balance_amount DECIMAL(15,2),
 -- 연 이자율 (퍼센트)
 annual_interest_rate DECIMAL(7,4),
 -- 기존 대출 월 상환액 (원)
 monthly_repayment DECIMAL(15,2),
 -- 남은 상환 기간 (개월)
 remaining_months INT,
 -- 대출 시작일
 start_date DATE,
 -- 외래키: snapshot_id → input_snapshots.snapshot_id 참조
 CONSTRAINT fk_loans_snapshot FOREIGN KEY (snapshot_id) REFERENCES input_snapshots(snapshot_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 신용거래 및 연체 입력
CREATE TABLE credit_profiles (
 -- 분석 입력 버전 ID
 snapshot_id BIGINT NOT NULL PRIMARY KEY,
 -- 현재 연체 여부 (모르면 NULL)
 has_current_overdue BOOLEAN NULL,
 -- 현재 연체 금액 (원)
 current_overdue_amount DECIMAL(15,2),
 -- 현재 연체 지속 기간 (일)
 current_overdue_days INT,
 -- 최근 1년 연체 횟수
 overdue_count_last_year INT,
 -- 가장 최근 연체 시점
 latest_overdue_date DATE,
 -- 최근 6개월 신규 대출 수
 new_loan_count_six_months INT,
 -- 사용자가 입력한 보유 대출 수
 reported_loan_count INT,
 -- 보유 신용카드 수
 credit_card_count INT,
 -- 최근 6개월 신규 신용카드 수
 new_card_count_six_months INT,
 -- 최초 신용거래 시작일
 first_credit_date DATE,
 -- NICE 신용점수
 nice_score INT,
 -- KCB 신용점수
 kcb_score INT,
 -- 외래키: snapshot_id → input_snapshots.snapshot_id 참조
 CONSTRAINT fk_credit_snapshot FOREIGN KEY (snapshot_id) REFERENCES input_snapshots(snapshot_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 차량 이용 조건
CREATE TABLE vehicle_preferences (
 -- 분석 입력 버전 ID
 snapshot_id BIGINT NOT NULL PRIMARY KEY,
 -- 차량 구매 목적 목록 (JSON)
 purchase_purposes JSON,
 -- 희망 차량 상태 코드 (신차·중고차 등)
 vehicle_condition_code VARCHAR(20),
 -- 선호 차급 목록 (JSON)
 preferred_classes JSON,
 -- 선호 연료 목록 (JSON)
 preferred_fuels JSON,
 -- 주 탑승 인원 수
 passenger_count INT,
 -- 연간 예상 주행거리 (km)
 annual_mileage_km INT,
 -- 주 운행 도로 종류 코드
 road_type_code VARCHAR(20),
 -- 충전 가능 여부 (모르면 NULL)
 charging_available BOOLEAN NULL,
 -- 희망 할부 기간 (개월)
 desired_installment_months INT,
 -- 차량 선택 우선순위 목록 (JSON)
 priority_order JSON,
 -- 외래키: snapshot_id → input_snapshots.snapshot_id 참조
 CONSTRAINT fk_preferences_snapshot FOREIGN KEY (snapshot_id) REFERENCES input_snapshots(snapshot_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 차량 제조사
CREATE TABLE brands (
 -- 고유 식별자 (자동 증가 기본키)
 id BIGINT NOT NULL AUTO_INCREMENT PRIMARY KEY,
 -- 제조사 이름
 name VARCHAR(60) NOT NULL,
 -- 생성 시각 (현재 시각 자동 기록)
 created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
 -- 중복 방지: name 조합은 유일해야 함
 UNIQUE KEY uq_brands_name (name)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 추천 대상 차량 정보
CREATE TABLE vehicles (
 -- 고유 식별자 (자동 증가 기본키)
 id BIGINT NOT NULL AUTO_INCREMENT PRIMARY KEY,
 -- 차량 제조사 ID
 brand_id BIGINT NOT NULL,
 -- 차량 이름
 name VARCHAR(100) NOT NULL,
 -- 차량 트림 이름
 trim_name VARCHAR(100),
 -- 차량 연식
 model_year INT,
 -- 차량 상태 코드
 condition_code VARCHAR(20),
 -- 차급 코드
 class_code VARCHAR(30),
 -- 연료 코드
 fuel_code VARCHAR(30),
 -- 승차 정원
 seating_capacity INT,
 -- 차량 가격 (원)
 price DECIMAL(15,2),
 -- 연비 또는 전비 수치
 efficiency_value DECIMAL(10,3),
 -- 연비 또는 전비 단위
 efficiency_unit VARCHAR(20),
 -- 차량 이미지 주소
 image_url VARCHAR(500),
 -- 차량 정보 출처 이름
 source_name VARCHAR(100),
 -- 차량 정보 출처 링크
 source_url VARCHAR(500),
 -- 예시 데이터 여부
 is_example BOOLEAN NOT NULL DEFAULT FALSE,
 -- 수정 시각 (변경 시 자동 갱신)
 updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
 -- 외래키: brand_id → brands.id 참조
 CONSTRAINT fk_vehicles_brand FOREIGN KEY (brand_id) REFERENCES brands(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 회원 관심 차량
CREATE TABLE favorite_vehicles (
 -- 소유 회원 ID (입력 스냅샷에서는 비회원이면 NULL)
 user_id BIGINT NOT NULL,
 -- 연결된 차량 ID
 vehicle_id BIGINT NOT NULL,
 -- 생성 시각 (현재 시각 자동 기록)
 created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
 -- 복합 기본키: 같은 회원의 동일 차량 중복 저장 방지
 PRIMARY KEY (user_id, vehicle_id),
 -- 외래키: user_id → users.id 참조
 CONSTRAINT fk_favorites_user FOREIGN KEY (user_id) REFERENCES users(id),
 -- 외래키: vehicle_id → vehicles.id 참조
 CONSTRAINT fk_favorites_vehicle FOREIGN KEY (vehicle_id) REFERENCES vehicles(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 분석 모형 버전
CREATE TABLE model_versions (
 -- 분석 모형 버전 ID
 model_version_id BIGINT NOT NULL AUTO_INCREMENT PRIMARY KEY,
 -- 분석 모형 또는 규칙 이름
 model_name VARCHAR(100) NOT NULL,
 -- 모형 버전 이름
 version_label VARCHAR(50) NOT NULL,
 -- 분석 실행 방식 코드 (MOCK·RULE·ML 등)
 execution_type VARCHAR(20) NOT NULL,
 -- 모형 또는 규칙 설명
 description TEXT,
 -- 생성 시각 (현재 시각 자동 기록)
 created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
 -- 중복 방지: model_name, version_label 조합은 유일해야 함
 UNIQUE KEY uq_model_version (model_name, version_label)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 분석 실행 결과 이력
CREATE TABLE analysis_runs (
 -- 분석 실행 ID
 analysis_id BIGINT NOT NULL AUTO_INCREMENT PRIMARY KEY,
 -- 분석 입력 버전 ID
 snapshot_id BIGINT NOT NULL,
 -- 분석 모형 버전 ID
 model_version_id BIGINT NOT NULL,
 -- 처리 상태 코드 (값 목록은 별도 정의)
 status_code VARCHAR(20) NOT NULL,
 -- 분석에서 계산한 월 가용자금 (원)
 monthly_available_amount DECIMAL(15,2),
 -- 자체 위험 점수 (실제 신용점수와 별개)
 risk_score DECIMAL(8,4),
 -- 자체 위험 또는 부담 등급 코드
 risk_grade_code VARCHAR(30),
 -- 권장 차량 가격 하한 (원)
 recommended_price_min DECIMAL(15,2),
 -- 권장 차량 가격 상한 (원)
 recommended_price_max DECIMAL(15,2),
 -- 권장 월 자동차 총비용 (원)
 recommended_monthly_car_cost DECIMAL(15,2),
 -- 분석 실패 코드
 error_code VARCHAR(50),
 -- 분석 요청 시각
 requested_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
 -- 분석 완료 시각
 completed_at DATETIME,
 -- 외래키: snapshot_id → input_snapshots.snapshot_id 참조
 CONSTRAINT fk_analysis_snapshot FOREIGN KEY (snapshot_id) REFERENCES input_snapshots(snapshot_id),
 -- 외래키: model_version_id → model_versions.model_version_id 참조
 CONSTRAINT fk_analysis_model FOREIGN KEY (model_version_id) REFERENCES model_versions(model_version_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 분석 근거와 개선 안내
CREATE TABLE analysis_factors (
 -- 분석 근거 ID
 factor_id BIGINT NOT NULL AUTO_INCREMENT PRIMARY KEY,
 -- 분석 실행 ID
 analysis_id BIGINT NOT NULL,
 -- 영향 요인 코드
 factor_code VARCHAR(50),
 -- 영향 방향 코드 (긍정·주의 등)
 direction_code VARCHAR(20),
 -- 요인이 분석 결과에 기여한 값
 contribution_value DECIMAL(10,4),
 -- 사용자가 읽을 분석 근거 설명
 explanation TEXT,
 -- 사용자에게 권장하는 다음 행동
 suggested_action TEXT,
 -- 분석 근거 표시 순서
 display_order INT,
 -- 외래키: analysis_id → analysis_runs.analysis_id 참조
 CONSTRAINT fk_factors_analysis FOREIGN KEY (analysis_id) REFERENCES analysis_runs(analysis_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 분석별 추천 차량 결과
CREATE TABLE recommendations (
 -- 추천 결과 ID
 recommendation_id BIGINT NOT NULL AUTO_INCREMENT PRIMARY KEY,
 -- 분석 실행 ID
 analysis_id BIGINT NOT NULL,
 -- 연결된 차량 ID
 vehicle_id BIGINT NOT NULL,
 -- 분석 내 추천 순위
 rank_order INT NOT NULL,
 -- 차량 추천 점수
 recommendation_score DECIMAL(10,4),
 -- 차량 추천 이유
 reason_text TEXT,
 -- 추천 또는 계산 당시 차량 가격 (원, 이후 변경과 무관하게 보존)
 vehicle_price_snapshot DECIMAL(15,2),
 -- 예상 월 할부금 (원)
 estimated_monthly_installment DECIMAL(15,2),
 -- 예상 월 유지비 (원)
 estimated_monthly_running_cost DECIMAL(15,2),
 -- 비용 계산 가정과 출처 (JSON)
 assumptions_json JSON,
 -- 중복 방지: analysis_id, vehicle_id 조합은 유일해야 함
 UNIQUE KEY uq_recommendation_vehicle (analysis_id, vehicle_id),
 -- 중복 방지: analysis_id, rank_order 조합은 유일해야 함
 UNIQUE KEY uq_recommendation_rank (analysis_id, rank_order),
 -- 외래키: analysis_id → analysis_runs.analysis_id 참조
 CONSTRAINT fk_recommendations_analysis FOREIGN KEY (analysis_id) REFERENCES analysis_runs(analysis_id),
 -- 외래키: vehicle_id → vehicles.id 참조
 CONSTRAINT fk_recommendations_vehicle FOREIGN KEY (vehicle_id) REFERENCES vehicles(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 구매 조건별 비용 계산
CREATE TABLE simulations (
 -- 구매 조건 시뮬레이션 ID
 simulation_id BIGINT NOT NULL AUTO_INCREMENT PRIMARY KEY,
 -- 분석 실행 ID
 analysis_id BIGINT NOT NULL,
 -- 연결된 차량 ID
 vehicle_id BIGINT NOT NULL,
 -- 추천 또는 계산 당시 차량 가격 (원, 이후 변경과 무관하게 보존)
 vehicle_price_snapshot DECIMAL(15,2),
 -- 시뮬레이션 선수금 (원)
 down_payment_amount DECIMAL(15,2),
 -- 할부 기간 (개월)
 installment_months INT,
 -- 연 이자율 (퍼센트)
 annual_interest_rate DECIMAL(7,4),
 -- 연간 예상 주행거리 (km)
 annual_mileage_km INT,
 -- 계산된 월 할부금 (원)
 monthly_installment DECIMAL(15,2),
 -- 할부 기간 총 이자 (원)
 total_interest_amount DECIMAL(15,2),
 -- 월 연료비 (원)
 monthly_fuel_cost DECIMAL(15,2),
 -- 월 보험료 (원)
 monthly_insurance_cost DECIMAL(15,2),
 -- 월 자동차세 (원)
 monthly_tax_cost DECIMAL(15,2),
 -- 월 정비비 (원)
 monthly_maintenance_cost DECIMAL(15,2),
 -- 월 주차비 (원)
 monthly_parking_cost DECIMAL(15,2),
 -- 월 자동차 총비용 (원)
 monthly_total_car_cost DECIMAL(15,2),
 -- 구매 후 남는 월 가용자금 (원)
 remaining_monthly_available DECIMAL(15,2),
 -- 자체 위험 또는 부담 등급 코드
 risk_grade_code VARCHAR(30),
 -- 시뮬레이션 계산 규칙 버전
 calculation_version VARCHAR(50),
 -- 비용 계산 가정과 출처 (JSON)
 assumptions_json JSON,
 -- 생성 시각 (현재 시각 자동 기록)
 created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
 -- 외래키: analysis_id → analysis_runs.analysis_id 참조
 CONSTRAINT fk_simulations_analysis FOREIGN KEY (analysis_id) REFERENCES analysis_runs(analysis_id),
 -- 외래키: vehicle_id → vehicles.id 참조
 CONSTRAINT fk_simulations_vehicle FOREIGN KEY (vehicle_id) REFERENCES vehicles(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 저장한 구매 계획
CREATE TABLE purchase_plans (
 -- 저장한 구매 계획 ID
 plan_id BIGINT NOT NULL AUTO_INCREMENT PRIMARY KEY,
 -- 소유 회원 ID (입력 스냅샷에서는 비회원이면 NULL)
 user_id BIGINT NOT NULL,
 -- 구매 조건 시뮬레이션 ID
 simulation_id BIGINT NOT NULL,
 -- 구매 계획 이름
 plan_name VARCHAR(100),
 -- 목표 선수금 (원)
 target_down_payment DECIMAL(15,2),
 -- 현재 준비금 (원)
 current_funds DECIMAL(15,2),
 -- 구매 계획 월 목표 저축액 (원)
 monthly_saving_target DECIMAL(15,2),
 -- 예상 구매일
 expected_purchase_date DATE,
 -- 부채 우선 상환 계획 메모
 debt_repayment_notes TEXT,
 -- 처리 상태 코드 (값 목록은 별도 정의)
 status_code VARCHAR(20) NOT NULL,
 -- 생성 시각 (현재 시각 자동 기록)
 created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
 -- 수정 시각 (변경 시 자동 갱신)
 updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
 -- 외래키: user_id → users.id 참조
 CONSTRAINT fk_plans_user FOREIGN KEY (user_id) REFERENCES users(id),
 -- 외래키: simulation_id → simulations.simulation_id 참조
 CONSTRAINT fk_plans_simulation FOREIGN KEY (simulation_id) REFERENCES simulations(simulation_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Application validation required by ERD:
-- purchase_plans.user_id must equal the user owning its simulation's analysis snapshot.
-- Editing input creates a new snapshot; re-analysis creates a new analysis_run;
-- changing purchase conditions creates a new simulation. No financial eligibility rules assumed.

