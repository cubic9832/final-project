import displacements from './vehicleDisplacements.json' with { type: 'json' };
import { resolvePlanningEfficiency } from '../vehicle/resolvePlanningEfficiency.js';

export const taxSource = 'https://www.law.go.kr/LSW/lsSideInfoP.do?docCls=jo&joBrNo=00&joNo=0127&lsiSeq=282559&urlMode=lsScJoRltInfoR';

// 비영업용 신차 기준, 연납 공제·차령 경감 제외. 금액 단위는 만 원.
export function annualVehicleTax(cc, electric = false, seats = 5) {
  if (seats >= 11) return null; // 승합 등록 여부는 현재 카탈로그로 확정할 수 없다.
  if (electric) return 13;
  if (!Number.isFinite(cc) || cc <= 0) return null;
  return cc * (cc <= 1000 ? 80 : cc <= 1600 ? 140 : 200) * 1.3 / 10000;
}

export function getVehicleCostDefaults(vehicle, annualDistance = 12000) {
  const cc = displacements[vehicle.id]?.cc;
  const tax = annualVehicleTax(cc, vehicle.fuel === 'ELECTRIC', vehicle.seats);
  const energyPrice = { GASOLINE: 1700, HYBRID: 1700, DIESEL: 1550, LPG: 1000, ELECTRIC: 350 }[vehicle.fuel] ?? '';
  // 보험사 견적 모델이 아닌 예산 수립용 가정: 연 60만 원 + 차량가의 1%.
  const insurance = Math.round(60 + vehicle.price / 10000 * 0.01);
  // 실제 부과세액·정비 견적이 아닌 자금 계획용 가정.
  const estimatedTax = Math.max(20, Math.round(vehicle.price / 10000 * 0.01));
  const distance = Number.isFinite(annualDistance) && annualDistance >= 0 ? annualDistance : 12000;
  const baseMaintenance = Math.max(30, vehicle.price / 10000 * 0.015);
  // 연간 비용의 40%는 고정 적립, 60%는 주행에 따른 소모로 가정한다.
  const maintenance = Math.round(baseMaintenance * (0.4 + 0.6 * distance / 12000));
  const efficiencyInfo = resolvePlanningEfficiency(vehicle);
  const efficiency = efficiencyInfo.value;
  return {
    efficiencyEstimated: efficiencyInfo.estimated,
    efficiencySource: efficiencyInfo.sourceUrl,
    inputs: { efficiency, energyPrice, insurance, annualTax: tax ?? estimatedTax, maintenance },
    notes: {
      efficiency: efficiencyInfo.basis,
      energyPrice: '연료별 기본 가정 · 실시간 시세 아님',
      insurance: '계획용 추정 · 연 60만 원 + 차량가의 1% · 실제 견적 아님',
      annualTax: tax === null ? '예산용 추정 · 차량가의 연 1% (최소 20만 원) · 실제 세액 아님' : vehicle.fuel === 'ELECTRIC' ? '비영업용 승용 전기차 · 지방교육세 포함' : `${cc.toLocaleString('ko-KR')}cc · 비영업용 신차 · 지방교육세 30% 포함`,
      maintenance: `예산용 추정 · 기준비 max(차량가 × 1.5%, 30만 원) × (40% + 60% × 연 주행거리 / 12,000km) · 현재 ${distance.toLocaleString('ko-KR')}km`,
    },
    displacementSource: displacements[vehicle.id]?.source,
  };
}

export function updatePlanInput(vehicle, inputs, name, value) {
  const next = { ...inputs, [name]: value };
  if (name === 'annualDistance' && Number.isFinite(value) && value >= 0 && inputs.maintenance === getVehicleCostDefaults(vehicle, inputs.annualDistance).inputs.maintenance) {
    next.maintenance = getVehicleCostDefaults(vehicle, value).inputs.maintenance;
  }
  return next;
}
