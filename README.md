# Final_Project

폴더별 역할과 데이터 관리 경계는 [프로젝트 구조](docs/structure.md), 데이터 생성·변환 방법은 [데이터 도구](tools/data/README.md), 머신 러닝 실행 방법은 [ML 안내](ml/README.md)를 참고하세요.

재무 진단 UI는 유지하며, 마지막 페이지의 **추천 차량 확인하기** 버튼을 눌렀을 때만 ML 추천을 표시합니다. [실행 방법](docs/recommendation.md)을 참고하세요.

## 실행

### Windows PowerShell에서 전체 실행

프로젝트 루트에서 실행합니다. Node.js, Java, ML 가상환경·패키지·학습 모델([초기 준비](ml/README.md))이 필요합니다.

```powershell
.\dev.ps1
```

React(5173)·Spring(8080)·Python 추천 서버(8001)를 함께 실행합니다. 이미 사용 중인 포트는 기존 프로세스를 재사용하므로 해당 포트가 이 프로젝트 서버인지 확인하세요. MySQL(3306)이 실행 중이면 그대로 사용하고, 없으면 Docker Desktop을 통해 프로젝트 DB를 시작합니다. DB 계정·스키마는 아래 직접 실행 설정과 같습니다.

터미널을 열어 둔 채 사용하며, Ctrl+C를 누르면 이번 실행으로 새로 켠 앱 서버와 하위 프로세스만 종료합니다. 기존 서버와 DB는 유지합니다. 로그는 `tmp/dev/<실행시각>/`에 저장됩니다. 처음 실행할 때만 프런트 의존성이 없으면 `npm ci`를 수행하며, ML 설치·모델 학습은 자동으로 하지 않습니다.

```powershell
.\dev.ps1 -Check                  # 서버를 켜지 않고 실행 준비 확인
.\dev.ps1 -DatabasePort 3307      # 다른 MySQL 포트 사용
```

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
- 3306 포트를 이미 쓰고 있으면 `DB_PORT=3307 ./dev.sh` 로 실행합니다.
- Windows 는 Git Bash 에서 실행합니다.
- 이 Bash 스크립트에는 추천 서버가 포함되지 않습니다. 추천까지 함께 켜려면 위의 `dev.ps1`을 사용하세요.

### 직접 실행

DB 는 `docker compose up -d` 로 띄우거나, 로컬 MySQL 8 에 `final_sample` DB 와 `server` / `server` 계정을 준비합니다.

```bash
cd back && ./gradlew bootRun
cd front && npm install && npm run dev
```

## DB 스키마

테이블은 서버 시작 시 Flyway 가 `back/src/main/resources/db/migration` 의 SQL 로 자동 생성합니다. 변경 방법은 [back/SCHEMA.md](back/SCHEMA.md) 를 참고하세요.
