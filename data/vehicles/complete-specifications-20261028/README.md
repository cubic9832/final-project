# 전체 차량 제원 보완 — 2026-10-28

107개 모델군, 323개 사양에 공통 주요 정보 28개를 채웠다. `vehicles.csv`는 사양당 한 행이며 각 항목에 값·상태·근거 열이 있다. `vehicles.json`에는 항목별 출처와 조건도 보관한다. `completion-report.json`은 항목별 상태 개수와 입출력 해시다.

- 전장: 기존 원장 287개 + 공식 상세 자료 17개 + 합성 추정 19개.
- 0–100km/h: 공식 공개 38개 + 합성 추정 285개.
- 외관 비례·윤곽: 전체 대표 모델 사진의 주관적 3단계 평가.
- 실내·승차감: 전체 중립 0.5 합성 가정. 실차 평가나 사진 확인 결과가 아니다. 이 두 항목은 현재 UI의 직접 선택/학습 축에 추가하지 않았다.

항목 상태는 `catalog-reference`(기존 원장의 검증 상태 그대로), `official-reference`(제조사 공개 자료), `visual-review`(사진 서열 평가), `estimated`(합성 가정)로 구분한다. 제조사 원문 조건·지역·연식 차이는 그대로 남긴다. 추정은 난수가 아니며 선언한 차체·연료별 기본값과 식별 가능한 제원에 기반한다. 측정·통계로 검증한 예측은 아니다. 비용 추정은 실제 보험 견적이나 세법 계산 결과가 아니다.

공식 가속 수치는 유지한다. 출력이 공개되었지만 가속이 없는 사양은 `1.3 + 0.593 × 중량kg / 출력kW`라는 검증 전 합성 가정을 사용한다. 중량이 미공개이면 차체별 중량 가정을 명시한다. 공개 건조중량을 공차중량으로 바꾸어 표기하지 않는다. 이외 가속 추정은 차체·연료 기본값과 식별 가능한 배기량·공차중량 보정을 사용하며 가격·브랜드·외관 점수를 입력으로 쓰지 않는다.

공통 정보는 전장·전폭·전고·휠베이스·정원·공차중량·배기량·출력·토크·최고속도·적재량·지상고·연료·효율·효율단위·가격·연식·차체형태·변속기·구동·월보험료·월세금·월정비비·가속·외관비례·윤곽·실내단순함·승차감이다. 이 스키마의 9,044개 값에는 빈 값이 없다. 출처 URL, 미확인 연식의 원본 식별자, 선택 장비·충돌 기록 등 근거/선택적 메타데이터는 가짜 값으로 채우지 않는다.

원본 재무 카탈로그를 덮어쓰지 않는다. 추정 정원·전장·가격은 필수 탑승 인원 확인이나 구매 적격의 공식 증거로 승격하지 않는다. 취향 비교용 정원·전장 파생값은 추정 상태로 포함한다. 원본 연식이 비어 있어도 원본 매칭 키를 유지하고 표시용 연식 추정만 별도 저장한다.

```powershell
$env:PYTHONPATH='ml'
python -m tools.data.vehicles.build_full_vehicle_traits
python -m tools.data.vehicles.complete_vehicle_specifications
python -m tools.data.households.generate_preference_cohorts --traits data/vehicles/complete-specifications-20261028/vehicle_traits.json --output data/households/synthetic/preference-cohorts-complete-v2-20261028
python -m vehicle_matching.train_preference_cohorts --data data/households/synthetic/preference-cohorts-complete-v2-20261028 --output ml/outputs/models/preference-cohorts/20261028-v4-complete
```

생성기 출력 데이터는 922개 비교군·2,766개 선호 프로필·794,358개 후보 평가 행이다. 학습 결과는 `ml/outputs/models/preference-cohorts/20261028-v4-complete/training_report.json`에 보관한다. 합성 규칙 재현 지표이며 실제 사람의 취향 정확도를 의미하지 않는다. 기존 출력 폴더가 있으면 새 버전 경로를 지정해 재학습한다.
