import { resolveVehicleImage } from '../../../vehicle/resolveVehicleImage.js';
import { formatFinancialMoney } from '../../formatFinancialMoney.js';

export const fuelLabels = { GASOLINE: '가솔린', HYBRID: '하이브리드', DIESEL: '디젤', LPG: 'LPG', ELECTRIC: '전기' };
export const candidateMoney = value => formatFinancialMoney(value, 1);
export const candidateImage = resolveVehicleImage;
