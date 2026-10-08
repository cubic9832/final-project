# 기능별 파일 및 이름 기준

공식 문서의 언어·프레임워크 규칙을 우선한다. 공식 문서가 강제하지 않는 파일명과 기능별 배치는 아래 프로젝트 규칙을 적용한다. 프레임워크·빌드 도구가 정한 설정 파일명과 진입점은 그대로 유지한다.

## React 프론트엔드

공식 규칙: [컴포넌트 이름](https://react.dev/learn/your-first-component)은 대문자로 시작하고, [Hook 이름](https://react.dev/learn/reusing-logic-with-custom-hooks)은 `use` 뒤에 대문자로 시작하는 이름을 붙인다. React가 모든 파일명이나 폴더 구조를 강제하는 것은 아니다.

| 기능 | 프로젝트 파일 규칙 | 예시 |
| --- | --- | --- |
| 화면·컴포넌트 | 컴포넌트 이름과 같은 PascalCase | `VehicleList.jsx`, `VehicleCard.tsx` |
| Hook | `use` + PascalCase | `useVehicles.js`, `useVehicles.ts` |
| API 호출 | camelCase + `Api` | `vehicleApi.js`, `vehicleApi.ts` |
| 유틸리티 | 역할이 드러나는 camelCase | `formatCurrency.js`, `formatCurrency.ts` |
| 컴포넌트 스타일 | 컴포넌트 이름과 일치 | `VehicleCard.css`; CSS Modules 사용 시 `VehicleCard.module.css` |

- JSX를 포함하면 `.jsx` 또는 `.tsx`, 일반 로직은 `.js` 또는 `.ts`를 사용한다. JavaScript·TypeScript 선택은 프론트엔드 구성 시 정하며 혼용을 위해 중복 파일을 만들지 않는다.
- 도메인별 파일은 `features/vehicle/`처럼 기능 단위로 모으고, 여러 기능에서 실제로 재사용하는 요소만 `shared/`에 둔다. 기능 폴더는 소문자 kebab-case를 사용한다.

## Spring 서버 — Java 기준

공식 근거: [Spring Boot 코드 구조](https://docs.spring.io/spring-boot/reference/using/structuring-your-code.html)는 특정 배치를 강제하지 않으며 역도메인 패키지와 최상위 패키지의 애플리케이션 클래스를 권장한다. [Java 패키지 및 파일 규칙](https://docs.oracle.com/javase/specs/jls/se25/html/jls-7.html)을 따른다.

- 패키지는 소문자로 작성하고 실제 프로젝트의 역도메인 루트 아래에 기능별 패키지를 둔다. 예: `<root>.vehicle`. 기본 패키지는 사용하지 않는다.
- public 최상위 타입의 이름과 `.java` 파일명을 일치시키고 타입 이름은 PascalCase를 사용한다.
- 기능 패키지 안에서 역할을 구분한다. 아래 접미사는 Spring의 강제 사항이 아닌 프로젝트 규칙이다.

| 기능 | 프로젝트 파일 규칙 | 예시 |
| --- | --- | --- |
| HTTP 요청 처리 | `도메인Controller.java` | `VehicleController.java` |
| 비즈니스 로직 | `도메인Service.java` | `VehicleService.java` |
| 영속성 접근 | `도메인Repository.java` | `VehicleRepository.java` |
| 도메인 모델 | 도메인 이름 | `Vehicle.java` |
| 요청·응답 DTO | 동작·대상 + `Request` / `Response` | `CreateVehicleRequest.java`, `VehicleResponse.java` |
| 설정 | 목적 + `Config` | `WebConfig.java` |

## Python 딥러닝

공식 근거: [PEP 8](https://peps.python.org/pep-0008/#naming-conventions)에 따라 모듈은 짧은 소문자 이름을 사용하고 필요하면 underscore를 넣는다. 패키지는 짧은 소문자로 작성하며 underscore는 피한다. 함수·변수는 snake_case, 클래스는 CapWords를 사용한다.

아래 기능 배치와 예시는 프로젝트 규칙이며 딥러닝 프레임워크를 특정하지 않는다.

| 기능 | 파일명 예시 | 책임 |
| --- | --- | --- |
| 데이터 로딩 | `dataset.py` | 데이터 읽기와 샘플 제공 |
| 전처리 | `preprocessing.py` | 학습·추론에 필요한 공통 변환 |
| 모델 정의 | `vehicle_model.py` | 모델 구조 정의 |
| 학습 | `train.py` | 학습 실행 |
| 평가 | `evaluate.py` | 모델 성능 평가 |
| 추론 | `predict.py` | 입력에 대한 예측 |

- `vehicle/`처럼 기능별 패키지 안에서 필요한 역할만 분리한다. 예시 파일을 빈 틀로 미리 생성하지 않는다.
- 재사용 로직은 `.py`에 두고 탐색용 노트북은 `notebooks/`에 둔다. 데이터셋·체크포인트는 소스 파일과 구분하며 사용하는 라이브러리의 저장 형식에 맞는 확장자를 사용한다.
- 학습·평가·추론 코드는 import만으로 실행되지 않도록 실행 진입점을 분리한다.
