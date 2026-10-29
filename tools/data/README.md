# 데이터 도구

저장소 루트에서 Python 모듈로 실행한다. 데이터는 `data/`에 유지하며 소스는 이 폴더에서 관리한다. Python 3.10 이상, CSV 변환은 Node.js 18 이상을 사용한다.

```powershell
python -m pip install -r tools/data/requirements.txt
python -m tools.data.vehicles.normalize_vehicle_details
python -m tools.data.households.generate_profiles --count 1000 --output pilot
node tools/data/csv/exportSyntheticCsv.mjs --korean
python -m unittest discover -s tools/data/households/tests -t .
python -m unittest tools.data.vehicles.test_normalize_vehicle_details
```

CSV 변환은 Node.js 기본 모듈만 사용한다. npm 설치나 Codex 전용 런타임은 필요하지 않다. 각 exporter는 기존 JSON을 읽어 기존 CSV 경로에 기록한다. `exportSyntheticCsv`는 `generated/dataset.json`을 읽으므로 pilot 생성과 별개이며, 전체 데이터를 다시 생성한 뒤 사용한다.

- `households/`: 합성 프로필·보유자·구매 자금 생성과 보정. 공통 데이터 경로는 `paths.py`에서 관리한다.
- `households/tests/`: 합성 데이터의 재현성·금액·제약 검증.
- `vehicles/`: 공식 차량 자료 수집·정제·검증.
- `statistics/`: 공식 가구 통계 수집·추출.
- `purchasepatterns/`: 구매 경향 자료 수집.
- `csv/`: JSON에서 배포용 CSV 생성.

현재 등록 차량으로 확률적 비교 선택 데이터를 생성하는 도구는
`households/generate_behavioral_choices.py`다. 실행 방법과 두 규칙의 충돌 처리,
새 학습 스키마는 [행동 기반 데이터 안내](../../data/households/synthetic/behavioral-choice-v1/README.md)를 따른다.

전체 데이터 생성은 기존 산출물을 덮어쓴다. 단순 구조 검증에는 위 테스트를 사용하며 데이터 전체를 재생성하지 않는다.

디자인·실내·사용 목적·주행 취향과 고급 차량 조사 후보를 포함한 실험 데이터는
`households/generate_lifestyle_choices.py`로 생성한다. 새 출력 폴더를 요구하며 기존 데이터를
덮어쓰지 않는다. [데이터 설명과 재현 명령](../../data/households/synthetic/lifestyle-choice-v2-evidence-20261028/README.md)에
공식 제원·사진 검수 근거, 미확인 항목의 양쪽 마스킹, 취향 전용 비교와 구매 적격 비교의 구분을 명시했다.
난수 차량 특성을 사용하던 v1 자료는 사용 중단했다.
