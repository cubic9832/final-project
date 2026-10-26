# 프로젝트 구조와 관리 경계

```text
front/src/
  features/{vehicle,financial,company,preset,auth}/  기능별 코드
  shared/api/                                공통 HTTP 클라이언트·토큰 재발급
  pages/{home,about,login,signup,mypage,admin,...}/  독립 화면별 JSX·CSS
  components/                                공통 레이아웃·헤더·로그인 필요 화면 보호
  stores/                                    전역 상태 (로그인 정보, 공용 알림)
  styles/                                    전역 스타일과 테마
back/src/main/java/com/kh/back/
  {vehicle,company,auth,member,taste}/        기능별 Java 코드
    controller/                              HTTP API Controller
    dto/                                     DB 매핑 객체와 요청·응답 DTO
    mapper/                                  MyBatis Mapper 인터페이스
    service/                                 Service 인터페이스·Impl 및 기능 정책
    repository/                              기존 JdbcTemplate 기반 DB 접근 (taste)
  common/                                    공통 응답과 오류 처리, JWT·Spring Security
tools/data/                                  데이터 수집·생성·정제·CSV 코드
data/                                        데이터·생성 규칙·출처·검증 기록
ml/                                          기존 진단 입력에 맞춘 모델·추론 API
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
features/auth/
  components/{AuthModal,AuthToast,PasswordInput,LogoutConfirmModal}  여러 화면·헤더가 함께 쓰는 팝업·입력칸
  authApi.js
  passwordPolicy.js   회원가입 · 비밀번호 찾기가 함께 쓰는 비밀번호 규칙
  memberApi.js
pages/
  home/{HomePage.jsx,HomePage.css}
  about/{AboutPage.jsx,AboutPage.css}
  login/{LoginPage.jsx,LoginPage.css,PasswordResetModal,RecaptchaBox,GoogleLoginButton}
  signup/{SignupPage.jsx,SignupPage.css,TermsModal,SignupCompleteModal,
          emailTypo.js,profileRules.js,GoogleSignupPage}
  mypage/{MyPage.jsx,MyPage.css,ProfileEditModal,EmailNotificationModal,PasswordChangeModal,
          AccountManageModal,notificationOptions.js}
  admin/{AdminPage.jsx,AdminPage.css,ModelMetricChart,adminExampleData.js}
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

백엔드는 [참고 저장소의 Spring 구조](https://github.com/wonguwon/final_project_sample/tree/step1--login/back/src/main/java/com/kh/back/member)를 따른다. API Controller는 Service 인터페이스를 호출하고, ServiceImpl이 Mapper·Repository와 업무 규칙을 조합한다. MyBatis XML은 이동한 Mapper와 DTO의 전체 클래스명을 참조한다. 차량 DB 매핑은 `vehicle/dto/VehicleDto`, SQL 접근은 `vehicle/mapper/VehicleMapper`, 응답 변환은 `vehicle/service/VehicleServiceImpl`이 담당한다. 인증 정책·검증 도우미는 `auth/service/`, 공통 응답·예외·Security는 `common/`에서 관리한다.

성공·실패 응답은 `ApiResponse.ok`·`ApiResponse.fail`로 통일하며, MVC 예외는 `common/exception/GlobalExceptionHandler`에서 처리한다. 인증·권한 오류는 Security의 진입점·거부 핸들러가 같은 실패 봉투로 반환한다. 기존 API 경로·요청 필드·DB 마이그레이션은 유지한다.

## 실행과 저장

- 웹 개발 실행: 루트 `dev.sh`, 프런트 `front/package.json`, 백엔드 Gradle.
- 데이터 처리: [데이터 도구](../tools/data/README.md)의 모듈 실행 방법 사용.
- ML 코드: `ml/recommender`. 모델·전처리·평가 결과: `ml/outputs/models/financial-ui-v1/all-cars/{시각}`. 입력 UI를 변경하지 않고 기존 진단값으로 재학습한다.
- 모델 실행 의존성은 `ml/pyproject.toml`에서 관리하고 API는 serve extra로 설치한다. 검증한 Windows CPU 직접 의존성 버전은 `ml/requirements-cpu-windows.txt`에 기록한다.
- 설치 의존성·Python 캐시·가상환경·임시 파일은 루트 `.gitignore`에서 제외한다. 원본·재현에 필요한 설정과 공유할 결과는 의도적으로 관리한다.
- `examples/legacy`는 웹 빌드 대상이 아니며 예전 IDE 프로젝트를 보존한다.

추천 요청 변환과 API 호출은 features/financial의 일반 모듈로, 추천 화면·차량 카드·스타일·이미지 매핑은 pages/recommendations/에 함께 둔다. 종합 결과 페이지의 기존 추천 버튼 이벤트에서만 API를 요청하고 성공하면 /financial/recommendations로 이동한다. 기존 진단 입력 화면과 헤더는 유지한다. [실행 및 API 계약](recommendation.md)을 참고한다.
