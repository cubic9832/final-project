# Final_Project

폴더별 역할과 데이터 관리 경계는 [프로젝트 구조](docs/structure.md), 데이터 생성·변환 방법은 [데이터 도구](tools/data/README.md), 머신 러닝 실행 방법은 [ML 안내](ml/README.md)를 참고하세요.

재무 진단 UI는 유지하며, 마지막 페이지의 **추천 차량 확인하기** 버튼을 눌렀을 때만 ML 추천을 표시합니다. [실행 방법](docs/recommendation.md)을 참고하세요.

## 실행

### Elasticsearch·Kibana (Docker 자동 실행)

`dev.ps1`·`dev.cmd`·`dev.sh` 실행 시 MySQL과 함께 Elasticsearch(9200, 한국어 분석기 nori 포함)와 Kibana(5601)도 Docker로 자동 실행됩니다. 첫 실행 때 nori 를 설치한 이미지를 빌드하므로 몇 분 걸릴 수 있으며, Docker Desktop 메모리는 4GB 이상을 권장합니다. 개발용이라 보안을 끈 단일 노드이며 인증 없이 http://localhost:9200 으로 접속합니다. 9200 포트를 이미 쓰고 있으면 `ES_PORT=9201` 환경변수로 바꿉니다. 직접 띄울 때는 `docker compose up -d` 로 MySQL·Elasticsearch·Kibana를 모두 시작합니다.

### Windows PowerShell에서 전체 실행

프로젝트 루트에서 실행합니다. Node.js, Java, ML 가상환경·패키지·학습 모델([초기 준비](ml/README.md))이 필요합니다.

```powershell
.\dev.ps1
```

React(5173)·Spring(8080)·Python 추천 서버(8002)를 함께 실행합니다. 이미 사용 중인 포트는 기존 프로세스를 재사용하므로 해당 포트가 이 프로젝트 서버인지 확인하세요. 프로젝트 MySQL(3307)이 실행 중이면 그대로 사용하고, 없으면 Docker Desktop을 통해 프로젝트 DB를 시작합니다. DB 계정·스키마는 아래 직접 실행 설정과 같습니다.

터미널을 열어 둔 채 사용하며, Ctrl+C를 누르면 이번 실행으로 새로 켠 앱 서버와 하위 프로세스만 종료합니다. 기존 서버와 DB는 유지합니다. 로그는 `tmp/dev/<실행시각>/`에 저장됩니다. 처음 실행할 때만 프런트 의존성이 없으면 `npm ci`를 수행하며, ML 설치·모델 학습은 자동으로 하지 않습니다.

```powershell
.\dev.ps1 -Check                  # 서버를 켜지 않고 실행 준비 확인
.\dev.ps1 -DatabasePort 3308      # 다른 MySQL 포트 사용
```

명령 프롬프트에서는 기존 `dev.cmd`도 동일한 스크립트를 호출합니다.

```bat
dev.cmd                 # MySQL + Spring + React + Python 추천 서버
dev.cmd down            # 프로젝트 DB 컨테이너 중지 (데이터 유지)
dev.cmd reset           # 프로젝트 DB 컨테이너와 데이터 삭제
set DB_PORT=3308 && dev.cmd
```

PowerShell에서는 `.\dev.ps1 down`, `.\dev.ps1 reset`도 사용할 수 있습니다. `-DatabasePort`를 생략하면 `DB_PORT` 환경변수를 사용하며, 둘 다 없으면 3307입니다. `reset`은 DB 데이터를 삭제하므로 재초기화할 때만 사용하세요. Spring을 새로 켜는 경우 Java 소스의 연속 컴파일도 실행해 저장 시 DevTools 자동 재시작을 유지합니다.

스크립트 실행 정책으로 차단되는 경우 이 실행에만 적용합니다.

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\dev.ps1
```

### Git Bash에서 실행 (Docker DB·Spring·React)

Docker, JDK(17 이 없으면 Gradle 이 자동으로 받음), Node.js 가 필요합니다.

```bash
./dev.sh          # MySQL(Docker) + Spring Boot + Vite 실행, Ctrl+C 로 종료
./dev.sh down     # DB 컨테이너 중지 (데이터 유지)
./dev.sh reset    # DB 컨테이너와 데이터 삭제
```

- 프론트: http://localhost:5173 / 백엔드: http://localhost:8080
- Java 파일을 저장하면 서버가 자동 재시작되고, 프론트는 HMR 로 바로 반영됩니다.
- 3307 포트를 이미 쓰고 있으면 `DB_PORT=3308 ./dev.sh` 로 실행합니다.
- Windows 는 Git Bash 에서 실행합니다.
- 이 Bash 스크립트에는 추천 서버가 포함되지 않습니다. 추천까지 함께 켜려면 위의 `dev.ps1`을 사용하세요.

### 직접 실행

DB 는 기본 호스트 포트 3307에서 `docker compose up -d` 로 띄우거나, 같은 포트의 로컬 MySQL 8 에 `final_sample` DB 와 `server` / `server` 계정을 준비합니다.

```bash
cd back && ./gradlew bootRun
cd front && npm install && npm run dev
```

## 회원 인증 키 (환경변수)

로그인 · 회원가입의 외부 서비스 키는 **코드 · DB · git 에 넣지 않고 환경변수로만** 줍니다. 키가 없어도 아래처럼 개발 모드로 동작하므로, 조원은 키 없이 그대로 실행하면 됩니다.

| 환경변수 | 쓰는 곳 | 없을 때 (개발 모드) |
|---|---|---|
| `MAIL_USERNAME` · `MAIL_PASSWORD` | 이메일 인증 메일 발송 (Gmail 계정 · 앱 비밀번호) | 메일을 보내지 않고 **서버 로그에 인증 코드** 출력: `[DEV-MAIL] email verification code=123456 to=…` |
| `RECAPTCHA_SECRET_KEY` (백) · `VITE_RECAPTCHA_SITE_KEY` (프론트) | 로그인 3번 실패 후 reCAPTCHA | 구글 공식 테스트 키 (체크만 하면 통과) |
| `GOOGLE_CLIENT_ID` (백) · `VITE_GOOGLE_CLIENT_ID` (프론트) | 구글 로그인 | 구글 버튼이 "설정 필요" 로 비활성 |
| `JWT_SECRET` · `JWT_COOKIE_SECURE` | 토큰 서명 키 · HTTPS 쿠키 | 로컬용 값 · `false` (배포 때 꼭 바꾸기) |

- 개발 모드 회원가입: 이메일 [인증 코드 받기] → 백엔드 콘솔(또는 `tmp/dev/…` 로그)에서 `DEV-MAIL` 줄의 6자리 코드를 찾아 입력합니다.
- 프론트 키(`VITE_…`)는 `front/.env.local` 에 적습니다. `.env.*` 는 git 에서 제외됩니다.
- 백엔드 키는 서버를 켜는 터미널에서 넣습니다. 비밀번호가 명령 기록에 남지 않게 `read -s` 로 입력합니다.

```bash
export MAIL_USERNAME=보내는계정@gmail.com
read -s -p "Gmail 앱 비밀번호: " MAIL_PASSWORD; echo; export MAIL_PASSWORD
DB_PORT=3308 ./dev.sh
```

## DB 스키마

테이블은 서버 시작 시 Flyway 가 `back/src/main/resources/db/migration` 의 SQL 로 자동 생성합니다. 변경 방법은 [back/SCHEMA.md](back/SCHEMA.md) 를 참고하세요.
