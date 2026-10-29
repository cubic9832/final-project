# ML 파일 분류 및 정리 기록

2026-10-28 기준. 실행 진입점·Python import·도구와 테스트 참조를 검토했다. 현재 실행 분류는 함수 내부 import와 구형 모델 로딩 분기도 포함하는 보수적 의존성 범위이며, 모든 요청이 모든 파일을 실행한다는 뜻은 아니다.

## 현재 추천 서비스 코드

| 파일 | 책임 |
| --- | --- |
| `vehicle_matching/api.py` | 추천 API 요청·응답과 모델 로딩 |
| `vehicle_matching/body_types.py` | 검증된 차량 차체 유형 연결 |
| `vehicle_matching/budget.py` | 현금 구매 예산 계산 |
| `vehicle_matching/catalog.py` | 차량 카탈로그 입출력·식별·해시 검증 |
| `vehicle_matching/catalog_merge.py` | 기존 차량과 확장 차량 목록 병합 |
| `vehicle_matching/explanations.py` | 추천 근거와 비교 설명 구성 |
| `vehicle_matching/features.py` | 기본 모델 학습·추론 공통 입력 변환 |
| `vehicle_matching/finance.py` | 구매 자금·월 비용·재무 적합성 계산 |
| `vehicle_matching/managed_catalog.py` | 백엔드가 제공하는 차량 목록 조회 |
| `vehicle_matching/model.py` | 기본 비교 순위 모델과 모델 로딩 |
| `vehicle_matching/preference_model.py` | 선호를 포함한 순위 모델·전처리·가중치 저장 |
| `vehicle_matching/preferences.py` | 선호 평가와 후보 제외 기준 |
| `vehicle_matching/problems.py` | API 오류 응답 구성 |
| `vehicle_matching/recommendation_policy.py` | 필수 정원·선호 중요도·ML 순서의 정렬 정책 |
| `vehicle_matching/seating.py` | 차량별 정원 등록 자료 적용 |
| `vehicle_matching/service.py` | 후보 검증·모델 점수 계산·최종 추천 조합 |
| `vehicle_matching/specifications.py` | 검증된 차량 사양 적용 |

## 재학습·평가·데이터 준비 코드

현재 요청 처리에서는 호출하지 않지만 재학습·독립 평가·데이터 도구 참조가 있어 유지한다. `tools/data`에서도 일부 모델·정책 구현을 가져오므로 단순 미사용 파일로 삭제하지 않았다.

| 파일 | 책임 |
| --- | --- |
| `vehicle_matching/__init__.py` | 패키지 초기화 |
| `vehicle_matching/dataset.py` | 재현 가능한 합성 재무 프로필 제공 |
| `vehicle_matching/evaluate.py` | 비교 정답 일치도 및 조건 준수 평가 |
| `vehicle_matching/evaluate_curated_population.py` | 정제 데이터에서 모델 비교 평가 |
| `vehicle_matching/evaluate_preference_population.py` | 선호 프로필별 추천·재무 경계 평가 |
| `vehicle_matching/extend_body_population.py` | 차체 선호 입력을 포함하도록 학습 데이터 확장 |
| `vehicle_matching/partition_preference_population.py` | 데이터 분할·쌍별 학습 자료 구성 |
| `vehicle_matching/refine_population.py` | 학습·검증·평가 자료 정제와 무결성 확인 |
| `vehicle_matching/retrain_verified_catalog.py` | 검수 차량 카탈로그로 데이터 재생성·재학습 |
| `vehicle_matching/score_transforms.py` | 오프라인 점수 변환 실험의 공통 계산 |
| `vehicle_matching/train.py` | 초기 비교 순위 모델 학습 |
| `vehicle_matching/train_curated_population.py` | 정제 데이터에서 학습 실행 |
| `vehicle_matching/train_preference_population.py` | 선호 프로필 생성과 비교 순위 모델 학습 |
| `vehicle_matching/validate_curated_population.py` | 정제 자료와 추천 결과 검증 |

## 독립 실험·분석 — 정리 후 보존

| 파일 | 분류 |
| --- | --- |
| `experiments/__init__.py` | 독립 실험·분석 — 정리 후 보존 |
| `experiments/audit_ml_ablation.py` | 독립 실험·분석 — 정리 후 보존 |
| `experiments/audit_preference_population.py` | 독립 실험·분석 — 정리 후 보존 |
| `experiments/audit_preference_reversals.py` | 독립 실험·분석 — 정리 후 보존 |
| `experiments/audit_preference_sensitivity.py` | 독립 실험·분석 — 정리 후 보존 |
| `experiments/candidate-v2/catalog.json` | 회귀 테스트용 초기 모델 묶음; 현재 테스트가 로딩하므로 유지 |
| `experiments/candidate-v2/metadata.json` | 회귀 테스트용 초기 모델 묶음; 현재 테스트가 로딩하므로 유지 |
| `experiments/candidate-v2/model.pt` | 회귀 테스트용 초기 모델 묶음; 현재 테스트가 로딩하므로 유지 |
| `experiments/candidate-v2/report.json` | 회귀 테스트용 초기 모델 묶음; 현재 테스트가 로딩하므로 유지 |
| `experiments/diagnose_score_conversion.py` | 독립 실험·분석 — 정리 후 보존 |
| `experiments/experiment_score_transforms.py` | 독립 실험·분석 — 정리 후 보존 |

## 구형 구현·기록 — 기본 실행에서 분리

| 파일 | 분류 |
| --- | --- |
| `legacy/__init__.py` | 구형 구현·기록 — 기본 실행에서 분리 |
| `legacy/history/ml-readme.md` | 구형 구현·기록 — 기본 실행에서 분리 |
| `legacy/history/recommendation-v1.md` | 구형 구현·기록 — 기본 실행에서 분리 |
| `legacy/history/vehicle-matching-readme.md` | 구형 구현·기록 — 기본 실행에서 분리 |
| `legacy/README.md` | 구형 구현·기록 — 기본 실행에서 분리 |
| `legacy/recommender/__init__.py` | 구형 구현·기록 — 기본 실행에서 분리 |
| `legacy/recommender/__main__.py` | 구형 구현·기록 — 기본 실행에서 분리 |
| `legacy/recommender/api.py` | 구형 구현·기록 — 기본 실행에서 분리 |
| `legacy/recommender/artifact.py` | 구형 구현·기록 — 기본 실행에서 분리 |
| `legacy/recommender/cli.py` | 구형 구현·기록 — 기본 실행에서 분리 |
| `legacy/recommender/dataset.py` | 구형 구현·기록 — 기본 실행에서 분리 |
| `legacy/recommender/evaluate.py` | 구형 구현·기록 — 기본 실행에서 분리 |
| `legacy/recommender/metrics.py` | 구형 구현·기록 — 기본 실행에서 분리 |
| `legacy/recommender/models/__init__.py` | 구형 구현·기록 — 기본 실행에서 분리 |
| `legacy/recommender/models/mlp.py` | 구형 구현·기록 — 기본 실행에서 분리 |
| `legacy/recommender/predict.py` | 구형 구현·기록 — 기본 실행에서 분리 |
| `legacy/recommender/preprocessing.py` | 구형 구현·기록 — 기본 실행에서 분리 |
| `legacy/recommender/ranking.py` | 구형 구현·기록 — 기본 실행에서 분리 |
| `legacy/recommender/service.py` | 구형 구현·기록 — 기본 실행에서 분리 |
| `legacy/recommender/train.py` | 구형 구현·기록 — 기본 실행에서 분리 |
| `legacy/serve-v1.ps1` | 구형 구현·기록 — 기본 실행에서 분리 |
| `legacy/tests/__init__.py` | 구형 구현·기록 — 기본 실행에서 분리 |
| `legacy/tests/support.py` | 구형 구현·기록 — 기본 실행에서 분리 |
| `legacy/tests/test_api.py` | 구형 구현·기록 — 기본 실행에서 분리 |
| `legacy/tests/test_dataset.py` | 구형 구현·기록 — 기본 실행에서 분리 |
| `legacy/tests/test_model.py` | 구형 구현·기록 — 기본 실행에서 분리 |
| `legacy/tests/test_preprocessing.py` | 구형 구현·기록 — 기본 실행에서 분리 |
| `legacy/tests/test_quality_experiment.py` | 구형 구현·기록 — 기본 실행에서 분리 |
| `legacy/train_quality_choices.py` | 구형 구현·기록 — 기본 실행에서 분리 |

## 현재 회귀 검증 — 유지

| 파일 | 분류 |
| --- | --- |
| `tests/.gitkeep` | 현재 회귀 검증 — 유지 |
| `tests/test_asset_funding.py` | 현재 회귀 검증 — 유지 |
| `tests/test_body_preferences.py` | 현재 회귀 검증 — 유지 |
| `tests/test_budget_band.py` | 현재 회귀 검증 — 유지 |
| `tests/test_catalog_merge.py` | 현재 회귀 검증 — 유지 |
| `tests/test_explanations.py` | 현재 회귀 검증 — 유지 |
| `tests/test_financial_soft_policy.py` | 현재 회귀 검증 — 유지 |
| `tests/test_managed_catalog.py` | 현재 회귀 검증 — 유지 |
| `tests/test_managed_costs.py` | 현재 회귀 검증 — 유지 |
| `tests/test_ml_only_ranking.py` | 현재 회귀 검증 — 유지 |
| `tests/test_monthly_affordability.py` | 현재 회귀 검증 — 유지 |
| `tests/test_population_partition.py` | 현재 회귀 검증 — 유지 |
| `tests/test_preference_population.py` | 현재 회귀 검증 — 유지 |
| `tests/test_preference_reversals.py` | 현재 회귀 검증 — 유지 |
| `tests/test_preferences.py` | 현재 회귀 검증 — 유지 |
| `tests/test_purchase_preference.py` | 현재 회귀 검증 — 유지 |
| `tests/test_purpose_independence.py` | 현재 회귀 검증 — 유지 |
| `tests/test_ranking_precision.py` | 현재 회귀 검증 — 유지 |
| `tests/test_recommendation_budget.py` | 현재 회귀 검증 — 유지 |
| `tests/test_recommendation_policy.py` | 현재 회귀 검증 — 유지 |
| `tests/test_refine_population.py` | 현재 회귀 검증 — 유지 |
| `tests/test_score_transforms.py` | 현재 회귀 검증 — 유지 |
| `tests/test_seating_registry.py` | 현재 회귀 검증 — 유지 |
| `tests/test_specifications.py` | 현재 회귀 검증 — 유지 |
| `tests/test_vehicle_matching.py` | 현재 회귀 검증 — 유지 |
| `tests/test_verified_catalog_training.py` | 현재 회귀 검증 — 유지 |

## 모델·평가 자료와 실행 설정 — 유지

| 경로 | 판단 |
| --- | --- |
| `outputs/models/candidate-preferences/20261027-seating-verified-v1/*` | 현재 기본 모델·카탈로그·학습·서빙 검증 기록. 변경하지 않음 |
| `outputs/models/candidate-preferences/20261026-100k-v1/*`, `20261026-refined-v1/*`, 로컬 `20261026-body-v1/*` | 이전 모델 비교·재학습 출처 보존. 현재 기본 모델과 구분 |
| `outputs/reports/**`, `reports/**` | 실험 근거와 데이터 출처·평가 기록. 재현 명령의 모듈 경로만 갱신 |
| `serve-candidates.ps1` | 현재 8002 서버 진입점 |
| `pyproject.toml`, `requirements.txt`, `requirements-cpu-windows.txt`, `.gitignore` | 설치·패키지·환경·추적 기준 |
| `examples/candidate-profile.json` | 현재 요청 예시 |
| `examples/profile.json` | 구형 v1 입력 예시; 과거 문서 참조를 위해 유지 |
| `.venv/`, `*.egg-info/`, `__pycache__/` | Git 제외 로컬 설치·캐시. 사용자 실행 환경이므로 일괄 삭제하지 않음 |

## 제거한 파일

| 이전 파일 | 이유 |
| --- | --- |
| `config/datasets.json` | 참조 데이터 4개가 모두 없고 현재 학습·서빙 코드가 읽지 않는 참고 설정 |
| `vehicle/__init__.py`, `vehicle/train.py`, `vehicle/evaluate.py`, `vehicle/predict.py` | 구형 recommender CLI를 단순 재호출하는 중복 호환 진입점. 구형 CLI 자체는 legacy에 보존 |

## 이동 및 연결 변경

- `recommender/**/*.py` → `legacy/recommender/`; import와 구형 CLI 설치 진입점을 갱신했다.
- 구형 전용 테스트 5개와 `support.py` → `legacy/tests/`. 현재 테스트와 분리했다.
- `experiments/train_quality_choices.py` → `legacy/train_quality_choices.py`.
- `vehicle_matching/{audit_ml_ablation,audit_preference_population,audit_preference_reversals,audit_preference_sensitivity,diagnose_score_conversion,experiment_score_transforms}.py` → `experiments/`. 상호 import·테스트·보고서 재현 명령을 갱신했다.
- 기존 README 2개와 구형 API 문서 → `legacy/history/`. AI 작업 기록은 보존했다.
- `serve.ps1` → `legacy/serve-v1.ps1`. 루트 `dev.ps1`의 기본 실행은 현재 8002 서버로 맞췄다.
- `vehicle_matching/problems.py`에 기존 오류 응답 구현을 옮겨 현재 서비스의 v1 의존성을 제거했다.
- 데이터와 모델 묶음의 파일 내용·해시·출처 경로는 변경하지 않았다. 과거 JSON 보고서의 경로는 당시 기록으로 보존한다.

## 검증

- 현재 추천·학습 테스트: **94개 중 92개 통과, 기존 실패 2개**.
- 보관한 v1·품질 실험 테스트: **22개 모두 통과**.
- 기존 실패 재현: Git HEAD의 원본 소스를 메모리에서 로딩해 관련 테스트 5개를 실행했고 같은 2개 실패를 확인했다.
  - `test_population_partition`: 테스트용 차량에 검증된 차체 유형이 없어 `Unverified body type` 발생.
  - `test_seating_registry`: 확장 차량 16개가 좌석 등록 목록에 없어 전체 ID 집합 동일성 검증 실패.
- 기존 실패를 숨기기 위한 테스트 삭제·조건 완화는 하지 않았다.
- 현재 모델의 체크섬 검증과 차량 **282개 로딩 성공**. 현재 API 로딩 시 `legacy`·`recommender` 모듈이 import되지 않음을 확인했다.
- 로컬 editable 패키지 재설치 성공. 구형 CLI 및 이동한 실험 모듈 import 확인.
- 샌드박스의 Windows asyncio 로컬 소켓 제한으로 API 테스트가 대기해, 같은 테스트를 제한 밖에서 실행했다. 임시 디렉터리는 작업공간 `tmp/`로 지정했다.
- 데이터·모델 묶음에는 변경이 없으며 재학습·데이터 재생성을 수행하지 않았다.
