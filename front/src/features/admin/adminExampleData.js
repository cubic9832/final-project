// 관리자 대시보드 예시 데이터 (Figma: ADMIN 01 · 관리자 대시보드)
// 백엔드·모델 서버 연결 전이라 화면 확인용 값만 둔다. 실제 운영 수치가 아니다.
// 모델 지표·파이프라인 수치는 담당자가 실제 값을 정하면 API 응답으로 바꾼다.

export const summaryCards = [
  { label: '수집 작업', value: '정상', note: '마지막 완료 00:38', tone: 'good' },
  { label: '차량 데이터', value: '1,284건', note: '오늘 변경 18건' },
  { label: '모델 버전', value: 'v1.4.2', note: 'ROC-AUC 0.88', tone: 'good' },
  { label: '오늘 예측', value: '3,842건', note: '오류율 0.17%' },
];

// 데이터 수집 → 정제 → DB 적재 → 검색 인덱싱 단계별 처리 건수
export const pipelineSteps = [
  { label: '제조사 차량 데이터 수집', done: 1284, total: 1284, tone: 'good' },
  { label: '정제·중복 제거', done: 1276, total: 1284, tone: 'info' },
  { label: 'MySQL 적재', done: 1276, total: 1276, tone: 'good' },
  { label: 'Elasticsearch 인덱싱', done: 1269, total: 1276, tone: 'warning' },
];

export const pipelineWarning = {
  title: '7건 재시도 대기',
  message: '옵션명 형식 오류로 검색 인덱스에서 제외되었습니다. 원본 데이터는 보존됩니다.',
};

// 모델 버전 비교 (이전 → 현재). 값은 예시값
export const modelInfo = {
  production: 'v1.4.2',
  deployedAt: '2026.09.28',
  previous: 'v1.4.1',
};

export const modelMetrics = [
  { name: 'F1', previous: 0.78, current: 0.8 },
  { name: 'ROC-AUC', previous: 0.86, current: 0.88 },
  { name: '재현율', previous: 0.74, current: 0.77 },
];

export const modelScoreCards = [
  { label: 'F1', value: '0.80', highlight: true },
  { label: 'ROC-AUC', value: '0.88', highlight: true },
  { label: 'MAE', value: '96만' },
];

// 요청 경로별 서비스 상태. status: 'ok'(정상) | 'check'(점검)
export const services = [
  { id: 'model', name: 'FastAPI 모델 서버', detail: 'p95 182ms · 3 pods · v1.4.2 loaded', status: 'ok' },
  { id: 'api', name: 'Spring Boot 서비스 API', detail: 'p95 240ms · 오류율 0.12% · 4 pods', status: 'ok' },
  { id: 'web', name: 'React 연동', detail: 'v2.8.0 · API schema 일치 · CDN hit 96%', status: 'ok' },
  { id: 'search', name: 'Elasticsearch', detail: '인덱스 지연 7건 · cluster green', status: 'check' },
];

// 재학습·배포 이력. status: 'success'(성공) | 'rollback'(롤백)
export const deployments = [
  { id: 1, time: '2026.10.02 00:30', version: 'vehicle-etl-20261002', task: '데이터 수집·정제', status: 'success', actor: 'system' },
  { id: 2, time: '2026.09.28 14:20', version: 'model-v1.4.2', task: '재학습·검증·배포', status: 'success', actor: 'admin.kim' },
  { id: 3, time: '2026.09.21 10:05', version: 'search-index-v37', task: '차량 인덱스 교체', status: 'success', actor: 'admin.lee' },
  { id: 4, time: '2026.09.14 09:42', version: 'model-v1.4.1', task: '성능 저하로 롤백', status: 'rollback', actor: 'admin.kim' },
];

export const managementCards = [
  { id: 'vehicle', title: '차량 데이터 관리', count: '1,284건', note: '가격·트림·연비 검수 대기 18건', action: '차량 데이터 열기' },
  { id: 'user', title: '사용자 관리', count: '8,421명', note: '관리자 승인 대기 2건 · 잠금 계정 4건', action: '사용자 관리 열기' },
];

// 감사 로그 (오늘)
export const auditLogs = [
  { id: 1, time: '10:42:18', actor: 'admin.kim', action: '차량 트림 수정', target: '현대 아반떼 HEV 가격' },
  { id: 2, time: '10:05:33', actor: 'admin.lee', action: '사용자 잠금 해제', target: 'user_2048' },
  { id: 3, time: '09:48:07', actor: 'system', action: '모델 상태 확인', target: 'FastAPI /health' },
  { id: 4, time: '09:15:49', actor: 'admin.kim', action: '감사 로그 내보내기', target: '2026-09-01~10-02' },
];
