# 프로젝트 구조와 관리 경계

```text
front/src/
  features/{vehicle,financial,company,preset}/  기능별 코드
  shared/api/                                공통 HTTP 클라이언트
  pages/{home,about,login,...}/               독립 화면별 JSX·CSS
  components/                                공통 레이아웃
  styles/                                    전역 스타일과 테마
back/src/main/java/com/kh/back/
  {vehicle,company}/                          기능별 Java 코드
  common/                                    공통 응답과 오류 처리
tools/data/                                  데이터 수집·생성·정제·CSV 코드
data/                                        데이터·생성 규칙·출처·검증 기록
ml/                                          향후 모델 학습·평가·예측
output/                                      공유할 검토 문서 산출물
examples/legacy/                              기존 독립 Java 예제 보존
tmp/                                         재생성 가능한 로컬 임시 자료 (Git 제외)
```

## 프런트엔드 화면 배치

```text
features/financial/
  pages/
    overview/FinancialPage.jsx
    assets/{FinancialAssetsPage.jsx,FinancialAssetsPage.css}
    credit/{FinancialCreditPage.jsx,FinancialCreditPage.css}
    vehicle/{FinancialVehiclePage.jsx,FinancialVehiclePage.css,
             VehiclePriorities.jsx,reorderPriorities.js}
    review/{FinancialReviewPage.jsx,FinancialReviewPage.css}
    result/{FinancialResultPage.jsx,FinancialResultPage.css}
  styles/FinancialPages.css
  calculateFinancialSummary.js
  calculateVehicleBudget.js
features/vehicle/
  pages/{search,results,detail,compare,simulation}/
  components/{VehicleCard,VehicleArtwork,VehicleCatalogGate}.jsx
  styles/VehiclePages.css
  VehicleContext.jsx
  useVehicle.js
  vehicleApi.js
  vehicleData.js
features/company/
  pages/{list,detail}/
  companyApi.js
pages/
  home/{HomePage.jsx,HomePage.css}
  about/{AboutPage.jsx,AboutPage.css}
  login/{LoginPage.jsx,LoginPage.css}
  not-found/NotFound.jsx
  predict/PredictPage.jsx
  search/SearchPage.jsx
```

- 특정 화면에서만 사용하는 JSX·CSS·로직은 해당 화면 폴더에 함께 둔다. 차량 우선순위 컴포넌트와 정렬 로직은 재무 차량 입력 화면이 소유한다.
- 기능 내 여러 화면에서 사용하는 컴포넌트는 해당 기능의 `components/`, 공통 스타일은 `styles/`에 둔다. 기존 공통 CSS를 화면마다 복제하지 않는다.
- 기능 공통 계산·API·상태 모듈은 기능 루트에 유지한다. 파일이 실제로 늘어날 때 역할별 하위 폴더를 추가한다.
- 서로 다른 기능이 함께 사용하는 동일한 계약의 요소만 `shared/`로 올린다.
- 라우트는 `App.jsx`에서 화면 모듈을 직접 import한다. 화면마다 별도 재노출용 `index` 파일을 만들지 않는다.
- 차량 검색과 결과는 별도 화면 파일로 관리한다. URL과 사용자 동작은 유지한다.

## 데이터 경로

기존 데이터 경로와 생성 규칙은 데이터 해시·출처 기록 및 ML CSV 연결을 보존하기 위해 유지한다. `sources`는 원본, `extracted`는 추출 중간 자료, `csv`는 변환 결과다. 가구 합성 데이터는 생성 묶음별 디렉터리에서 JSON·CSV·설정·검증 기록을 함께 관리한다. 소스 코드와 테스트는 `tools/data`로 분리했다.

`data/households/manual/profiles.csv`는 기존 루트 파일을 보존한 자료다. 검증된 ML 입력으로 자동 채택하지 않으며, 학습 데이터의 기준 경로는 `ml/config/datasets.json`이다.

원본 파일·합성 데이터의 일괄 이동이나 재생성은 구조 변경에 포함하지 않는다. 데이터 묶음을 추가할 때 소스 코드를 복제하지 않고 패키지의 생성 모듈과 별도 설정을 사용한다.

백엔드의 company·vehicle 코드는 각 기능 패키지 안에 배치한다. MyBatis XML은 클래스 전체 이름을 참조한다. 차량 조회는 영속성 모델 `Vehicle`을 반환하고 Controller에서 `VehicleResponse`로 변환해 HTTP 응답과 DB 매핑을 분리한다. 단순 조회를 감싸기 위한 Service는 추가하지 않는다.

## 실행과 저장

- 웹 개발 실행: 루트 `dev.sh`, 프런트 `front/package.json`, 백엔드 Gradle.
- 데이터 처리: [데이터 도구](../tools/data/README.md)의 모듈 실행 방법 사용.
- 모델·전처리·평가 결과: `ml/outputs/models`, `ml/outputs/reports`. 현재 ML은 미구현 상태다.
- 모델 의존성 버전 고정은 실제 설치·호환성 검증과 함께 진행한다. 현재 requirements는 설치 후보이며 실행 환경이 검증된 lock 파일은 아니다.
- 설치 의존성·Python 캐시·가상환경·임시 파일은 루트 `.gitignore`에서 제외한다. 원본·재현에 필요한 설정과 공유할 결과는 의도적으로 관리한다.
- `examples/legacy`는 웹 빌드 대상이 아니며 예전 IDE 프로젝트를 보존한다.
