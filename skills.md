# 프로젝트 폴더 구조 규칙

이번 `test` 브랜치의 구조 정리에 적용한 기준이다. 새 기능 추가와 폴더 이동에도 동일하게 적용한다. 세부 설계와 이름은 [설계 기준](.agents/skills/design-standards/SKILL.md), [명명 기준](.agents/skills/naming-standards/SKILL.md)을 함께 따른다.

## React: 기능 → 화면 → 화면 전용 파일

- 먼저 `features/financial/`, `features/vehicle/`처럼 업무 기능별로 묶는다.
- 기능 안에서 `pages/result/`, `pages/recommendations/`처럼 화면 단위로 한 번 더 묶는다. 폴더명은 소문자 kebab-case를 사용한다.
- 한 화면에서만 사용하는 JSX·CSS·컴포넌트·로직은 그 화면 폴더에 함께 둔다. 확장자가 같다는 이유로 모든 JSX와 CSS를 각각 별도 폴더에 모으지 않는다.
- 화면·컴포넌트 파일은 PascalCase로 쓰고, 전용 CSS는 해당 컴포넌트 이름과 맞춘다. 일반 계산·변환 모듈은 camelCase로 쓴다.
- 독립된 책임이 있는 컴포넌트는 한 화면에서만 사용해도 분리할 수 있다. 단순 마크업을 감싸기 위한 파일은 만들지 않는다.
- 기능 내 여러 화면이 함께 쓰는 컴포넌트는 해당 기능의 `components/`, 스타일은 `styles/`에 둔다. 기능 공통 계산·API 모듈은 기능 루트에서 시작하고 실제 파일이 늘어나면 역할별 폴더를 추가한다.
- 서로 다른 기능에서 실제로 재사용하는 동일한 의미·계약의 요소만 `shared/`로 옮긴다. 공통 요소가 특정 기능 내부 구현에 의존하지 않도록 한다.
- 라우트는 `App.jsx`에서 화면을 직접 import한다. 단순 재노출만 하는 화면별 `index` 파일이나 미래 사용을 예상한 빈 폴더는 만들지 않는다.

```text
front/src/
  features/
    financial/
      pages/
        result/
          FinancialResultPage.jsx
          FinancialResultPage.css
        recommendations/
          FinancialRecommendationsPage.jsx
          FinancialRecommendationsPage.css
          RecommendationCard.jsx
          recommendationImages.js
      components/
      styles/
      calculateVehicleBudget.js
    vehicle/
  shared/
```

위 트리는 배치 예시다. 실제로 필요한 파일과 폴더만 만든다. 별도 URL과 이동 흐름을 가진 추천 결과는 독립 화면으로 두며, 카드 내부 이미지·로딩 실패 처리는 해당 화면이 소유한다.

## Spring: 기능별 패키지와 책임 분리

- 프로젝트의 역도메인 루트 아래 `company`, `vehicle`처럼 기능별 패키지를 둔다. 패키지명은 소문자로 쓴다.
- 기능 안에서 HTTP 입출력, 비즈니스 규칙, 영속성 접근의 책임을 구분한다. 단순 조회를 전달하기만 하는 불필요한 Service는 추가하지 않는다.
- DB 매핑 모델과 HTTP 요청·응답 DTO를 구분한다. 예를 들어 `Vehicle`과 `VehicleResponse`를 분리한다.
- 패키지를 이동할 때 Java import와 MyBatis XML의 클래스 전체 이름 참조도 함께 수정한다.

## Python·데이터: 실행 코드와 산출물 분리

- 재사용 가능한 데이터 수집·변환 코드는 `tools/data/` 패키지에, ML 코드는 `ml/`에 둔다. 데이터 자체와 실행 코드를 섞지 않는다.
- 데이터 읽기·전처리·모델 정의·학습·평가·추론은 변경 이유에 따라 분리한다. 학습과 추론은 같은 전처리 구현을 사용한다.
- 모듈은 짧은 소문자와 필요한 underscore로 이름을 짓고, import만으로 학습이나 추론이 실행되지 않도록 진입점을 분리한다.
- 원본·추출 중간 자료·CSV는 `data/` 아래 역할별로 구분한다. 합성 데이터는 생성 묶음별로 데이터·설정·검증 기록을 함께 관리한다.
- 기존 데이터 경로는 출처·해시·학습 설정의 연결을 확인한 뒤 변경한다. 폴더 정리만을 위해 데이터를 재생성하거나 일괄 이동하지 않는다.
- 모델·전처리·평가 보고서는 `ml/outputs/models/` 아래 실행 묶음별로 관리한다. 가상환경·캐시·임시 파일·학습 산출물의 Git 추적 여부는 `.gitignore`로 명시한다.

## 구조 변경 시 확인

- 폴더 이동 자체가 기존 URL·화면 동작·계산 결과·API 계약을 바꾸지 않도록 한다.
- import, 라우트, 빌드 설정, 데이터·모델 경로와 실행 문서를 함께 확인한다.
- 변경 범위에 맞춰 빌드·린트·기존 테스트와 주요 사용자 흐름을 검증한다. 파일 이동 자체만 검사하는 형식적인 테스트는 추가하지 않는다.
