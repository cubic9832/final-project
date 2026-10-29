# 콤파 챗봇 실행·운영

## 기능과 구조

로그인한 회원만 이용한다. 서비스 이용 / 차종 도감 / 자동차 용어 카테고리, 추천 질문, 취향 결과·차량 상세·재무 추천의 용어 설명 연결을 유지한다. 비회원에게는 챗봇과 설명 버튼을 표시하지 않는다.

추천 질문 9개와 사이트의 용어 설명 20개는 Spring에 등록한 고정 답변을 보여준다. 추천 질문과 용어가 같은 항목을 가리키면 같은 답변을 사용한다. 외부 AI를 호출하지 않아 토큰과 일일 AI 질문 횟수를 사용하지 않으며, API 키가 없거나 AI 질문 횟수를 모두 사용해도 이용할 수 있다. 답변은 `back/src/main/java/com/kh/back/chatbot/service/ChatGuideAnswers.java`에서 관리한다.

직접 입력한 질문은 React → Spring → 로컬 문서 검색 → 선택한 AI → 답변 순서다. 한국어 2글자 단위·단어로 상위 4개 문서 조각을 검색하며 벡터 DB나 ML 서버는 필요하지 않다. 고정 답변도 최근 대화에 저장하므로 이후 직접 입력하는 후속 질문에 맥락을 전달한다. 후속 AI 질문에서는 이전 고정 답변도 입력 토큰에 포함될 수 있다. 직접 입력한 문장이 추천 질문과 같더라도 AI로 처리한다.

## 모델 선택과 키

기본값은 기존 Gemini 연결이다. OpenAI를 사용하려면 실행할 PowerShell에서 설정하고 기존 Spring 서버를 종료한 뒤 다시 실행한다. 실제 키는 소스·React VITE 변수·Git에 넣지 않는다.

```powershell
cd C:\workspace\Spring
$env:CHATBOT_PROVIDER = 'openai'
$env:OPENAI_MODEL = 'gpt-5.6-luna'
$chatbotSecret = Read-Host 'OpenAI API 키' -AsSecureString
$env:OPENAI_API_KEY = [System.Net.NetworkCredential]::new('', $chatbotSecret).Password
.\dev.ps1
```

Windows 사용자 환경변수로 설정했다면 IDE·터미널을 완전히 닫았다가 다시 연다. dev.ps1은 켜진 서버를 재사용하므로 기존 서버를 종료한 후 실행해야 새 의존성과 키가 적용된다.

Gemini: CHATBOT_PROVIDER=gemini, GEMINI_API_KEY, GEMINI_MODEL(기본 gemini-3.5-flash-lite).
OpenAI: CHATBOT_PROVIDER=openai, OPENAI_API_KEY, OPENAI_MODEL. 모델은 해당 키에 허용된 이름을 지정한다. 자동 제공자 전환은 아직 하지 않는다.

OpenAI는 Spring AI 2.0.2 ChatClient를 사용한다. ChatMemory는 두 제공자에서 사용하는 서버 측 최근 10개 메시지 창이다. 실패한 요청이 반쪽 대화로 저장되지 않도록 서비스에서 성공한 질문·답변 쌍만 추가하며, 이중 저장을 피하기 위해 자동 메모리 Advisor는 붙이지 않는다. 외부 요청은 30초 제한, SDK 자동 재시도 0회·Spring AI 최대 시도 1회다. 키가 없어도 서버·이력 조회는 작동하고 질문 전송만 503으로 안내한다.

## 기록·사용량·개인정보

- 회원 번호는 JWT 인증 주체에서만 가져온다. 클라이언트가 보낸 회원 번호·대화 이력은 사용하지 않는다.
- 질문 1~500자, 회원별 한국 시간 자정 기준 하루 30회, 서버 동시 외부 호출 4개까지다. 외부 호출 단계에 진입한 실패도 차감한다. 입력 오류·키 없음·동시 요청 거절은 차감하지 않는다.
- 최근 10개 메시지를 서버 메모리에 보관해 새로고침 뒤 복원한다. 대화 삭제는 사용량을 초기화하지 않는다. 서버 재시작 시 대화·사용량은 사라진다. 다중 서버 배포 시 공유 저장소가 필요하다.
- 주민번호·카드번호·전화번호·계좌번호·이메일은 검색·전송·기록 전에 가리고 답변도 가린다. 원문 질문을 대화 기록에 넣지 않는다. 이름·주소·변형 입력을 정규식으로 모두 검출할 수 없어 화면에도 입력 금지를 안내한다.
- 시스템 지침은 back/src/main/resources/prompts/chatbot-system.st를 UTF-8로 읽는다. 답변 범위·거절·3~5문장·일반 텍스트를 지시하지만 모델 준수를 보장하는 필터는 아니다.
- OpenAI에는 현재 회원의 최근 진단 중 월 여유금·구매 가격 상한과 저장된 취향 이름만 요약한다. 이름·연락처·계좌·원본 응답은 포함하지 않는다. 무료 Gemini에는 이 개인 요약을 자동 첨부하지 않는다.

## API

모든 요청은 로그인 필요. 기존 /api/v1/chat-messages와 ApiResponse 봉투를 유지한다.

- POST: { "message": "MPV란?" } → data: { answer, question, remaining, sources }. question은 가린 질문이며 화면은 이것을 표시한다.
- POST /api/v1/chat-messages/guides: { "guideId": "MPV" } → 같은 응답 구조로 등록된 고정 질문·답변을 반환하고 회원별 대화에 추가한다. 등록되지 않은 ID는 400이며 외부 AI 호출로 대체하지 않는다. remaining은 차감하지 않는다.
- GET: data: { messages: [{ role: "user" 또는 "model", text }], remaining }.
- DELETE: 본인 대화만 삭제하며 사용량은 유지한다.

400 입력 오류, 401 로그인 필요, 429 동시 요청 또는 일일/제공자 한도, 503 키 없음 또는 OpenAI 연결 실패. Gemini 키·모델·응답 오류는 502, 전송 지연은 504. 내부 예외 내용·질문 원문·키를 오류 응답이나 챗봇 로그에 기록하지 않는다.

## 자료와 검증

안내 문서: back/src/main/resources/chatbot/knowledge/*.md. 제목 단위와 최대 1,200자 조각으로 나눠 검색한다. 수정 뒤 서버를 재시작한다. 검색 자료 목록은 모델에게 전달한 자료이며 실제 인용 여부를 검증한 출처는 아니다. UI에는 노출하지 않는다.

실제 답변은 [검증표](chatbot-evaluation.md)의 20개 질문을 모델별로 실행해 기록한다. 자동화 테스트의 가짜 응답 성공과 실제 모델의 사실 정확성을 구분한다.
