// 관리자 UI 검토용 예시. 운영 통계·실제 회원·모델 평가 결과가 아니다.
export const summaryCards = [
  { label: '차량 데이터', value: '258건', note: '차량·트림 정보 관리', destination: 'vehicles' },
  { label: '추천 라벨', value: '20종', note: '이미지·주요 정보·추천 사유', destination: 'recommendations' },
  { label: '회원 현황', value: '128명', note: '가입·상태·권한 확인', destination: 'members' },
  { label: '적용 모델', value: 'v1.0.0', note: '전체 차량 추천 모델', destination: 'models' },
];
export const services = [
  { id: 'api', name: 'Spring API', detail: '회원·차량 서비스', status: '정상' },
  { id: 'database', name: 'MySQL', detail: '회원·차량 데이터', status: '정상' },
  { id: 'model', name: '추천 서버', detail: '차량 추천 추론', status: '확인 필요' },
];
export const vehicleExamples = [
  { id: 'vehicle-k5', labelCode: 'OWN001', model: 'K5', brand: '기아', body: '세단', grade: '중형', trim: '2.0 가솔린 프레스티지', price: '2,900만 원', efficiency: '12.6km/L', fuel: '가솔린', status: '검수 대기', updatedAt: '2026.10.20', image: '/images/recommendations/cutouts/k5.webp' },
  { id: 'vehicle-ray', labelCode: 'OWN004', model: '레이', brand: '기아', body: '경차', grade: '경형', trim: '1.0 가솔린 시그니처', price: '1,800만 원', efficiency: '12.7km/L', fuel: '가솔린', status: '공개', updatedAt: '2026.10.20', image: '/images/recommendations/cutouts/ray.webp' },
  { id: 'vehicle-niro', labelCode: 'OWN003', model: '니로', brand: '기아', body: 'SUV', grade: '소형', trim: '하이브리드 프레스티지', price: '3,100만 원', efficiency: '20.8km/L', fuel: '하이브리드', status: '공개', updatedAt: '2026.10.19', image: '/images/recommendations/cutouts/niro.webp' },
  { id: 'vehicle-palisade', labelCode: 'OWN014', model: '팰리세이드', brand: '현대', body: 'SUV', grade: '대형', trim: '가솔린 익스클루시브', price: '4,500만 원', efficiency: '9.7km/L', fuel: '가솔린', status: '비공개', updatedAt: '2026.10.18', image: '/images/recommendations/cutouts/palisade.webp' },
];
export const recommendationExamples = [
  { ...vehicleExamples[0], purpose: '출퇴근', reason: '매일 주행할 경로에서 승차감과 운전 편의성을 비교해 볼 수 있는 세단 후보입니다.' },
  { ...vehicleExamples[1], purpose: '출퇴근', reason: '작은 차체를 활용한 주차와 좁은 도로에서의 이동을 고려해 볼 수 있습니다.' },
  { ...vehicleExamples[2], purpose: '주말 여가', reason: '여행 짐과 야외 활동 장비를 고려해 실내·적재 공간을 비교해 볼 수 있는 후보입니다.' },
  { ...vehicleExamples[3], purpose: '가족 이동', reason: '동승 인원과 짐을 고려해 좌석 구성과 공간 활용을 비교해 볼 수 있는 후보입니다.' },
];
export const memberExamples = [
  { id: 'demo-member-1', nickname: '첫차준비생', email: 'f***@example.com', joinedAt: '2026.10.20', role: 'USER', status: '정상', lock: '잠금 없음' },
  { id: 'demo-member-2', nickname: '주말드라이버', email: 'w***@example.com', joinedAt: '2026.10.19', role: 'USER', status: '정상', lock: '로그인 잠금' },
  { id: 'demo-member-3', nickname: '운영담당자', email: 'a***@example.com', joinedAt: '2026.10.15', role: 'ADMIN', status: '정상', lock: '잠금 없음' },
  { id: 'demo-member-4', nickname: '도심운전자', email: 'c***@example.com', joinedAt: '2026.10.12', role: 'USER', status: '탈퇴', lock: '해당 없음' },
];
export const modelInfo = { production: 'v1.0.0', previous: 'v0.9.0', deployedAt: '2026.10.20', schema: 'financial-ui-v1' };
export const modelMetrics = [{ name: 'Top-1', previous: 0.65, current: 0.7 }, { name: 'Top-3', previous: 0.82, current: 0.88 }, { name: 'Macro F1', previous: 0.62, current: 0.68 }];
export const deployments = [
  { id: 'model-run-1', time: '2026.10.20 10:30', version: 'v1.0.0', task: '모델 적용', status: '적용 중', actor: 'admin.demo' },
  { id: 'model-run-2', time: '2026.10.19 16:00', version: 'v0.9.0', task: '모델 평가', status: '검증 완료', actor: 'admin.demo' },
];
export const auditLogs = [
  { id: 'log-1', time: '2026.10.20 10:42', actor: 'admin.demo', type: '관리자 변경', action: '추천 사유 수정', target: 'K5 · 출퇴근', result: '완료' },
  { id: 'log-2', time: '2026.10.20 10:30', actor: 'admin.demo', type: '관리자 변경', action: '모델 적용', target: 'v1.0.0', result: '완료' },
  { id: 'log-3', time: '2026.10.19 09:48', actor: 'system', type: '서비스 오류', action: '추천 요청 실패', target: 'REQ-DEMO-003', result: '확인 필요' },
  { id: 'log-4', time: '2026.10.19 09:15', actor: 'admin.demo', type: '관리자 변경', action: '차량 정보 검수', target: '레이 · 트림 정보', result: '완료' },
];
