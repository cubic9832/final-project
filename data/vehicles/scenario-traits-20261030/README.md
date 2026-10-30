# 시나리오 추천의 차량 성향 자료

현재 모델 카탈로그 96모델·308사양의 외관 스타일, 차체 윤곽, 가속 성능을 모두 연결한다.
학습 체크포인트와 학습 카탈로그는 변경하지 않는다.

- 282사양의 기존 대표 이미지 외관 평가를 보존했다. 개별 트림의 실물 검증은 아니다.
- 나머지 26사양의 외관·윤곽은 차체 분류에 따른 명시적인 자체 가정이다.
  `editorial-body-prior`이며 사진을 검토한 평가로 표시하지 않는다.
- 가속 3사양은 기존 공식 자료, 305사양은 차체·연료 등에 따른 미검증 추정값이다.
  추정 범위는 통계적 신뢰구간이 아니며 실제 성능을 보장하지 않는다.
- 각 값의 근거, 방법, 가정 입력, 한계는 `evidence`에 기록한다.
- coverage_report.json은 308사양의 세 필드 커버리지와 입력 파일 해시를 기록한다.

재생성: 루트에서 `PYTHONPATH=ml;.`를 설정하고
`python -m tools.data.vehicles.build_scenario_traits` 실행.

## 추천 계약

`scenario`는 sportiness/angularity/acceleration(0~1 또는 null),
design_importance/performance_importance(1~5),
asset_retention_importance/running_cost_importance(1~5 또는 null)를 받는다.
알 수 없는 필드와 범위 밖 입력은 HTTP 400 Problem Details로 반환한다.

자금 보존·유지비 중요도는 기존 모델의 관측 가능한 중요도 특징에 연결한다.
외관·윤곽·가속은 기존 68입력 모델이 학습하지 않았으므로 사용자별 명시적인
가중 일치도를 우선 비교하고 동률일 때 모델 점수로 정렬한다. 구매·유지비·좌석의
필수 검사는 항상 먼저 적용한다. 전체 적격 사양에서 정렬한 뒤 모델별 한 사양을 고른다.
`rankingScore`는 변형하지 않은 기존 모델 원본 점수다. 학습 성능 향상으로 해석하지 않는다.
`rankingPolicy`, `tasteMatches`, `lifestyleEvidence`로 별도 정렬과 근거를 노출한다.
