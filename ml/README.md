# 차량 보유자 특성 기반 머신러닝

현재는 폴더 구조와 데이터 경로 설정만 만든 준비 단계다. 데이터 로딩·전처리·모델 학습·평가·추론은 아직 구현하지 않았으며, 모델 설치나 학습도 실행하지 않았다. train/evaluate/predict 실행 시 구현 전 안내와 함께 종료한다.

## 구조

```text
ml/
├─ .gitignore
├─ requirements.txt
├─ README.md
├─ config/
│  └─ datasets.json
├─ vehicle/
│  ├─ __init__.py
│  ├─ train.py
│  ├─ evaluate.py
│  └─ predict.py
└─ outputs/
   ├─ models/
   └─ reports/
```

train/evaluate/predict는 각각 학습·평가·추론의 미구현 안내 진입점이다. 데이터 로딩·전처리·모델 정의 모듈은 실제 구현 시 필요한 책임에 따라 추가하며, 빈 역할 모듈을 미리 만들지 않는다. 학습·추론 코드는 import만으로 실행하지 않는다. tests에는 추후 데이터 누출 방지·전처리 일관성·추론 등 핵심 동작 테스트만 추가한다.

데이터 생성·정제 소스는 `tools/data/`, 기존 학습 CSV와 생성 규칙은 `data/`에서 관리한다. 실행 방법은 [데이터 도구](../tools/data/README.md)를 참고한다.

## 데이터 연결

`config/datasets.json`은 저장소 루트 기준 상대 경로로 기존 학습 CSV 4개를 가리킨다. 합성 국내 100,000명과 수입차 96,000명, 합계 196,000명·20개 모델이다. 데이터 파일은 기존 data 폴더에 유지하며 ml 아래로 복제하지 않는다.

목표는 개인 특성으로 비슷한 보유자 집단의 차량을 추천하는 것이다. 정답은 보유차량_라벨코드다. 기존 데이터_구분의 학습/검증/평가를 유지한다. 구매 내역·모델명·브랜드·차체·차급 등 정답 관련 항목과 프로필 ID·시드·버전 등 관리 항목은 학습 입력에서 제외한다. 전처리나 집단 프로토타입은 학습 구간으로만 계산한다.

전체 자료는 가상 규칙으로 생성했다. 평가 점수는 합성 패턴의 학습 결과이며 실제 구매 경향·구매 자격을 검증하는 수치가 아니다.

## 환경 준비 방법

아래는 추후 설치할 때 사용할 PowerShell 명령이다. 저장소 루트에서 실행하며 이번 구조 생성 작업에서 실행한 명령은 아니다.

```powershell
python -m venv ml/.venv
& ./ml/.venv/Scripts/python.exe -m pip install -r ml/requirements.txt
```

초기 의존성은 pandas, NumPy, scikit-learn, CatBoost다. 설치 환경의 호환성을 확인한 뒤 버전을 고정한다. 딥러닝 비교가 실제 구현 범위에 들어오면 PyTorch 등의 의존성을 추가한다.

## 구현 후 실행할 진입점

ml 폴더를 작업 디렉터리로 삼아 모듈 방식으로 실행할 예정이다. 현재는 모두 미구현 상태다.

```powershell
Set-Location ml
python -m vehicle.train
python -m vehicle.evaluate
python -m vehicle.predict
```

모델과 전처리 메타데이터는 outputs/models, 지표와 혼동행렬 등은 outputs/reports에 저장한다. 가상환경·캐시·환경변수 파일·생성된 모델과 보고서는 ml/.gitignore로 제외한다. 빈 출력 폴더만 .gitkeep으로 유지하며 완료된 것처럼 보이는 모델이나 평가 결과는 만들지 않는다.
