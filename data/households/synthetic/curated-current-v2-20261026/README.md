# 현재 정책 정제 데이터

생성·선별·분류의 상세 기준은 [rules.txt](rules.txt)에 있다. 예전 차량 정답은 재사용하지 않고, 재무·선호 입력만 가져와 현재 규칙으로 비교 정답을 다시 만들었다.

| 역할 | 입력 사례 수 | 비교 쌍 수 | 파일 |
| --- | ---: | ---: | --- |
| 학습 | 155,599 | 1,224,642 | training.csv / train_profiles.jsonl / train_pairs.npz |
| 검증 | 28,016 | 220,074 | validation.csv / validation_profiles.jsonl / validation_pairs.npz |
| 평가 | 47,729 | 373,926 | evaluation.csv / test_profiles.jsonl / test_pairs.npz |
| 재무 검증 | 13,052 | 사용하지 않음 | financial_validation.csv / financial_profiles.jsonl |
| 별도 1원 경계 검증 | 2,529 | 사용하지 않음 | financial_boundary_cases.csv |

입력 사례 합계는 **244,396행**이며, 경계 검증 2,529건은 별도다. 기존 306,429행에서 178,508행, 신규 100,000행에서 65,888행을 남겼다. 같은 입력의 서로 다른 차량을 비교한 쌍 수와 사람의 입력 사례 수를 혼동하지 않는다.

CSV는 사람이 확인할 요약이고 JSONL은 정확한 입력, NPZ는 실제 학습용 특징·정답·비교 인덱스다. CSV의 확률적 선택 차량을 분류 라벨로 쓰지 않는다. 비교 학습에는 적격 후보가 둘 이상이고 점수 차이가 있는 사례만 들어간다.

검증 결과는 `validation_report.json`, 출처 해시·제외 사유·분할·학습 기록은 `refinement_report.json`, 이전 모델과 같은 평가 입력을 사용한 비교는 `balanced_evaluation_report.json`에 있다.

통합본 학습 모델은 `ml/outputs/models/candidate-preferences/20261026-refined-v1`에 저장했다. 신규·기존 입력 각 150개에서 기존 32비트 sigmoid 점수로 평가하면 ML 단독 NDCG@3은 이전 0.9188 → 통합 0.8325였지만, 출력 포화로 순위가 손실된 수치였다. 원본 출력으로 수정한 재평가는 이전 0.9977 → 통합 0.9989다. 최종 추천 NDCG@3은 양쪽 모두 약 1.0이고 재무 위반은 0건이었다. **실행 모델은 교체하지 않았다.** 점수는 합성 평가 규칙과의 일치도이며 사용자 만족도나 실제 구매 정확도가 아니다.

재학습은 저장소의 `ml` 폴더에서 실행한다.

```powershell
./.venv/Scripts/python.exe -m vehicle_matching.train_curated_population --data-dir ../data/households/synthetic/curated-current-v2-20261026 --output outputs/models/candidate-preferences/새실행폴더
```

이 정제본과 카탈로그만 있으면 재학습할 수 있다. 과거 원천을 다시 선별해야 하는 경우에만 `rules.txt`에 기록된 원격 Git 커밋의 원천을 별도 경로에 복구한다. 과거 실험 자료는 현재 폴더에 중복 보관하지 않는다.
