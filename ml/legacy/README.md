# 구형 ML 보관

현재 추천 서비스에서는 사용하지 않는 v1 라벨 분류 모델과 작업 기록이다. 과거 데이터 누수 방지·모델 재로딩 검증 및 품질 실험 재현을 위해 보존했다. 현재 실행은 상위 README를 따른다.

- `recommender/`: 구형 v1 구현. 내부 import는 `legacy.recommender`로 변경했다.
- `tests/`: 구형 구현에 대응하는 테스트 5개와 공통 fixture.
- `train_quality_choices.py`: 과거 라벨 분류 실험. 기본 데이터가 삭제된 과거 경로이므로 현재 재학습에 사용하지 않는다.
- `history/`: 이전 README 및 v1 API 안내 원문. 문서 안 경로·명령은 당시 위치이며 현재 실행 지침이 아니다.
- `serve-v1.ps1`: 과거 서버가 필요한 경우에만 수동 실행한다(8001).

프로젝트 루트에서 `$env:PYTHONPATH = "$PWD/ml;$PWD"` 설정 후 `python -m legacy.recommender --help`로 구형 CLI를 확인할 수 있다. 기존 `recommender` 콘솔 명령도 보관된 CLI를 가리킨다(패키지 재설치 필요).
