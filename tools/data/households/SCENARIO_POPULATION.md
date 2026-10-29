# 개별 작성 사례를 확장하는 데이터 생성기

기본 버전은 v3입니다. 기존 30명의 파일럿과 추가 9명, 총 39개 사례를 씨앗으로 사용합니다. 사용자를 먼저 만들고, 그 사용자의 구매·좌석 조건을 통과하는 차량에서 비교 후보를 뽑습니다. 차량 선택 결과에 맞춰 사용자 재무를 역산하지 않습니다.

## v3 일반 취향 추천

`scenario_population_v3_config.json`의 `identity_preferences: false`로 브랜드·개별 모델 선호를 정답 생성에서 제외했습니다. 모든 사용자 preferred_brands는 빈 배열, model_affinities는 빈 객체이며 두 항목의 효용 가중치는 0입니다. 감사 코드가 전체 사용자에서 이 조건을 검사합니다.

선택은 비용·유지비 부담·차체·연료·외부 전장·충전 여건에 따라 결정됩니다. 기존 68개 배열 계약을 유지하기 위해 브랜드/모델 일치도 슬롯은 중립 상수, 중요도 슬롯은 0으로 예약되어 있으며 사용자나 차량의 이름·ID를 이 슬롯에 인코딩하지 않습니다. 기존 v2 가중치를 그대로 사용하지 않고 v3 정답으로 다시 학습합니다.

실행 데이터 경로는 `data/households/synthetic/scenario-population-v3-broad-taste-10k-20261029`, 모델 경로는 `ml/outputs/models/scenario-choices/20261029-v3-broad-taste-10k`입니다. 아래 v2 설명 중 브랜드/모델 호감 혼합은 이전 실험 기록입니다.

## v2 변경

- 고가 전기 SUV 수집가·자산 기반 대형 세단 소유자·고자산 실속형 3명, 작업용/전기/수입 대형 픽업 사용자 3명, 디젤/GTI/하이브리드 해치백 선호자 3명을 추가했습니다.
- `data/vehicles/scenario-seating-20261029/registry.json`을 실험 카탈로그 복사본에만 적용합니다. 6개 모델·14개 사양의 좌석을 보완하며, 국내 공개 제원 참조와 제조사 동일 계열·해외 사양 참조를 구분합니다. `official-source-verified`로 일괄 승격하지 않습니다. 기존 파일럿 카탈로그와 서비스 원장은 수정하지 않습니다.
- `seating_supplements.json`에 변경 전 좌석·적용 값·출처·적용 범위를, `seed_personas.json`에 확장된 39개 씨앗을 남깁니다.
- 적격 모델 중 분할별 노출이 부족한 후보를 우선 선정하고 실제 비교 쌍에 넣습니다. 사용자 조건과 승리 횟수는 바꾸지 않습니다.
- 모델별 최소 비교 등장 횟수는 학습 20회/검증 5회/평가 5회입니다. 전체 사양별로는 합산 1회 이상입니다. 사용자 수가 아니라 A/B 비교에 참여한 횟수입니다.
- 전체 96개 모델·308개 사양의 `coverage_report.json`을 작성합니다. 최소 횟수 미달이면 오류로 종료하며 완료 manifest를 쓰지 않습니다. 부적격 차량을 포함하거나 고정 인원 수를 몰래 늘리지 않습니다.
- 작은 실험은 설정 파일의 최소 횟수를 명시적으로 줄일 수 있습니다.

## 사용

`ml/test` worktree 루트 PowerShell에서 실행합니다.

```powershell
$env:PYTHONPATH = "$PWD/ml;$PWD"
$env:PYTHONIOENCODING = 'utf-8'
$pythonPath = 'C:/workspace/final-project/ml/.venv/Scripts/python.exe'

# 사용자 1만 명, 사용자당 10쌍 = 비교 선택 10만 건
& $pythonPath -m tools.data.households.generate_scenario_population `
  --output data/households/synthetic/scenario-population-v2-10k-20261029 `
  --profiles 10000 --pairs-per-user 10 --shard-size 1000 --seed 20261029

# 저장된 전체 데이터를 다시 읽어 검증
& $pythonPath -m tools.data.households.audit_scenario_population `
  --data data/households/synthetic/scenario-population-v2-10k-20261029
```

100만 명/1천만 비교가 필요하면 `--profiles 1000000`과 새로운 `--output` 경로를 사용합니다. 한 번에 보관하는 특징 배열 크기는 `--shard-size`에 따라 제한됩니다. 사용자·재무 그룹 중복 검사 집합은 전체 사용자 수에 비례합니다. 아직 100만 명 생성의 실행 시간·자원 사용을 측정한 것은 아닙니다.

존재하는 출력 경로는 덮어쓰지 않습니다. 중단한 실행을 이어받는 기능은 없으므로 새 경로에서 다시 실행합니다. 성공 시 manifest가 생성되고, 전체 재검증 통과 시 validation_report.json이 생성됩니다. 같은 코드·입력·환경·seed에서 같은 결과를 만듭니다.

## 생성 순서

1. 작성된 사례 두 명을 뽑습니다. 첫 사례의 생활 목적과 필수 인원을 유지하고, 두 번째 사례의 취향을 일부 혼합합니다.
2. 재무에는 공동 배율과 작은 개별 편차를 주어 소득·지출·자산 간 관계를 유지합니다. 주행거리도 씨앗 사례 주변에서 변형하고 충전 접근성에 작은 변화를 줍니다.
3. 차체·연료·전장 선호, 중요도, 브랜드 선호, 개별 모델 호감을 관측 가능한 사용자 필드로 기록합니다. 원본 사례의 긴 서술문은 복사하지 않고 실제 생성된 조건으로 짧은 상황 설명을 만듭니다.
4. 현금 구매 가능액·구매 상한·유지비·12개월 자산 보전·필수 좌석을 확인합니다. 후보가 부족하면 사용자 설정을 바꾸지 않고 제외 사유를 집계한 뒤 새 사용자를 만듭니다.
5. 서로 다른 모델을 최대 20개 뽑고 모델별 사양 하나를 무작위로 선택합니다. 사양이 많은 차량이 그 이유만으로 더 많이 노출되지 않도록 모델을 먼저 뽑습니다.
6. 무작위 비교, 종합 선호가 가까운 비교, 항목별 장단점이 갈리는 비교, 차체·가격이 유사한 비교를 섞습니다. 후보가 없으면 해당 유형은 일반 비교로 대체합니다.
7. 사용자에게 명시된 중요도로 선택 효용을 계산하고, 작은 확률적 변동을 넣어 A/B를 선택합니다. 중간 계산은 감사 기록에만 저장합니다.
8. 선택에 유리한 항목과 양보한 항목으로 이유를 만듭니다. 효용이 낮은 후보가 뽑힌 경우 확률적 선택이었다고 표시하여 이유를 억지로 꾸미지 않습니다.

## 무엇을 조정할 수 있나

`scenario_population_v3_config.json`을 복사해 `--config`로 지정합니다. 기존 v1/v2 설정은 이전 실험 재현용으로 유지합니다.

| 설정 | 의미 |
| --- | --- |
| financial_log_sigma | 씨앗 주변 재무 변형 폭 |
| distance_log_sigma | 연간 주행거리 변형 폭 |
| secondary_preference_probability | 차체·연료·전장 선호를 두 번째 사례에서 가져올 가능성 |
| secondary_mix_range | 중요도·개별 모델 호감 혼합 비중 |
| temperature_range | 비교 선택의 변동 폭. 낮으면 높은 효용 후보를 일관되게 선택 |
| pool_models | 사용자당 비교 후보 모델 수 |
| pair_modes | 비교 유형과 순서 |
| minimum_buffer | 유지비 지급 후 남겨 두는 월 여유자금 |
| split_fractions | 학습/검증/평가 재무 그룹 분할 비율 |
| seating_registry | 실험 카탈로그에 적용할 좌석 근거 파일 |
| additional_personas | 기존 30개 사례에 추가할 사례 파일 |
| minimum_model_comparisons | 분할별·모델별 최소 비교 등장 횟수 |
| minimum_spec_comparisons | 전체 분할 합산 사양별 최소 비교 등장 횟수 |

씨앗 39개는 동일 확률로 선택됩니다. 적격 후보가 부족한 사용자는 탈락하므로 최종 수락 비율은 사례별로 달라질 수 있습니다. `generation_summary.json`의 시도·제외·사례별 수락·노출·승리 분포로 확인합니다. 씨앗의 개별 모델 호감을 명시적 선호로 확장하므로, 자유로운 서술문 해석을 매 행 수행하는 방식은 아닙니다.

## 모델 입력과 생성 기록

사용자 측 `model_affinities`는 파일럿에 작성된 선호 선택에서 가져온 명시적인 모델 호감도입니다. 브랜드/모델 호감은 `preferred_brands`, `model_affinities`에 저장되며 감사 파일에만 숨겨 두지 않습니다. 신규 선택 결과를 보고 이 필드를 수정하지 않습니다.

`vehicle_matching/scenario_features.py`가 학습·추론에 공통으로 사용할 68개 특징을 정의합니다.

- 기존 52개 재무·차량·선호 특징.
- 자금 보존, 유지비 부담, 차체, 연료, 전장, 브랜드, 모델 호감, 충전 접근성의 8개 평가값.
- 위 8개 항목의 사용자 중요도.

성능·승차감·정숙성·기술 중요도는 사용자 원본에 보관하지만, 대응 차량 특성이 없는 현재 버전에서는 직접 점수화하지 않습니다. 차체나 가격으로 승차감·가속 성능을 만들어 넣지 않습니다. 모델별 디자인 호감은 명시적인 주관적 선호로 반영합니다.

68개 입력에는 label·이유·생성 확률·난수·온도·효용·원본 사례 ID를 넣지 않습니다. 기존 52개 입력 모델과는 별도 계약이며 `scenario_model.ScenarioRanker`가 저장·로딩·추론을 담당합니다. 실행 서버 교체는 별도 작업입니다.

## 모델 학습

```powershell
& $pythonPath -m vehicle_matching.train_scenario_choices `
  --data data/households/synthetic/scenario-population-v2-10k-20261029 `
  --output ml/outputs/models/scenario-choices/20261029-v2-10k `
  --epochs 30 --batch-size 2048 --threads 4 `
  --old-model ml/outputs/models/behavioral-choices/20261028-million-v1
```

68→64→32→1 MLP를 새 가중치로 학습합니다. 정규화는 학습 분할만 사용하고, 검증 log loss가 가장 낮은 epoch를 저장합니다. 저장 모델을 다시 읽어 공통 인코더 추론과 저장 특징의 점수가 일치하는지 확인한 뒤 평가 분할을 측정합니다.

동일한 평가 쌍에서 MLP, 동일 입력 선형 모델, 기존 52개 입력 체크포인트, 선호 우선 규칙, 비용 단독 기준을 비교합니다. 생성 확률 기준은 평가 전용으로 별도 기록합니다. 학습기와 입력에는 생성 확률을 전달하지 않습니다. 모델·정규화·카탈로그 해시와 실행 설정은 `metadata.json`, 전체 학습 이력·지표는 `training_report.json`에 저장합니다.

추론은 `ScenarioRanker.load(모델폴더).score_candidates(user, vehicles)`를 사용합니다. `user`는 생성 JSONL과 같은 profile·preferred_brands·model_affinities·channel_weights 계약입니다. 재무·좌석 부적격 후보를 전달하면 오류를 반환합니다.

## 산출물

- `manifest.json`, `configuration.json`, `feature_schema.json`: 입력 버전·해시·설정·특징 계약.
- `catalog.json`: 기존 308개 사양 스냅샷.
- `shard-*/{train,validation,test}_profiles.jsonl`: 사용자 조건·취향·중요도.
- `shard-*/{train,validation,test}_choices.jsonl`: 비교 차량·선택·이유·비교 유형.
- `shard-*/{train,validation,test}_audit.jsonl`: 선택 확률·난수·효용·혼합 출처.
- `shard-*/{train,validation,test}_choices.npz`: 특징·쌍 인덱스·정답·사용자 ID·카탈로그 인덱스.
- `preview.json`: 실제 생성된 첫 20명의 전체 프로필과 비교 선택.
- `generation_summary.json`: 분포·노출·제외·선택 집계.
- `validation_report.json`: 저장 파일 재검증 결과.

분할은 재무 조건의 해시로 결정해 같은 재무 그룹이 서로 다른 분할에 섞이지 않게 합니다. 같은 씨앗 사례를 사용하는 서로 다른 사용자는 여러 분할에 존재할 수 있습니다. 별도의 사례 유형 전체 제외 평가는 아직 포함하지 않습니다.

## 확인

```powershell
& $pythonPath -m unittest tools.data.households.tests.test_scenario_population -v
```

전체 데이터 감사는 파일 해시, 인원·비교 수, 사용자 중복, 재무 그룹 누수, 독립 Decimal 현금·12개월 보전 검사, 필수 좌석, 사용자/차량 인덱스 연결, 공통 인코더 재구성, 확률·정답 일치, 사용자별 비교 중복을 검사합니다.
