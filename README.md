# Final_Project

폴더별 역할과 데이터 관리 경계는 [프로젝트 구조](docs/structure.md), 데이터 생성·변환 방법은 [데이터 도구](tools/data/README.md), 머신 러닝 실행 방법은 [ML 안내](ml/README.md)를 참고하세요.

재무 진단을 마치면 같은 결과 화면에서 실제 모델의 차량 추천을 확인할 수 있습니다. [실행 방법](docs/recommendation.md)에 따라 추천 API와 프런트를 함께 실행한 뒤 `/financial`로 접속합니다.

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
- Windows 는 Git Bash 에서 실행합니다.

### 직접 실행

DB 는 `docker compose up -d` 로 띄우거나, 로컬 MySQL 8 에 `final_sample` DB 와 `server` / `server` 계정을 준비합니다.

```bash
cd back && ./gradlew bootRun
cd front && npm install && npm run dev
```

## DB 스키마

테이블은 서버 시작 시 Flyway 가 `back/src/main/resources/db/migration` 의 SQL 로 자동 생성합니다. 변경 방법은 [back/SCHEMA.md](back/SCHEMA.md) 를 참고하세요.
