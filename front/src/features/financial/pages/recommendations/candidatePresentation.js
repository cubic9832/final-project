import { recommendationImages } from './recommendationImages.js';

export const fuelLabels = { GASOLINE: '가솔린', HYBRID: '하이브리드', DIESEL: '디젤', LPG: 'LPG', ELECTRIC: '전기' };
export const candidateMoney = value => Number.isFinite(value) ? `${(value / 10000).toLocaleString('ko-KR', { maximumFractionDigits: 1 })}만 원` : '계산 불가';
const aliases = {
  K5: 'OWN001', K8: 'OWN002', 니로: 'OWN003', 레이: 'OWN004', 모닝: 'OWN005', 셀토스: 'OWN006', 스포티지: 'OWN007', 아르카나: 'OWN008',
  '더 뉴 그랜저': 'OWN009', '더 뉴 그랜저 Hybrid': 'OWN009', '더 뉴 스타리아 라운지': 'OWN010',
  '디 올 뉴 아반떼': 'OWN011', '디 올 뉴 아반떼 Hybrid': 'OWN011', '쏘나타 디 엣지': 'OWN012', '쏘나타 디 엣지 Hybrid': 'OWN012',
  코나: 'OWN013', '코나 Hybrid': 'OWN013', 팰리세이드: 'OWN014', '팰리세이드 Hybrid': 'OWN014',
};
export const candidateImage = vehicle => recommendationImages[aliases[vehicle.model]];
