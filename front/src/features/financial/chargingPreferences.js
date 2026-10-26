export const chargingOptions = [
  '집·직장에서 충전 가능',
  '공용 충전소를 정기적으로 이용 가능',
  '충전 환경이 불편하거나 확보되지 않음',
  '잘 모르겠음',
];

export function normalizeCharging(value) {
  if (['집에서 충전 가능', '직장에서 충전 가능', '집 · 직장 충전 가능'].includes(value)) return chargingOptions[0];
  if (value === '충전 불가') return chargingOptions[2];
  return value;
}

export function canChargeRegularly(value) {
  return chargingOptions.slice(0, 2).includes(normalizeCharging(value));
}
