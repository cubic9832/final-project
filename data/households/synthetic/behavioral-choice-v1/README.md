# 행동 기반 합성 비교 데이터 생성

설계 규칙은 [rules.txt](rules.txt), 생성기는 `tools/data/households/generate_behavioral_choices.py`다.
기본 입력은 현재 Spring 서버에 등록된 차량의 추천 카탈로그다. 서버를 사용할 수 없으면 실패하며 과거 차량 목록으로 자동 대체하지 않는다.

저장소 루트 PowerShell에서 ML 가상환경을 사용한다.

```powershell
$env:PYTHONPATH = "$PWD/ml;$PWD"
& ./ml/.venv/Scripts/python.exe -m tools.data.households.generate_behavioral_choices --output data/households/synthetic/behavioral-choice-v1-run-20261028 --groups 25000
```

25,000개 재무 그룹마다 4개 선호 프로필을 시도한다. 중복과 적격 모델 2개 미만 사례는 학습에서 제외하므로 저장 프로필 수는 100,000개보다 적을 수 있다. 프로필별 비교는 최대 8쌍이며 차량별 수량이나 승리는 강제하지 않는다. 기존 경로 덮어쓰기는 거부한다.

서버 없이 재현할 때는 명시적으로 스냅샷을 선택한다. 이 경우 해당 파일이 현재 DB 차량을 나타낸다고 주장하지 않는다.

```powershell
& ./ml/.venv/Scripts/python.exe -m tools.data.households.generate_behavioral_choices --catalog path/to/catalog.json --output tmp/behavioral-offline --groups 100
& ./ml/.venv/Scripts/python.exe -m unittest tools.data.households.tests.test_behavioral_choices -v
```

기존 규칙 중 재무 분포·현금 구매·12개월 부족액 보전·필수 좌석·선호 선생성·그룹 분리를 유지한다. 기존의 결정적 정답·선호 우선 정렬·스포츠 차량별 10,000건 할당·과거 자료 병합과 미학습 차량 목록은 새 규칙으로 대체한다. 충돌을 그대로 병용할 수 없으므로 실행 폴더의 `rules.txt`에 우선순위를 기록하고 두 원문도 복사한다. 분할은 그룹 해시 기반 70/15/15 확률 배정이며 정확한 행 수 비율을 강제하지 않는다.

산출물:

- `catalog.json`: 이번 생성에서 고정한 전체 차량 스냅샷.
- `*_profiles.jsonl`: 학습·검증·평가의 입력과 그룹 ID.
- `*_choices.npz`: `features`, `comparisons`, `labels`, `profile_ids`, `vehicle_indices`. 비교 인덱스는 특징 행을 가리키고, label 1은 A 선택, 0은 B 선택이다. 특징은 정규화 전 값이며 이후 학습 분할로만 정규화한다.
- `*_audit.jsonl`: 잠재 성향·효용·선택 확률·난수. 학습 입력에서 제외한다.
- `excluded_profiles.jsonl`: 적격 모델 부족 사례와 제외 사유.
- `generation_report.json`: 시드·분포 설정·계보·파일 해시·노출/승리 수.
- `saved_data_audit.json`: 저장 후 재검수 결과.

기존 `*_pairs.npz`의 교사 점수 targets와 의미가 다르므로 기존 학습기에 바로 넣지 않는다. 이후 학습기는 `sigmoid(score_A-score_B)`와 이진 선택 label을 사용해야 한다. 이 명령은 더미 데이터 생성과 검수만 수행하며 모델 학습이나 서비스 전환은 하지 않는다.
