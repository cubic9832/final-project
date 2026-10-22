# 합성 개인·가구 재무 데이터

계획에 따라 일반 프로필 10,000개와 별도 경계 사례 60개를 생성한다. 각 프로필마다 국내 신차 시나리오 3개가 연결된다. 전체 개인 재무 정보는 합성이다. 실제 사람의 기록·대출 승인·연체 결과는 포함하지 않는다.

## 사용 파일

한국어 버전은 `generated/csv-ko/`에 저장한다. 컬럼명과 분류 값을 번역했으며 식별자·금액·비율·출처 URL은 원본과 동일하다. 예/아니오는 참/거짓에 대응한다. 연금리 0.06은 6%이며 비율을 퍼센트 숫자로 변환하지 않았다. 한국어 CSV는 `exportSyntheticCsv.mjs --korean`으로 재생성한다. 열·값의 대응표는 `korean_labels.json`에 기록한다. 트림 등 제조사의 고유 사양 이름은 유지한다.

`generated/csv/`의 profiles, expenses, loans, vehicle_scenarios, simulation_results를 profile_id로 연결한다. 시나리오와 결과는 scenario_id로 일대일 연결한다. 일반 프로필은 train/validation/test 70/15/15, 추가 60개는 edge_test다. 같은 프로필의 시나리오는 같은 split에 속한다. 결측은 빈 칸, 모든 `_won` 금액은 원이며 월/연 기간은 필드명에 명시한다. 금리 필드는 비율(0.06 = 연 6%)이다.

실제 차량 가격·연비는 기존 공식 자료 추출에서 연결된 사양을 사용한다. 자동 추출 자료이므로 출시 조건·옵션·세제 조건의 추가 검토가 필요하다. 차량 식별자는 기존 JSON 행 순서 기반이며 원본 SHA256은 검증 보고서에 기록한다. 개인·가구 비율, 소득 분산과 관계, 금리·에너지 단가·보험·정비·세금은 `generation_config.json`에 기록한 가정이다. 특히 등록 비용 7%와 연간 세금 적립액은 법정 세액이 아니다.

## 컬럼 사전

- 공통: profile_id 연결 키, budget_scope individual/household 예산 범위, is_synthetic 합성 여부, generator_version 생성 규칙 버전, seed 난수 seed, split 실험 구간.
- profiles: case_type 일반/경계 유형, age_years 나이, employment 취업 형태, household_size 가구원 수, dependents 부양 인원, housing 주거 형태. monthly_net_income_won은 해당 예산 범위의 월 실수령 합계이고 monthly_extra_income_won은 기타 소득. liquid_cash_won은 인출 가능 현금, locked_housing_deposit_won은 묶인 보증금, emergency_target_won은 목표 비상금. income_volatility_assumed는 가정한 변동성 속성으로 시계열 관측치가 아니며 이번 고정 20% 스트레스 계산에 직접 사용하지 않는다.
- expenses: housing/living/phone/transport/fixed/discretionary_won은 각각 월 주거비/생활비/통신비/교통비/보험 포함 기타 고정비/선택 소비. target_savings_won은 목표 월 저축으로 소비와 분리한다. 대출 상환은 이 파일에 포함되지 않는다.
- loans: loan_id·loan_sequence는 대출 식별자, loan_type secured/unsecured/card, balance_won 잔액, annual_rate_assumed 가정 연 금리, remaining_months 남은 기간. repayment_method annuity/equal_principal/bullet는 원리금균등/원금균등/만기일시. monthly_principal_won·monthly_interest_won은 현재 잔액 기준 다음 1개월의 원금·이자다. maturity_lump_sum_won은 만기일시의 만기 원금이며 월 상환액에 포함되지 않는다. 무대출 프로필은 loans 행이 없다.
- vehicle_scenarios: vehicle_id와 brand/model/trim/powertrain/fuel은 차량 사양 식별 정보. vehicle_price_won과 combined_efficiency/efficiency_unit은 실제 추출값. price/efficiency_source_url·page는 출처. down_payment_won 선수금, installment_months 할부 기간(0은 일시불), annual_rate_assumed 금리. annual_distance_km 연 주행거리, energy_price_assumed는 내연기관 원/L·전기 원/kWh. monthly_energy_cost_won은 거리÷연비×단가÷12. insurance/maintenance_annual_assumed_won은 연 보험/정비 가정. registration_cost_assumed_won은 초기 등록 비용, monthly_operating_cost_won은 에너지+보험+정비+세금 적립의 월 합계. monthly_replaced_transport_won은 차 구매로 줄어드는 기존 교통비. vehicle_data_origin/cost_origin은 출처 구분.
- simulation_results: monthly_before_purchase_won은 소득−생활 소비−기존 대출 상환−목표 저축. monthly_vehicle_payment_won은 차량 월 할부액, monthly_after_purchase_won은 구매 전 잔여액−할부−유지비+대체 교통비. income_stress_remaining_won은 소득 20% 감소, rate_stress_remaining_won은 모든 대출·할부 금리 2%p 상승 후 잔여액(각각 독립 스트레스). cash_after_purchase_won은 선수금·등록비 차감 후 현금. cash_runway_months는 그 현금÷구매 후 월 현금 유출이며 저축은 분모에서 제외한다. 부족한 현금은 0개월로 표시하고 음수 잔액은 보존한다. upfront_funding_gap_won은 초기 자금 부족, emergency_shortfall_won은 목표 비상금 부족. budget_exceeded_rule는 월 적자 또는 비상금 미달 여부. label_origin은 관측 결과가 아닌 규칙 산출물임을 표시한다.

일시불 시나리오는 자금이 부족해도 구매 가격 전액을 선수금으로 기록하여 부족액을 노출한다. 할부 시나리오는 등록비·비상금을 제외한 현금 이내로 선수금을 제한한다. 별도 경계 사례의 비중을 실제 인구 비율로 해석하지 않는다. 만기일시 대출의 만기 원금 조달과 미래 월별 상환 스케줄은 이번 한 달 현금흐름 계산 범위 밖이므로 maturity_lump_sum_won을 추가 검토해야 한다.

## 재현 및 검증

생활 수준 요인은 `lognormal(0, 0.22) × (월소득/300만원)^0.3`, 현금은 `월소득 × lognormal(log(5), 1.1)`이다. 소득은 취업 형태별 중앙값의 로그정규분포에 가구원 1명 증가마다 25%를 곱한다. 주거비 기준은 자가 25만원/보증금 임대 40만원/월세 75만원, 생활비 기준은 40만원+추가 가구원당 20만원, 기타 고정비는 18만원+추가 가구원당 8만원이며 생활 수준 요인을 곱한다. 선택 소비는 소득의 4~20%, 목표 저축은 0~25%, 추가 소득은 30% 확률로 본소득의 0~12%다. 대출 보유 시 1~2건이며 종류·상환 방식은 균등 선택이다. 담보대출 기간은 12/24/36/60/120/240개월, 기타는 12/24/36/60개월에서 균등 선택한다. 모두 관측 사실이 아닌 가정이며 일반 데이터의 높은 적자 비중도 실제 인구 추정에 사용하지 않는다.

프런트 화면 단위는 만 원이다. 연결 시 금액을 10,000으로 나눈다. values.income/extraIncome은 profiles의 소득, housing/fixed/transport/phone은 expenses의 대응 열, living은 living_won+discretionary_won, loan은 월 원금·이자 합계, savings는 target_savings_won이다. assets.deposit/emergency/downPayment는 인출 가능 현금/목표 비상금/선수금에 대응한다. 이번 작업은 데이터 생성까지이며 화면의 기존 고정 금리·유지비 계산을 변경하지 않았다.

저장소 루트에서 Python으로 `-m tools.data.households.generate_profiles --count 1000 --output pilot`을 먼저 실행하고, 검증 후 인자 없이 실행하면 10,000개를 생성한다. `python -m unittest discover -s tools/data/households/tests -t .`로 핵심 계산을 검증한다. CSV는 `tools/data/csv/exportSyntheticCsv.mjs`를 Node.js로 실행하여 작성한다.

`generated/validation-report.json`은 행 수, 구간 분할, 재현성, 출처 해시, 회계 검증 결과와 평균을 기록한다. 기존 가구 총소득 평균은 규모 참고로만 보고하며 합성 실수령액과 직접 일치시키지 않는다. 개인 분포나 실제 예측 성능을 검증한 자료가 아니다. 모델을 실험한다면 계산식 기준선과 비교하고 결과 변수·결과 파생값을 입력에 넣지 않아야 한다.
