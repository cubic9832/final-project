# 공식 쿠페·오픈카 학습 보강

신규 11개 모델군 × 10,000건 = 110,000건의 독립 입력 기반 적격 비교 사례.
학습 77,190건, 검증 16,360건, 평가 16,450건으로 나눴다. 모델군 안의 세부 트림은 무작위 선택한다. 실제 구매 이력이나 차량별 10,000회의 승리라는 뜻은 아니다.

기존 `seating-verified-v1-20261027`의 카탈로그 282개 사양과 비교 배열을 보존하고 공식 검토 신규 22개 사양을 더해 학습 카탈로그는 304개 사양이다. 운영 DB 308개 사양과 서로 다른 스냅샷이므로 308+22로 합산하지 않는다.

기존 규칙 원문과 이번 적용 차이는 `rules.txt`에 있다. 생성 및 원본 해시는 `generation_report.json`, 저장 후 재검수는 `saved_data_audit.json`에 기록했다. 110,000건 전체에서 중복 입력, 신규 재무 그룹 분할 누수, 부적격 비교, 정답 순서 오류는 0건이었다.

생성·학습 명령(새 출력 경로 필요):

```powershell
$env:PYTHONPATH='ml'
ml/.venv/Scripts/python.exe -m vehicle_matching.train_sports_population --source data/households/synthetic/seating-verified-v1-20261027 --supplement data/vehicles/sports-catalog-20261028/catalog.json --data data/households/synthetic/sports-official-v1-20261028 --output ml/outputs/models/candidate-preferences/20261028-sports-official-v1 --old-model ml/outputs/models/candidate-preferences/20261027-seating-verified-v1 --per-model 10000 --epochs 12
```

이 모델별 수량은 사용자가 요청한 합성 학습 노출량이며 시장 점유율을 반영하지 않는다. 신모델은 학습에도 등장하므로 평가 결과는 미학습 차량 일반화 성능이 아닌 미학습 재무 그룹에 대한 합성 정책 일치도다. 좌석/길이 누락과 유지비 가정의 한계는 차량 카탈로그 README를 참고한다.
