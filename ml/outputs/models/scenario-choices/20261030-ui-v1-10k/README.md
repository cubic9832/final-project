# UI와 일치하는 차량 추천 모델

현재 UI의 비용·자금 보존·유지비 중요도, 윤곽·가속·연료·크기 취향을 학습했다.
38입력 → 64 → 32 → 1 MLP. 기존 68입력 모델·데이터는 변경하지 않았다.

- 데이터: ui-scenario-population-v1-20261030, 10,000명·99,442쌍
- 30 epochs 중 검증 log loss 최저인 epoch 10 선택
- 별도 평가 15,039쌍: 정확도 71.7135%, log loss 0.535948, Brier score 0.181851
- 동일 데이터 선형 모델: 정확도 71.4742%, log loss 0.540198
- 생성 확률의 기대 정확도: 71.7337%. 확률적 선택 때문에 정답 생성 정책도 매번 같은 차량을 고르지 않는다.
- 위 수치는 합성 선택 예측 성능이다. 기존 모델과는 정답 생성·데이터가 달라 정확도 수치의 직접 비교는 불가하다.
- 저장 후 재로딩·공통 인코더 추론 일치, 전체 데이터 검사 및 모델 품질 기준 통과
- 12종 UI 입력 진단에서 학습 min/max 범위 밖 특징 없음
- 윤곽만 지정해 중요도 1→5를 바꾸어도 추천 순서가 달라지는 것을 확인

재무·좌석 필수 검사 후 **학습 모델 점수만으로** 순서를 정한다.
예전의 윤곽·가속 일치도 우선 정렬은 이 모델의 서비스에서 사용하지 않는다.
충전 미응답은 충전 불가와 구분하며, 차체 선호와 삭제된 외관 비례는 모델 특징에 없다.
카탈로그·차량 특징·가중치는 metadata.json에 기록한 SHA-256으로 검증한다.

재현 (저장소 루트, PYTHONPATH=ml;.):

```powershell
python -m tools.data.households.generate_ui_scenario_population --output <새-데이터-경로> --profiles 10000
python -m vehicle_matching.train_ui_scenario --data <데이터-경로> --output <새-모델-경로> --epochs 30
```

학습 이력과 평가: training_report.json. 입력 민감도: input_sensitivity_report.json.
서버 기본값: ml/serve-candidates.ps1, 포트 8002.
