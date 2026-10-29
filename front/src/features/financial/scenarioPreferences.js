export function buildScenarioPreferences(vehicle, profile, errors) {
  const distance = Number(vehicle.annualDistanceKm ?? 15000);
  if (!Number.isFinite(distance) || distance < 2000 || distance > 50000) errors.push('연간 주행거리');
  profile.annual_distance = distance;
  if (vehicle.chargingAvailable !== undefined && typeof vehicle.chargingAvailable !== 'boolean') errors.push('충전 여건');
  profile.charging_available = vehicle.chargingAvailable ?? false;
  return {};
}
