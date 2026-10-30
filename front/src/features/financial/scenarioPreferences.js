import { buildLifestylePreferences } from './lifestylePreferences.js';

export function buildScenarioPreferences(vehicle, profile, errors) {
  profile.annual_distance = 15000;
  if (vehicle.fuel === '전기' && vehicle.chargingAvailable !== undefined && typeof vehicle.chargingAvailable !== 'boolean') errors.push('충전 여건');
  profile.charging_available = vehicle.fuel === '전기' && vehicle.chargingAvailable === true;
  const taste = buildLifestylePreferences(vehicle, errors);
  const importance = (key, label) => {
    const value = Number(vehicle[key] ?? 3);
    if (!Number.isInteger(value) || value < 1 || value > 5) errors.push(label);
    return value;
  };
  return {
    sportiness: taste.sportiness, angularity: taste.angularity, acceleration: taste.acceleration,
    design_importance: taste.design_importance, performance_importance: taste.performance_importance,
    asset_retention_importance: importance('assetRetentionImportance', '구매 후 자금 보존 중요도'),
    running_cost_importance: importance('runningCostImportance', '월 유지비 중요도'),
  };
}
