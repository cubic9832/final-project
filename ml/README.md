# 차량 추천 모델

구매 전에 알 수 있는 프로필로 보유 차량 라벨을 맞히고, 확률이 높은 상위 k대를 추천합니다. 국내차와 수입차는 카탈로그가 겹치지 않아 같은 코드로 세그먼트마다 따로 학습합니다.

사전학습 가중치는 쓰지 않습니다. 작은 MLP를 데이터에서 처음부터 학습합니다.

## 데이터 파이프라인

`owners.csv`와 `purchases.csv`를 `프로필_식별자`로 1:1 조인합니다. `owner-summary.csv`는 학습에 쓰지 않습니다. 기본 입력은 `data/seed/domestic-car` 또는 `data/seed/imported-car`이고, `--data`로 `data/generated/{segment}`처럼 같은 파일 이름을 가진 디렉터리를 지정할 수 있습니다.

```text
owners.csv + purchases.csv
        │  프로필_식별자 조인, 구매 후 정보 제거
        ▼
데이터_구분  학습 / 검증 / 평가
        │  학습 분할만으로 수치 log1p·표준화, 범주 코드
        ▼
MLP 후보 학습 → 검증 top-3이 가장 높은 설정
        │  평가 분할은 여기서 한 번만 측정
        ▼
outputs/models/{segment}/{시각}/
        │
        ▼
프로필 한 건 → 상위 k대 (라벨코드, 모델, 차체, 차급, 확률)
```

분할 이름은 파일의 `데이터_구분` 값을 그대로 씁니다. 학습으로 전처리와 가중치를 맞추고, 검증으로 하이퍼파라미터를 고르며, 평가는 최종 보고에만 씁니다.

### 학습에 넣는 값

나이, 경력, 가구원수, 부양인원, 연간 세전소득, 현금·금융·보증금·부동산, 월 주거비, 월 생활비, 월 저축, 연간 주행거리, 구매 전 대출잔액(`기존대출잔액_보정전_원`), 성별, 직업, 이용목적.

금액처럼 범위가 큰 수치를 포함해 위 수치는 `log1p` 후 표준화합니다. 표준화 평균과 범주 코드는 학습 분할에서만 맞춥니다. 추론은 저장된 그 변환을 그대로 씁니다.

### 학습에서 빼는 값

차가 정해진 뒤에만 알 수 있는 값은 넣지 않습니다. 보유 차량 라벨·브랜드·모델·차체·차급, 그 차의 가격·트림·연료·할부, 차량 할부가 더해진 대출잔액·순자산·월상환·월잔여액, `기존_모델`, `데이터_구분`과 생성 메타데이터가 여기 해당합니다.

## 준비

Python 3.11 이상, numpy, PyTorch가 필요합니다.

```bash
cd ml
python -m venv .venv
source .venv/bin/activate
python -m pip install -e .
```

Windows에서는 `.venv\Scripts\activate` 로 가상환경을 켭니다.

## 실행

저장소 루트가 아니라 `ml` 디렉터리에서 실행합니다. `--segment`는 `domestic-car` 또는 `imported-car`입니다.

```bash
python -m recommender train --segment domestic-car
python -m recommender train --segment imported-car
```

- `--data`를 생략하면 `data/seed/{segment}`를 읽습니다.
- `--output`을 생략하면 `ml/outputs/models/{segment}/{시각}`에 저장합니다. 이미 있는 디렉터리에는 덮어쓰지 않습니다.
- 학습이 끝나면 산출물 디렉터리 경로를 출력합니다.

검증 top-3으로 고르는 MLP 후보는 `recommender/models/mlp.py`의 `candidate_rankers`에 있습니다. 기본은 은닉층 `(32, 16)`, `(64, 32)`, `(128, 64)` 세 가지이고, 에포크 30, 배치 256입니다.

프로필 한 건의 상위 3대:

```bash
python -m recommender predict --run outputs/models/domestic-car/20261016T163000 --profile examples/profile.json --k 3
```

`profile.json`은 학습에 넣은 항목만 담습니다.

```json
{
  "나이_세": 27,
  "경력_년": 5,
  "가구원수_명": 4,
  "부양인원_명": 1,
  "개인_연간세전소득_원": 79617000,
  "개인_현금성자산_원": 17742000,
  "개인_기타금융자산_원": 9920000,
  "개인_주거보증금자산_원": 0,
  "개인_부동산자산_원": 0,
  "개인_평균월주거비_원": 858000,
  "개인_평균월기타생활소비_원": 1957000,
  "개인_평균월저축액_원": 1576000,
  "연간_주행거리_km": 10529,
  "기존대출잔액_보정전_원": 0,
  "성별": "남성",
  "직업_유형": "근로자",
  "차량_이용목적": "여가"
}
```

출력은 그 세그먼트 라벨 중 상위 k개입니다. 확률은 세그먼트 전체 라벨에 대해 합이 1이고, 응답에는 상위만 담깁니다. 트림, 가격, 할부금은 나오지 않습니다.

```json
[
  {
    "라벨코드": "OWN007",
    "모델": "스포티지",
    "차체": "SUV",
    "차급": "준중형",
    "확률": 0.21
  }
]
```

저장해 둔 모델로 평가 분할만 다시 측정합니다. 전처리는 학습 때 저장한 상태를 씁니다.

```bash
python -m recommender evaluate --run outputs/models/domestic-car/20261016T163000 --data ../data/seed/domestic-car
```

`top3`은 정답 라벨이 확률 상위 3개 안에 있는 비율이고, `log_loss`는 정답 라벨 확률의 로그손실입니다.

## 산출물

`ml/outputs/models/`는 Git에 포함하지 않습니다.

`report.json`의 `train`, `validation`, `evaluation`은 검증 top-3이 가장 높았던 에포크로 되돌린 가중치에서 측정합니다. `selected_epoch`가 그 에포크 번호이고, `epochs`는 그 후보의 에포크별 학습·검증 top-3과 로그손실입니다. 평가는 모델을 고른 뒤에만 계산합니다.

학습 top-3이 검증보다 크게 높고 에포크가 지날수록 간격이 벌어지거나 검증 로그손실이 다시 올라가면 과학습입니다. 선택한 에포크가 그 이전인지 같이 봅니다. 검증과 평가가 비슷하면 검증으로 고른 결과가 평가 분할에 기대지 않은 것입니다.

| 파일 | 내용 |
| --- | --- |
| `preprocessor.json` | 수치 평균·표준편차, 범주 코드, 라벨과 모델·차체·차급 |
| `model.json` | MLP 설정과 입력·출력 크기 |
| `model.pt` | 가중치 |
| `report.json` | 고른 설정, 학습·검증·평가 지표, 선택 에포크와 에포크별 곡선, 후보별 검증 top-3 |

## 공통 로직과 교체

조인, 누수 컬럼 제거, 분할, 전처리, top-3·로그손실, 산출물 저장은 학습과 추론이 같이 쓰는 공통 코드입니다. 모델만 바꿉니다.

다른 구조를 넣을 때는 `fit`, `predict_proba`, `save`, `describe`, `learning_curve`를 가진 클래스를 만들고 `train`의 후보로 넘깁니다. 데이터와 지표 코드는 그대로 둡니다. 후보를 넘기지 않으면 `candidate_rankers`의 MLP를 비교합니다.

## 테스트

```bash
cd ml
source .venv/bin/activate
python -m unittest discover -s tests
```

누수 컬럼이 특징에 없는지, 전처리가 학습 분할만 보는지, 확률의 합이 1이고 열 수가 라벨 수와 같은지를 확인합니다.

## test 브랜치 통합

원본 구현은 `feat/data`의 `recommender` 패키지다. `test`에서는 `ml/recommender`로 배치하고 기본 산출물 경로를 `ml/outputs/models`로 변경했다. 데이터 생성기는 기존 `tools/data`를 유지하며 별도 `data-generator` 패키지는 가져오지 않았다. 프런트·HTTP API 연동은 이 통합에 포함하지 않는다.

`ml/config/datasets.json`은 국내 100,000명·수입 96,000명의 기존 확장 데이터 경로를 보존한 참고 설정이다. 이번 모델의 기본 입력은 `data/seed`의 국내 10,000명·수입 6,000명이다. 다른 자료를 쓰려면 동일 스키마의 `owners.csv`, `purchases.csv` 디렉터리를 `--data`로 지정한다. 이전 설정을 자동으로 읽는다고 가정하지 않는다.

Windows PowerShell에서 저장소 루트 기준:

```powershell
python -m venv ml/.venv
& ./ml/.venv/Scripts/python.exe -m pip install -e ./ml
Set-Location ml
& ./.venv/Scripts/python.exe -m unittest discover -s tests
& ./.venv/Scripts/python.exe -m recommender train --segment domestic-car
& ./.venv/Scripts/python.exe -m recommender train --segment imported-car
```

기존 `python -m vehicle.train`, `vehicle.evaluate`, `vehicle.predict`는 같은 추천 CLI로 연결되며 해당 명령의 인자를 그대로 받는다. 예: `python -m vehicle.train --segment domestic-car`.

`reports/epoch-batch-check.md`는 원본 브랜치의 실험 기록이며 이번 통합에서 다시 측정한 점수가 아니다. 합성 데이터의 평가 점수는 실제 구매 경향이나 구매 자격을 검증하지 않는다. 생성된 가중치와 실행 결과는 Git에서 제외한다.

이번 통합에서 실제 학습·평가한 환경과 결과는 [통합 검증 기록](reports/integration-check.md)에 있다. 검증한 Windows CPU 직접 의존성 버전은 `requirements-cpu-windows.txt`에 기록했다. 동일 버전을 사용할 때는 저장소 루트에서 `python -m pip install -r ml/requirements-cpu-windows.txt`를 먼저 실행한 뒤 `python -m pip install -e ./ml`로 패키지를 설치한다.
