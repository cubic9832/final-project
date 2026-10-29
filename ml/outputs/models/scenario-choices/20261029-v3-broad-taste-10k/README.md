# 브랜드·모델 지정 없는 일반 취향 추천 v3

사용자가 알고 있는 대략적인 취향과 이용 환경으로 차량을 추천합니다. 브랜드 또는 특정 차량 모델을 선택하도록 요구하지 않습니다.

- 입력: 재무 조건, 비용 중요도, 선호 차체·연료·외부 전장 크기와 중요도, 필수 인원, 주행거리, 충전 접근성.
- 학습 데이터: 사용자 10,000명, 비교 선택 100,000쌍, 전체 96모델·308사양.
- 모든 사용자의 브랜드 선호·모델 호감은 비어 있고 해당 선택 효용 가중치는 0입니다. 정답을 새로 생성했습니다.
- 기존 68개 배열 계약의 브랜드/모델 일치도 슬롯은 중립 상수, 중요도 슬롯은 0입니다. 이름이나 ID를 입력으로 인코딩하지 않습니다.
- 30 epochs 중 검증 log loss가 가장 낮은 epoch 11을 선택했습니다. 평가 15,630쌍에서 정확도 73.84%, log loss 0.4696, Brier score 0.1588입니다.
- 저장 모델 재로딩과 공통 인코더 추론 점수가 일치했습니다.

데이터: `data/households/synthetic/scenario-population-v3-broad-taste-10k-20261029`.
설정: `tools/data/households/scenario_population_v3_config.json`.

## 실행 서버

화면 `http://127.0.0.1:5174`, 모델 API `http://127.0.0.1:8003`에 적용했습니다.

프론트에서 브랜드·모델 선택을 제거했고, 이전 저장값도 추천 요청에 포함하지 않습니다. API는 해당 필드를 포함하는 요청에 400을 반환합니다. 옵션 조회도 선호 브랜드·차량 모델 선택지를 제공하지 않습니다.

`serving_verification.json`에 실제 프록시 검증 결과를 저장했습니다. 브랜드나 모델을 지정하지 않은 전기·픽업 선호 요청으로 무쏘 EV, 무쏘, EV3를 추천했습니다. 모든 결과가 재무·필수 인원을 충족했습니다.

전체 데이터 재검증, 학습·데이터 테스트 12개, API 테스트 5개, 프론트 테스트 15개 및 빌드를 통과했습니다.

## 재현

```powershell
$env:PYTHONPATH = "$PWD/ml;$PWD"
& C:/workspace/final-project/ml/.venv/Scripts/python.exe -m vehicle_matching.train_scenario_choices `
  --data data/households/synthetic/scenario-population-v3-broad-taste-10k-20261029 `
  --output ml/outputs/models/scenario-choices/<새-실행-이름> `
  --epochs 30 --batch-size 2048 --threads 4
```
