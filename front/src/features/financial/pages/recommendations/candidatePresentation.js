import { candidateModelImages } from './candidateModelImages.js';

export const fuelLabels = { GASOLINE: '가솔린', HYBRID: '하이브리드', DIESEL: '디젤', LPG: 'LPG', ELECTRIC: '전기' };
export const candidateMoney = value => Number.isFinite(value) ? `${(value / 10000).toLocaleString('ko-KR', { maximumFractionDigits: 1 })}만 원` : '계산 불가';
export const candidateImage = vehicle => candidateModelImages[`${vehicle.brand}::${vehicle.model}`];
