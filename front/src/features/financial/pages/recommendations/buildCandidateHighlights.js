import { candidateMoney, fuelLabels } from './candidatePresentation.js';

// Describe observed specifications and user priorities, not inferred satisfaction.
export function buildCandidateHighlights(candidate, preferences = {}) {
  const { vehicle, cost } = candidate;
  const components = candidate.integratedScore?.components ?? [];
  const descriptions = [];
  const add = (key, text) => {
    const component = components.find(item => item.key === key);
    if (component?.weight > 0) descriptions.push({ key, text, weight: component.weight });
  };
  const match = key => components.some(item => item.key === key && item.score === 100);
  if (match('fuel')) {
    const fuel = { PHEV: '플러그인 하이브리드', MILD_HYBRID: '마일드 하이브리드' }[vehicle.original_fuel] || fuelLabels[vehicle.fuel];
    if (fuel) add('fuel', `${fuel} 모델로, 선호하신 연료 조건에 맞아요.`);
  }
  if (match('space') && !candidate.lengthVerificationRequired && Number.isFinite(vehicle.length_mm)) {
    const size = { small: '작은', medium: '보통', large: '큰' }[preferences.preferredSize];
    if (size) add('space', `선호하신 ${size} 크기 범위에 들어요. 차량 길이는 ${(vehicle.length_mm / 1000).toFixed(2)}m예요.`);
  }
  const seats = vehicle.seats ?? (vehicle.seat_options?.length ? Math.min(...vehicle.seat_options) : null);
  if (match('seating') && !candidate.seatingVerificationRequired && seats && Number(preferences.minimumSeats) > 0 && seats >= Number(preferences.minimumSeats)) {
    add('seating', `등록된 승차 정원은 ${seats}명으로, 원하신 ${preferences.minimumSeats}명 이상 탑승 조건에 맞아요.`);
  }
  const remaining = `예상 월 유지비는 ${candidateMoney(cost.monthly_running_cost)}이고, 지출 후 매달 ${candidateMoney(cost.remaining_monthly)}이 남아요.`;
  add('cost', remaining);
  if (preferences.purpose) add('purpose', `${preferences.purpose} 용도를 중요하게 선택하신 조건을 반영해 비교한 후보예요.`);

  const important = descriptions.filter(item => item.weight >= 4).sort((a, b) => b.weight - a.weight);
  // Keep every matching high-priority condition visible; otherwise show up to
  // two matching preferences and a financial explanation.
  const chosen = important.length ? important : descriptions.filter(item => !['cost', 'purpose'].includes(item.key)).sort((a, b) => b.weight - a.weight).slice(0, 2);
  const result = chosen.map(item => item.text);
  if (!chosen.some(item => item.key === 'cost')) result.push(remaining);
  if (result.length < 2) result.push('현재 사용 가능한 예금으로 구매할 수 있어요.');
  return result;
}
