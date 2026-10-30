export const initialLifestylePreferences = {
  exteriorSportiness: 'any', exteriorAngularity: 'any', accelerationPreference: 'any',
  lifestylePurpose: 'any', preferredBrand: '', designImportance: '3',
  performanceImportance: '3', lifestylePurposeImportance: '3', brandImportance: '3',
};
export const lifestyleBrands = ['BMW', 'KG모빌리티', 'MINI', '기아', '렉서스', '르노코리아', '마세라티', '메르세데스-벤츠', '볼보', '쉐보레', '제네시스', '테슬라', '토요타', '현대'];

export function lifestyleSummary(vehicle = {}) {
  const scenario = vehicle.scenarioMode ? [
    vehicle.fuel !== '상관없음' && vehicle.fuel,
    vehicle.fuel === '전기' && (vehicle.chargingAvailable ? '전기차 충전 가능' : '전기차 충전 여건 없음'),
    `예금 보존 중요도 ${vehicle.assetRetentionImportance ?? 3}/5`,
    `유지비 중요도 ${vehicle.runningCostImportance ?? 3}/5`] : [];
  const lines = ({ 0: '둥근 윤곽', 0.5: '직선·곡선 조화', 1: '각진 윤곽' })[vehicle.exteriorAngularity];
  const purpose = ({ commute: '도심 이동', family: '가족 이동', 'weekend-drive': '주말 드라이브' })[vehicle.lifestylePurpose];
  const acceleration = ({ 0: '낮은 가속 성능', 0.5: '중간 가속 성능', 1: '빠른 가속 선호' })[vehicle.accelerationPreference];
  return [...scenario, lines, acceleration, !vehicle.scenarioMode && purpose, !vehicle.scenarioMode && vehicle.fuel !== '상관없음' && vehicle.fuel].filter(Boolean).join(' · ') || '선호 조건 없음';
}

export function buildLifestylePreferences(vehicle, errors) {
  const input = { ...initialLifestylePreferences, ...vehicle };
  const target = (key, label) => {
    if (input[key] === 'any') return null;
    if (!['0', '0.5', '1'].includes(String(input[key]))) { errors.push(label); return null; }
    return Number(input[key]);
  };
  const importance = key => {
    const value = Number(input[key]);
    if (!Number.isInteger(value) || value < 1 || value > 5) errors.push('취향 중요도');
    return value;
  };
  if (!['any', 'commute', 'family', 'weekend-drive'].includes(input.lifestylePurpose)) errors.push('주 사용 목적');
  return {
    sportiness: null, angularity: target('exteriorAngularity', '차체 윤곽'),
    acceleration: target('accelerationPreference', '가속 성능 선호'),
    purpose: input.lifestylePurpose === 'any' ? null : input.lifestylePurpose, brand: null,
    design_importance: importance('designImportance'), performance_importance: importance('performanceImportance'),
    purpose_importance: importance('lifestylePurposeImportance'), brand_importance: 3,
  };
}
