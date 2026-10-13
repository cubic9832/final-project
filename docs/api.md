# REST API 기준

Spring 서버와 Python에서 HTTP API를 제공하는 경우에 적용한다. React의 API 호출도 동일한 계약을 따른다.

## 리소스 및 HTTP 메서드

- 리소스를 중심으로 설계하고 요청마다 처리에 필요한 인증·입력 정보를 전달한다. 이전 요청의 서버 세션 상태에 의존하는 API를 만들지 않는다.
- 프로젝트 경로 규칙으로 컬렉션은 복수 명사, 경로 단어는 소문자 kebab-case를 사용한다. 예: `/vehicles`, `/prediction-jobs/{id}`. 조회·생성·삭제 동사를 경로에 넣지 않는다.
- 단일 리소스 식별자는 경로에, 필터·정렬·페이지 조건은 쿼리에 둔다.
- GET은 조회하며 데이터를 변경하지 않는다. POST는 생성·처리 요청, PUT은 전체 교체, PATCH는 부분 변경, DELETE는 삭제에 사용한다.
- PUT·DELETE의 멱등성을 유지한다. POST·PATCH를 자동 재시도하려면 중복 실행을 방지하는 계약이 먼저 있어야 한다.

## 응답 및 오류

- 일반 데이터는 JSON으로 주고받고 올바른 `Content-Type`을 지정한다.
- 성공은 결과에 맞게 200, 생성은 201과 생성 리소스의 `Location`, 본문 없는 성공은 204를 사용한다. 204 응답에는 본문을 넣지 않는다.
- 잘못된 입력은 400, 인증이 없거나 유효하지 않으면 401, 권한 부족은 403, 리소스 없음은 404, 현재 상태와의 충돌은 409, 서버 오류는 5xx로 구분한다. 실패를 200 응답으로 감추지 않는다.
- 오류 응답은 RFC 9457의 Problem Details와 `application/problem+json`을 사용한다. `type`, `title`, `status`, `detail`, `instance`를 용도에 맞게 사용하고 실제 HTTP 상태와 일치시킨다. 필드 오류 확장은 API 계약에 문서화한다.
- 내부 스택 트레이스나 민감 정보를 오류 응답에 노출하지 않는다.
- 오래 걸리는 학습·추론을 비동기로 제공한다면 202로 접수를 알리고 작업 상태를 조회할 리소스를 제공한다. 202를 처리 완료로 해석하지 않는다.

## 공식 근거와 프로젝트 선택

HTTP 메서드·멱등성·상태 코드는 [RFC 9110](https://www.rfc-editor.org/rfc/rfc9110.html), PATCH는 [RFC 5789](https://www.rfc-editor.org/rfc/rfc5789.html), 오류 형식은 [RFC 9457](https://www.rfc-editor.org/rfc/rfc9457.html)을 기준으로 한다. 복수 명사·kebab-case 경로는 프로젝트의 명명 선택이다.

Spring에서는 [HTTP 메서드별 요청 매핑](https://docs.spring.io/spring-framework/reference/web/webmvc/mvc-controller/ann-requestmapping.html)을 사용해 각 엔드포인트의 메서드를 명시한다.
