# Final_Project

## 실행

### 한 번에 실행 (Docker DB)

Docker, JDK(17 이 없으면 Gradle 이 자동으로 받음), Node.js 가 필요합니다.

```bash
./dev.sh          # MySQL(Docker) + Spring Boot + Vite 실행, Ctrl+C 로 종료
./dev.sh down     # DB 컨테이너 중지 (데이터 유지)
./dev.sh reset    # DB 컨테이너와 데이터 삭제
```

- 프론트: http://localhost:5173 / 백엔드: http://localhost:8080
- Java 파일을 저장하면 서버가 자동 재시작되고, 프론트는 HMR 로 바로 반영됩니다.
- 3306 포트를 이미 쓰고 있으면 `DB_PORT=3307 ./dev.sh` 로 실행합니다.

Windows 는 Git Bash 없이 `dev.cmd` 를 사용합니다. Docker Desktop 을 켠 뒤, 저장소 폴더에서 명령 프롬프트 또는 PowerShell 을 엽니다.

```bat
dev.cmd                 # MySQL(Docker) + Spring Boot + Vite 실행, Ctrl+C 로 종료
dev.cmd down            # DB 컨테이너 중지 (데이터 유지)
dev.cmd reset           # DB 컨테이너와 데이터 삭제
set DB_PORT=3307 && dev.cmd   # 3306 포트를 이미 쓰고 있을 때
```

PowerShell 에서 포트를 바꿀 때는 `$env:DB_PORT = "3307"; .\dev.cmd` 입니다.

### 직접 실행

DB 는 `docker compose up -d` 로 띄우거나, 로컬 MySQL 8 에 `final_sample` DB 와 `server` / `server` 계정을 준비합니다.

```bash
cd back && ./gradlew bootRun
cd front && npm install && npm run dev
```

## DB 스키마

테이블은 서버 시작 시 Flyway 가 `back/src/main/resources/db/migration` 의 SQL 로 자동 생성합니다. 변경 방법은 [back/SCHEMA.md](back/SCHEMA.md) 를 참고하세요.

## 더미 데이터

시드는 `data/seed`, 생성 결과는 `data/generated` 입니다. 생성 결과는 Git에 포함하지 않습니다. 준비 방법과 컬럼 규칙은 [data-generator/README.md](data-generator/README.md) 를 참고하세요.

```bash
cd data-generator
python -m datagen generate --segment domestic-car --rows 100000 --seed 42
python -m datagen generate --segment imported-car --rows 100000 --seed 42
```
