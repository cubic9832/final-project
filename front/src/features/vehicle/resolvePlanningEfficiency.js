import { resolveVehicleDetails } from './resolveVehicleDetails.js';

// 공식 효율이 없을 때만 쓰는 계획용 가정. 학습 당시 카탈로그는 변경하지 않는다.
const estimates = {
  GASOLINE: { default: 12, SUV: 10, MPV: 9, COUPE: 10, CONVERTIBLE: 9, ROADSTER: 10 },
  HYBRID: { default: 18, SUV: 16, MPV: 14 },
  DIESEL: { default: 14, SUV: 12, MPV: 11 },
  LPG: { default: 9, SUV: 8, MPV: 7 },
  ELECTRIC: { default: 5, SUV: 4.5, MPV: 3.5 },
};
export function resolvePlanningEfficiency(vehicle) {
  const unit = vehicle.fuel === 'ELECTRIC' ? 'km/kWh' : 'km/L';
  if (Number.isFinite(vehicle.efficiency) && vehicle.efficiency > 0) return { value: vehicle.efficiency, unit, estimated: false, basis: `등록 사양${vehicle.efficiency_reference_only ? ' (참고값)' : ''} · ${vehicle.checked_on || '확인일 미등록'}`, sourceUrl: vehicle.source_url };
  const details = resolveVehicleDetails(vehicle);
  const field = details?.fields.find(item => /국내\s*복합(연비|전비)/.test(item.label) && typeof item.value === 'string' && item.value.includes(unit));
  const matched = field?.value.match(/^(\d+(?:\.\d+)?)\s*km\/(L|kWh)\s*$/);
  if (matched && Number(matched[1]) > 0) return { value: Number(matched[1]), unit, estimated: false, basis: `등록된 국내 복합 제원 · ${details.checked_on}`, sourceUrl: details.source_url };
  const fuel = estimates[vehicle.fuel] || estimates.GASOLINE;
  const base = fuel[vehicle.body_type] || fuel.default;
  const highPerformance = vehicle.fuel === 'GASOLINE' && (Number(vehicle.price) >= 200000000 || /Trofeo|M[248]\b|M[248]\d{2}|M40i|M850i/i.test(vehicle.trim || ''));
  const value = Math.round(base * (highPerformance ? 0.8 : 1) * 10) / 10;
  return { value, unit, estimated: true, basis: `계획용 추정 ${value}${unit} · 연료·차체별 기본값${highPerformance ? '에 고성능·고가 차량 보정 0.8배 적용' : ''} · 공식 인증값 아님`, sourceUrl: null };
}
