const purposes = { 출퇴근: 'commute', '주말 여가': 'leisure', '가족 이동': 'family', 업무: 'business' };
const fuels = { 가솔린: 'GASOLINE', 하이브리드: 'HYBRID', 디젤: 'DIESEL', LPG: 'LPG', 전기: 'ELECTRIC', 상관없음: null };

// UI 금액(만 원)을 v2 계약(원)으로 변환한다. 미입력 필수값을 임의로 만들지 않는다.
export function buildCandidateRecommendation({ values = {}, assets = {}, loans, vehicle = {} } = {}) {
  const errors = [];
  function amount(value, label, optional = false) {
    if (optional && (value === undefined || value === '')) return 0;
    if (value === undefined || value === '' || value === null || typeof value === 'boolean' || !Number.isFinite(Number(value)) || Number(value) < 0) {
      errors.push(label);
      return 0;
    }
    return Math.round(Number(value) * 10000);
  }
  const profile = {
    monthly_income: amount(values.income, '월 실수령액') + amount(values.extraIncome, '기타 정기 소득', true),
    monthly_expenses: amount(values.housing, '월 주거비') + amount(values.fixed, '월 고정 지출') + amount(values.living, '월 생활비')
      + amount(values.transport, '교통비', true) + amount(values.phone, '통신비', true),
    existing_monthly_payment: 0,
    liquid_assets: amount(assets.deposit, '사용 가능 예금'),
    down_payment: amount(assets.downPayment, '선수금'),
    emergency_reserve: amount(assets.emergency, '비상 자금'),
    monthly_savings: amount(values.savings, '목표 저축', true),
    annual_rate: 0.06,
    minimum_buffer: amount(vehicle.minimumBuffer, '구매 후 최소 월 여유자금', true),
    purpose: purposes[vehicle.purpose],
    preferred_fuel: fuels[vehicle.fuel],
    charging_available: ['집에서 충전 가능', '직장에서 충전 가능', '집 · 직장 충전 가능'].includes(vehicle.charging),
    cost_importance: Number(vehicle.costImportance ?? 3),
    space_importance: Number(vehicle.spaceImportance ?? 3),
    minimum_seats: Number(vehicle.minimumSeats ?? 0),
    preferred_size: vehicle.preferredSize ?? 'any',
  };
  if (!Array.isArray(loans)) errors.push('대출 내역');
  else for (const loan of loans) {
    if ([loan.balance, loan.payment].every(value => value === '' || value === undefined)) continue;
    amount(loan.balance, '대출 잔액', true);
    profile.existing_monthly_payment += amount(loan.payment, '대출 월 상환액');
  }
  const distance = /^\d[\d,]*km$/.test(vehicle.annualDistance ?? '') ? Number(vehicle.annualDistance.replace(/[^0-9]/g, '')) : NaN;
  profile.annual_distance = distance;
  const months = vehicle.installment === '일시불' ? 0 : /^(24|36|48|60)개월$/.test(vehicle.installment ?? '') ? Number.parseInt(vehicle.installment, 10) : NaN;
  profile.months = months;
  if (!Number.isFinite(distance) || distance > 200000) errors.push('연간 주행거리');
  if (!Number.isFinite(months)) errors.push('할부 기간');
  if (!profile.purpose) errors.push('이용 목적');
  if (![profile.cost_importance, profile.space_importance].every(value => Number.isInteger(value) && value >= 1 && value <= 5)) errors.push('요소 중요도');
  if (!Number.isInteger(profile.minimum_seats) || profile.minimum_seats < 0 || profile.minimum_seats > 9) errors.push('최소 탑승 인원');
  if (!['any', 'small', 'medium', 'large'].includes(profile.preferred_size)) errors.push('선호 크기');
  if (!(vehicle.fuel in fuels)) errors.push('선호 연료');
  if (!['충전 불가', '집에서 충전 가능', '직장에서 충전 가능', '집 · 직장 충전 가능'].includes(vehicle.charging)) errors.push('충전 가능 여부');
  if (profile.down_payment + profile.emergency_reserve > profile.liquid_assets) errors.push('선수금과 비상 자금 합계는 예금 이내여야 합니다');
  return { errors, request: errors.length ? null : { profile, k: 3 } };
}
