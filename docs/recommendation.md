# 차량 추천 실행과 API

현재 구현은 `ml/vehicle_matching`, 모델은 `ml/outputs/models/candidate-preferences/20261027-seating-verified-v1`이다. 설치·재학습은 [ML 안내](../ml/README.md)를 따른다.

루트 `dev.ps1` 또는 `./ml/serve-candidates.ps1`로 8002 서버를 실행한다. 프런트엔드 Vite의 `/api/v2` 프록시는 이 서버로 요청을 보낸다. 배포 시에도 동일 경로를 추천 API로 전달해야 한다.

- `POST /api/v2/recommendations`: `{profile: {...}, k: 3}`. 프로필 예시는 `ml/examples/candidate-profile.json`이다.
- `GET /api/v2/recommendation-options`: 후보·입력·정책 정보.
- 요청 스키마와 응답 상세는 서버 `/docs`와 `ml/vehicle_matching/api.py`를 따른다.
- 실패는 HTTP 상태 코드와 `application/problem+json`을 사용한다.

현재 모델은 합성 비교 정답을 학습했다. 재무 조건과 필수 정원·선호 중요도 및 ML 점수를 사용하며 점수는 구매·만족 확률이 아니다.

구형 v1 문서는 [작업 기록](../ml/legacy/history/recommendation-v1.md)에 보관했다. v1 서버는 기본 개발 실행에 포함하지 않는다.
