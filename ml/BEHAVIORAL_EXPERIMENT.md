# 합성 행동 기반 100만 프로필 실험

이 실험은 `ml/test` 브랜치의 독립 worktree에서 수행한다. `hhc`의 미커밋 작업·모델·기본 서비스 설정을 변경하지 않는다. 기존 `ml/test` 이력은 보존하고 `hhc` 커밋까지 fast-forward했다.

## 2026-10-28 실행 결과

등록 차량 308개 사양을 고정해 적격 프로필 1,000,000개와 비교 선택 7,667,026쌍을 생성했다.
학습/검증/평가 프로필은 700,126 / 149,653 / 150,221개이며,
비교 쌍은 5,368,642 / 1,146,064 / 1,152,320개다.
재무 그룹 274,268개를 검사했고 분할 간 중복·누수는 0건이었다.

12 epoch 중 검증 log loss가 가장 낮은 11 epoch 모델을 선택했다.
동일한 평가 쌍 1,152,320건의 결과는 다음과 같다.

| 방법 | 정확도 | log loss | Brier score |
| --- | ---: | ---: | ---: |
| 새 신경망 | 68.53% | 0.5565 | 0.1912 |
| 선형 모델 | 65.36% | 0.6010 | 0.2081 |
| 기존 체크포인트 | 66.44% | 보정되지 않아 비교 생략 | 보정되지 않아 비교 생략 |
| 선호 우선 규칙 + 비용 동률 해소 | 66.53% | 해당 없음 | 해당 없음 |
| 비용 단독 규칙 | 55.93% | 해당 없음 | 해당 없음 |
| 무작위 선택 | 기대값 50% | 0.6931 | 0.2500 |

기존 모델 대비 정확도는 약 2.09%p, 선호 우선 규칙 대비 약 2.00%p 높았다.
실제 사용자 행동 검증이 아니라 정해 둔 합성 행동 가정에 대한 결과다.
계수 분포 변경에 대한 별도 민감도 실험과 세부 집단별 평가는 이번 실행에 포함하지 않았다.
생성·학습 핵심 테스트 5개와 기존 차체·유지비·추천 정책 테스트 9개가 통과했다.
`hhc` 모델 디렉터리 파일 84개의 실행 전후 SHA-256은 모두 일치했다.
증거는 `ml/outputs/reports/behavioral-million-20261028/hhc-model-protection.json`에 기록했다.

데이터의 수량 단위는 적격 비교가 가능한 프로필이다. 100만 개를 정확히 저장하며 프로필마다 최대 8쌍의 확률적 비교 선택을 생성한다. 부적격 프로필은 대체 입력을 새로 생성하되 선택 차량에 맞춰 기존 입력을 고치지 않는다. 차량은 생성 시작 시 등록 차량 API의 스냅샷으로 고정한다.

기존 규칙의 재무 분포·현금 구매·12개월 부족액 보전·필수 좌석을 유지한다. 새 규칙의 성향·절충·확률적 선택을 적용하며 결정적 정답과 스포츠 차량별 할당은 대체한다. 과거 정답이나 과거 모델의 예측을 학습 정답에 섞지 않는다. 과거 모델은 사후 비교에만 사용한다.

## 실행

이 worktree 루트 PowerShell에서 실행한다. Python 실행 파일은 `hhc`의 기존 가상환경을 공유하지만 `PYTHONPATH`는 이 worktree를 가리킨다. 패키지 재설치나 기존 가상환경 변경은 하지 않는다.

```powershell
$env:PYTHONPATH = "$PWD/ml;$PWD"
$pythonPath = 'C:/workspace/final-project/ml/.venv/Scripts/python.exe'
$env:OMP_NUM_THREADS = '1'
$env:MKL_NUM_THREADS = '1'
& $pythonPath -u -m tools.data.households.generate_behavioral_population `
  --output data/households/synthetic/behavioral-million-20261028 `
  --profiles 1000000 --shard-size 10000 --workers 6
& $pythonPath -u -m vehicle_matching.train_behavioral_choices `
  --data data/households/synthetic/behavioral-million-20261028 `
  --output ml/outputs/models/behavioral-choices/20261028-million-v1 `
  --epochs 12 --batch-size 16384 --threads 4 `
  --old-model ml/outputs/models/candidate-preferences/20261027-seating-verified-v1
```

생성 중단 후에는 동일 옵션에 `--resume`를 붙인다. 설정을 바꾸거나 불완전한 분할을 덮어쓰는 재개는 허용하지 않는다. 저장 완료된 분할은 다시 검수한다. 이후 전역 검수가 중복·누수·정확한 수량을 확인해야 최종 manifest가 학습에 사용된다.

## 학습과 평가

52개 입력을 쓰는 64→32→1 신경망을 새로 학습한다. 목적함수는 `BCEWithLogits(score_A-score_B, A선택여부)`이며 기존 교사 점수 회귀 항은 사용하지 않는다. 잠재 성향·효용·생성 확률·선택 난수는 입력에 포함하지 않는다. 학습 분할만으로 정규화하고 검증 log loss가 가장 낮은 epoch를 선택한다. 평가 분할은 선택에 사용하지 않는다.

같은 평가 비교 쌍에서 신경망, 선형 비교 모델, 기존 체크포인트와 동전 던지기를 비교한다. log loss·Brier score·정확도를 기록한다. 기존 선호 우선 규칙(비용으로 동률 해소)과 비용 단독 규칙은 정확도로 비교하며 동점은 기대 정답률 0.5로 계산한다. 규칙 점수를 확률로 해석하지 않는다. 기존 체크포인트의 점수 차이는 새 선택 확률에 보정되지 않았으므로 해당 log loss를 확률 품질의 공정한 비교로 해석하지 않는다. 관측되지 않는 사용자 성향이 있어 개별 선택은 본질적으로 확률적이다.

원본 생성기에서 재무 판정은 같은 그룹 내 재사용하고, 저장 검수는 압축 배열을 한 번만 읽도록 최적화했다. 선택·재무·특징 계산의 의미는 유지하며 데이터는 동일 계열의 규칙을 따른다.

## 산출물과 보존

- `data/households/synthetic/behavioral-million-20261028/manifest.json`: 정확한 프로필 수, 분할별 프로필·비교 수와 분할 보고서 해시.
- 같은 폴더의 `population_audit.json`: 분할 간 중복과 재무 그룹 누수 검사.
- `shard-*/`: 프로필·특징·확률적 정답·감사 기록·개별 검수.
- `ml/outputs/models/behavioral-choices/20261028-million-v1/`: 독립 모델·정규화·카탈로그·학습 이력과 평가 결과.

대형 원본 배열·JSONL·중복 카탈로그는 로컬에 보존하고 Git 추적에서 제외한다. 구성·규칙·해시·검수 결과와 모델은 브랜치에 기록한다. 다른 PC에서 원본을 재생성하려면 버전 관리된 루트 `catalog.json`을 `--catalog`로 명시한다. 모델은 서비스에 자동 활성화하지 않는다. 결과는 합성 행동 가정에 대한 성능이며 실제 구매 행동 검증이 아니다.
