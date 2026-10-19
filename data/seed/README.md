# 차량 추천 기준 데이터

`feat/data`의 ML 구현과 함께 가져온 국내 10,000명·수입차 6,000명의 합성 기준 데이터다. 각 세그먼트의 `owners.csv`와 `purchases.csv`를 프로필 ID로 연결한다. `owner-summary.csv`는 설명용이며 모델 학습에는 사용하지 않는다.

기존 `data/households/synthetic` 파일을 이동하거나 덮어쓰지 않는다. 생성·변환 코드의 위치는 `tools/data`이며, 두 스키마를 혼동하지 않도록 모델 실행 시 입력 디렉터리를 명시한다. 실제 구매 기록이 아닌 합성 자료다.
