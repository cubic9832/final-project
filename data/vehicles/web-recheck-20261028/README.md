# 추정 제원 웹 재검토 — 2026-10-28

107개 모델군의 기존 카탈로그/공식 페이지를 확인하고, 적용 가능한 자료가 있는 63개 모델군·200개 사양의 추정 항목 651개를 교체했다. 647개는 공식/공인 딜러 자료 참고값, 4개는 비공식 3개 사이트의 제원 일치값이다. 주요 정보 28개 × 323사양의 빈 값은 여전히 0개다.

`vehicles.csv`는 최신 전체 차량 데이터다. 각 항목에 값·상태·출처 수·출처 URL을 저장한다. 상세 조건·원문 수치·중앙값·관찰 범위·이전 추정값은 `vehicles.json`에 남긴다. `changes.json`에는 교체 내역, `remaining-estimates.json`에는 이번 자료에서 교체 근거를 확정하지 못한 5,487개 합성 가정이 있다. 모델군 단위 페이지 확인은 모든 항목의 독립 실측이 확인되었다는 뜻이 아니다.

## 채택 기준

1. 같은 세대·차체·구동/파워트레인·측정 항목의 자료만 사용한다. 차체 공통 치수를 다른 구동 사양에 참고한 경우 범위를 명시한다. 연식 미확인 차량의 표시용 추정 연식을 매칭 증거로 쓰지 않는다.
2. 공식 호환 자료가 있으면 먼저 적용한다. 비공식 자료는 서로 다른 사이트·발행자·확인 가능한 원문 출처가 3개 이상이어야 한다. 번역 페이지·같은 원문 재인용·같은 사이트의 여러 URL로 개수를 늘리지 않는다.
3. 후보 자료 전체의 근접성을 검사하고 중앙값을 저장한다. 유리한 3개만 골라 다른 충돌 수치를 버리지 않는다. 치수는 전체 범위가 `max(10mm, 중앙값의 0.5%)`, 가속은 `max(0.4초, 5%)`, 그 외 수치는 3% 이내여야 한다. 정원은 정확히 일치해야 한다. 같은 제조사의 복사본끼리도 충돌하면 보류한다.
4. 단위 환산은 기록된 경우에만 수행한다. 0–60mph를 0–100km/h로 변환하지 않는다. 건조중량을 공차중량으로 대체하지 않는다. 루프랙·서스펜션·좌석 폴딩 여부, 미러 포함 여부가 다른 값도 무조건 합치지 않는다.
5. `reported-specification`(제원표/공개 보고)과 `instrumented-test`(실측 시험)를 섞지 않는다. **3개 사이트의 공개 제원 일치는 독립 실측 3회가 아니다.** 이번 비공식 채택은 제원표 교차 확인 4개이며, 독립 실측 3회가 확인되어 교체된 가속 항목은 없다.
6. 기존 원장·공식값·사진 평가를 덮어쓰지 않고 합성 추정 항목만 교체한다. 실내·승차감 중립 가정, 개인별 보험료·정비비 등 비교 조건을 확보하지 못한 값은 추정 상태로 유지한다.

비공식 적용 예: GranCabrio 두 사양의 전폭 1,957mm·전고 1,365mm. [CarsGuide](https://www.carsguide.com.au/maserati/grancabrio/car-dimensions), [Goo-net](https://www.goo-net.com/catalog/MASERATI/GRANCABRIO/10156868/), [km77](https://www.km77.com/coches/maserati/grancabrio/2024/estandar/estandar/grancabrio/datos)의 제원표를 대조했다. 지역별 전장 차이와 다른 출력은 가져오지 않았다. 알려진 재인용은 중복 제외하지만, 이 사이트들의 모든 제원이 서로 독립적으로 측정되었다고 확인한 것은 아니다.

## 확인 기록과 한계

- 공식 카탈로그 PDF 74개 재요청: 저장 원문과 같은 해시 60개. 해시가 다르거나 재다운로드할 수 없는 문서는 이전 추출 텍스트를 최신 확인값으로 재사용하지 않았다.
- `official-fetch-audit.json`: 요청별 결과와 모델군별 문서 매칭.
- `official-dimension-reviews.json`: 해시가 동일하고 원장 전장과 차체가 부합하며 값이 하나인 치수만 추출.
- `*reviewed-evidence.json`: 수동 확인 출처·조건·수치.
- `held-family-reviews.json`: Porsche 현재 MY2027/원장 MY2026 차이, Volvo 지원 페이지 MY2027, Maserati 2026년 변경 출력 등 전이를 보류한 사유.
- Ferrari South Bay 12Cilindri Spider 헤더의 가속은 3.0초로 반올림되어 있다. 이를 2.95초 정확값으로 고쳐 쓰지 않고 공개 정밀도를 그대로 보관했다. 딜러의 11686mm 트랙, MINI 페이지의 741kg 중량 등 명백히 의심스러운 수치는 사용하지 않았다.

원본 재무 카탈로그와 필수 탑승 인원/구매 적격 검증은 유지한다. 웹 참고 제원과 추정 비용을 구매 가능 증거로 자동 승격하지 않는다.

## 재현

```powershell
$env:PYTHONPATH='ml'
python -m tools.data.vehicles.recheck_official_dimensions
python -m tools.data.vehicles.build_rechecked_specifications
python -m tools.data.households.generate_preference_cohorts --traits data/vehicles/web-recheck-20261028/vehicle_traits.json --output data/households/synthetic/preference-cohorts-web-recheck-final-20261028
python -m vehicle_matching.train_preference_cohorts --data data/households/synthetic/preference-cohorts-web-recheck-final-20261028 --output ml/outputs/models/preference-cohorts/20261028-v6-web-recheck
```

공식 웹 문서가 바뀌면 채택 수가 달라질 수 있다. 수동 레지스트리는 확인한 원문의 수치만 수정한다. 재학습 출력은 기존 폴더 대신 새 버전을 지정한다. 현재 기본 모델은 v6이며, 합성 정책 재현용 학습 지표를 실제 사람의 만족도 정확도로 해석하지 않는다.
