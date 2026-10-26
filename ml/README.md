# 현재 ml/test 학습 데이터

현재 운영 판단·미해결 서비스 점수 포화·행동 데이터 수집 후속 요건은 [ML 검증 상태](../docs/ml-recommendation-status.md)에 정리했다. 순위 평가 수정과 실제 서비스 점수 변환 수정은 구분한다.

현재 정제 데이터는 `data/households/synthetic/curated-current-v2-20261026`이며 상세 기준은 해당 폴더의 `rules.txt`를 따른다. 학습·검증·평가·재무 검증 파일을 분리했고, 정제본만으로 `python -m vehicle_matching.train_curated_population`을 실행할 수 있다.

통합 데이터 학습 결과는 `ml/outputs/models/candidate-preferences/20261026-refined-v1`에 있다. 초기 ML 단독 지표 하락은 sigmoid 출력 포화로 확인됐으며, 원본 출력 재평가에서는 통합 모델이 소폭 높았다. 실행 모델은 `20261026-100k-v1`로 유지했다. 최종 추천과 재무 경계 검증은 통과했다. 비교 지표는 정제 폴더의 `balanced_evaluation_report.json`을 참고한다.

아래 문서는 과거 v1 실험 기록이며 현재 입력·데이터·정책과 구분한다.

---
# 재무 진단 UI용 차량 추천 모델

> `ml/test` 독립 실험: [사용자·차량 조합 평가 v2](vehicle_matching/README.md). 고정 라벨 분류 대신 실제 가격 후보별 비용 검증과 pairwise MLP 순위를 사용한다. `./ml/serve-candidates.ps1`(8002)와 `npm --prefix front run dev`(5173)로 실행한다. 이 브랜치의 React는 v2에 연결되며 아래 v1 서버 코드는 보존한다.

현재 UI에서 이미 받는 정보만으로 학습·추론한다. 입력 항목 추가나 세전소득·인구 정보 추정을 하지 않는다. `feat/data` 기반 MLP를 재사용하되 입력 스키마를 `financial-ui-v1`로 바꿔 재학습했다. 기존 17항목 모델의 가중치는 이 모델과 호환되지 않는다.

## 입력

수치 입력은 월 실수령소득, 현금성 자산, 월 주거비, 월 기타 생활소비, 차량 구매 전 대출 잔액, 차량 구매 전 월 상환액, 연간 주행거리다. 범주 입력은 이용목적 하나다. 금액은 모두 원이다. 예시는 `examples/profile.json`에 있다.

구매 후 차량 할부가 포함된 보유자 대출잔액·월상환액은 사용하지 않는다. 구매 감사 자료의 `기존대출잔액_보정전_원`과 `기존월상환액_보정전_원`으로 대체한다. 목표 저축액을 실제 저축액으로 간주하지 않으며, 모델에서 저축 항목 자체를 제외한다.

## 설치·학습

저장소 루트 PowerShell:

```powershell
python -m venv ml/.venv
& ./ml/.venv/Scripts/python.exe -m pip install -e "./ml[serve,test]"
& ./ml/.venv/Scripts/python.exe -m recommender train --segment all-cars
```

기본 입력은 `data/seed/domestic-car`, `data/seed/imported-car`의 owners.csv·purchases.csv다. 국내 10,000명·수입 6,000명을 기존 구분대로 합쳐 학습 11,200명·검증 2,400명·평가 2,400명, 20개 라벨로 학습한다. 서로 다른 모델의 확률을 임의로 섞지 않고 하나의 분류 모델에서 상위 3개를 고른다.

`ml/config/datasets.json`은 기존 확장 CSV 경로의 참고 설정이며 이 모델의 기본 입력으로 자동 로딩하지 않는다.

전처리는 학습 분할에만 맞추고, MLP 후보 3개를 검증 top-3으로 비교한다. 에포크 상한30·배치256이며 선택된 에포크의 가중치를 저장한다.

산출물은 `ml/outputs/models/financial-ui-v1/all-cars/{시각}/`에 model.pt·model.json·preprocessor.json·report.json으로 저장하며 Git에서 제외한다. 이전 모델의 경로·가중치를 덮어쓰지 않는다.

## 서버와 화면

```powershell
./ml/serve.ps1
```

서버는 새 스키마 경로에서 최신 모델을 읽어 재사용한다. 특정 실행을 고정하려면 `ML_FINANCIAL_RUN` 환경변수에 모델 폴더의 절대 경로를 지정한다. 모델 교체 후에는 서버를 재시작한다.

React는 재무 진단 마지막 페이지의 **추천 차량 확인하기** 클릭에만 POST를 전송한다. 페이지 진입·새로고침·입력 완료만으로 추천을 요청하지 않는다. [화면 실행과 API 계약](../docs/recommendation.md)을 참고한다.

## CLI 평가·예측

아래 모델 폴더는 실제 학습 명령이 출력한 경로로 바꾼다.

```powershell
& ./ml/.venv/Scripts/python.exe -m recommender evaluate --run ml/outputs/models/financial-ui-v1/all-cars/20261019T121402 --data data/seed
& ./ml/.venv/Scripts/python.exe -m recommender predict --run ml/outputs/models/financial-ui-v1/all-cars/20261019T121402 --profile ml/examples/profile.json --k 3
```

기존 vehicle.train/evaluate/predict 진입점도 같은 CLI를 호출한다.

## 테스트

```powershell
Set-Location ml
./.venv/Scripts/python.exe -m unittest discover -s tests
```

입력 분할·조인·구매 결과 누수 방지·저장 모델 재로딩·API 오류 계약을 검증한다. CPU 검증 환경의 직접 의존성 버전은 requirements-cpu-windows.txt에 기록했다. 합성 데이터 평가 점수는 실제 구매 성향이나 구매 자격을 검증하지 않는다.
