# React 차량 추천

## 실행

저장소 루트의 첫 번째 PowerShell에서 서버 의존성을 설치하고 추천 API를 실행한다.

```powershell
& ./ml/.venv/Scripts/python.exe -m pip install -e "./ml[serve,test]"
./ml/serve.ps1
```

두 번째 터미널에서 프런트를 실행하고 `http://localhost:5173/predict`로 접속한다.

```powershell
npm --prefix front run dev
```

국내차·수입차를 선택해 조건을 입력하거나 `예시 조건 채우기`를 사용한다. 실제 모델 결과를 표시하며, 오류를 샘플 추천으로 대체하지 않는다. 추천 화면만 실행할 때에는 Spring·MySQL이 필요하지 않다. 기존 카탈로그·재무 기능은 루트 README의 실행 방법을 따른다.

## 모델 선택

모델 학습은 [ML 안내](../ml/README.md)를 따른다. API는 시작할 때 `ml/outputs/models/{segment}`의 최신 시각별 폴더를 읽는다. 시각별 폴더가 없으면 다른 폴더를 이름 역순으로 선택한다. 모델 변경 후에는 API를 재시작한다. 로딩 실패 시 다른 모델로 조용히 대체하지 않고 해당 구분의 사용 불가를 표시한다.

특정 모델을 고정할 때는 서버 시작 전에 절대 경로를 지정한다.

```powershell
$env:ML_DOMESTIC_RUN = 'C:\workspace\final-project\ml\outputs\models\domestic-car\20261019T102520'
$env:ML_IMPORTED_RUN = 'C:\workspace\final-project\ml\outputs\models\imported-car\20261019T102526'
./ml/serve.ps1
```

모델 폴더에는 `model.pt`, `model.json`, `preprocessor.json`이 필요하다. 매 요청마다 다시 학습하거나 모델 파일을 읽지 않는다.

## 입력과 결과

- 금액은 만 원으로 입력하며 React가 원 단위로 변환한다. 소득은 연간 세전소득, 지출·저축은 월 기준이다.
- 재무 진단의 월 실수령액을 세전 연봉으로 자동 변환하지 않는다. 추천 전용 폼에서 필요한 값을 직접 입력한다.
- 성별·직업·목적은 선택한 모델의 학습 범주를 선택지로 제공한다.
- 요청 중 폼을 비활성화하고 중복 전송을 막는다. 오류 시 입력을 유지하며 다시 요청할 수 있다. 입력 변경 시 이전 조건의 추천 결과를 지운다.
- 결과는 차종 후보와 모델 예측 확률이다. 가격·트림·월 부담·DB 차량 상세 매칭이나 구매 가능 판단은 포함하지 않는다. 확률은 적합도나 구매 가능 확률이 아니다.
- 입력은 브라우저 메모리와 추론 요청에서만 사용한다. 이 기능은 파일·DB·localStorage에 프로필을 저장하지 않고 서버 로그에도 요청 본문을 기록하지 않는다.

## API 계약

개발 시 Vite는 아래 두 경로를 `127.0.0.1:8001`로 전달한다. 나머지 `/api`는 기존 Spring 서버로 전달한다.

| 메서드와 경로 | 용도 |
| --- | --- |
| GET `/api/v1/recommendation-options` | 구분별 모델 사용 가능 여부와 범주 선택지 |
| POST `/api/v1/recommendations` | `{segment, profile, k: 3}`로 추천 요청 |

`segment`는 `domestic-car` 또는 `imported-car`다. `profile`의 키와 원 단위 예시는 `ml/examples/profile.json`을 따른다.

성공은 `200`과 `{success: true, data: ...}`다. 추천 데이터는 `segment`, `modelVersion`, `recommendations`를 포함한다. 각 차량은 `labelCode`, `model`, `body`, `grade`, `probability`를 제공한다.

실패는 `application/problem+json`이다. 입력 오류 `400`, 모델 사용 불가 `503`, 내부 처리 실패 `500`을 구분한다. 필드 오류 확장은 `errors: [{field, message}]`다. 서버가 꺼져 있으면 프런트에서 연결 실패와 재시도를 안내한다.

API는 로컬 개발용으로 `127.0.0.1`에 바인딩한다. 운영 배포에서는 웹 서버나 Spring 게이트웨이가 같은 두 경로를 Python 서비스로 전달하도록 구성해야 한다. Vite 개발 프록시는 운영 빌드에 포함되지 않는다.

## 검증

```powershell
npm --prefix front test
npm --prefix front run lint
npm --prefix front run build
Set-Location ml
./.venv/Scripts/python.exe -m unittest discover -s tests
```

실제 브라우저에서 국내·수입 Top 3 표시, 필수값 오류, 서버 종료 시 연결 실패·입력 보존·서버 복구 후 재요청을 확인했다.
