<<<<<<< HEAD
# 차량 추천 ML
=======
# 가성비별 추천 가격대 — 2026-10-27

현재 추천 정책은 `required-seats-preference-priority-price-band-v2`다. 가성비 중요도 낮음(1·2)은 구매 상한의 80%, 보통(3)은 70%, 높음(4·5)은 60%를 하한으로 적용한다. 상한은 비상자금을 제외한 가용 현금이며 별도 구매 상한이 있으면 그 값을 넘지 않는다. 하한은 차량 목록 최고가로 재계산하지 않으며 원 단위로 올림한다.

가격대는 일반 추천과 사양 확인 필요 후보 모두에 적용한다. 해당 가격대에 재무·정원 조건을 충족하는 후보가 없으면 하한을 임의로 낮추지 않고 빈 결과를 반환한다. 가격대 안에서는 기존 선호 중요도·모델 점수 정렬을 유지하고 비싼 차에 추가 가점을 주지 않는다.

이번 작업은 추천 후보 필터 변경이며 모델 가중치를 재학습하지 않았다. 실행 모델은 `20261027-seating-verified-v1` 그대로다. 이후 재학습 명령은 새 가격대 안의 후보로 특징·정답·비교 쌍을 생성한다. 기존 날짜별 학습 데이터·보고서는 당시 정책의 기록이다.

# 정원 검수 후 재학습 — 2026-10-27
>>>>>>> fe943476966c5a3cb271518b545315571ab574d3

현재 추천은 `vehicle_matching`의 비교 학습 모델을 사용한다. 입력 데이터는 `data/`, 생성·수집 도구는 `tools/data/`, 학습·평가·추론 코드는 `ml/`이 담당한다.

## 현재 모델과 데이터

- 기본 모델: `ml/outputs/models/candidate-preferences/20261027-seating-verified-v1/`
- 학습 자료: `data/households/synthetic/seating-verified-v1-20261027/`
- 서버는 시작 시 모델 묶음의 `model.pt`, `metadata.json`, `catalog.json`을 검증하고 로딩한다. 추천 요청마다 재학습하지 않는다.
- 합성 정답을 학습한 모델이다. 현재 추천은 재무·정원 필수 조건과 선호 우선순위를 적용하고 ML 점수를 함께 사용한다. 평가 수치는 실제 구매 확률이나 만족도가 아니다.

## 설치와 실행

프로젝트 루트 PowerShell:

```powershell
python -m venv ml/.venv
& ./ml/.venv/Scripts/python.exe -m pip install -e "./ml[serve,test]"
./ml/serve-candidates.ps1
```

API는 `127.0.0.1:8002`, `/api/v2/recommendations`를 사용한다. 루트 `dev.ps1`도 이 서버를 실행한다. `ML_CANDIDATE_CATALOG`로 외부 카탈로그를 지정할 수 있으며, 모델 폴더를 변경할 때는 `./ml/serve-candidates.ps1 -Run 'outputs/models/새로운-실행'`을 사용한다.

## 재학습

모델과 데이터의 기존 경로를 덮어쓰지 않고 새 출력 경로를 지정한다. 아래 명령은 이전 차체 선호 자료를 기반으로 카탈로그를 갱신하고 데이터·모델을 새로 생성한다. 실행 중인 Spring 차량 API(8080)의 추천 카탈로그를 사용하므로 상세 옵션은 `--help`를 확인한다.

```powershell
$env:PYTHONPATH = "$PWD/ml;$PWD"
& ./ml/.venv/Scripts/python.exe -m vehicle_matching.retrain_verified_catalog --help
& ./ml/.venv/Scripts/python.exe -m vehicle_matching.retrain_verified_catalog --source data/households/synthetic/body-preference-v1-20261026 --data data/households/synthetic/my-new-run --output ml/outputs/models/candidate-preferences/my-new-run --old-model ml/outputs/models/candidate-preferences/20261027-seating-verified-v1 --epochs 12
```

`train_curated_population`은 `refinement_report.json` 형식의 정제본을 위한 별도 학습 진입점이다. 최신 정원 데이터의 `generation_report.json` 형식과 혼용하지 않는다.

## 파일 분류와 검증

- [파일별 관리 목록](FILE_INVENTORY.md): 현재 실행·재학습·실험·보관·삭제 파일과 근거.
- `vehicle_matching/`: 현재 서비스와 학습·평가에 필요한 코드.
- `experiments/`: 운영 서비스가 사용하지 않는 오프라인 분석. 현재 모델의 검증·재현에 유용하므로 보존한다.
- `tests/`: 현재 추천·학습의 회귀 검증.
- `legacy/`: 구형 v1 코드·테스트와 AI 작업 기록. 현재 서비스가 의존하지 않는다.
- `outputs/`, `reports/`: 모델·평가 및 출처 기록. 모델 해시와 데이터 경로는 유지한다.

```powershell
$env:PYTHONPATH = "$PWD/ml;$PWD"
& ./ml/.venv/Scripts/python.exe -m unittest discover -s ml/tests -v
# 구형 코드를 수정하거나 과거 결과를 검증할 때만 실행
& ./ml/.venv/Scripts/python.exe -m unittest discover -s ml/legacy/tests -v
```

[ML 검증 상태](../docs/ml-recommendation-status.md), [현재 추천 계약](../docs/recommendation.md), [과거 작업 기록](legacy/history/ml-readme.md)을 참고한다.
