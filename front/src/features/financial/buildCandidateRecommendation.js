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
    monthly_expenses: values.monthlyExpenses !== undefined
      ? amount(values.monthlyExpenses, '월 생활지출 합계')
      : amount(values.housing, '월 주거비') + amount(values.fixed, '월 고정 지출') + amount(values.living, '월 생활비')
        + amount(values.transport, '교통비', true) + amount(values.phone, '통신비', true),
    existing_monthly_payment: 0,
    liquid_assets: amount(assets.deposit, '사용 가능 예금'),
    // Removed UI fields are zeroed for API compatibility, including old saved inputs.
    emergency_reserve: 0,
    monthly_savings: 0, // Retained only for API compatibility; ignore old saved values.
    minimum_buffer: 0,
    purpose: 'commute', // Fixed compatibility value; purpose is not evaluated.
    preferred_fuel: fuels[vehicle.fuel],
    charging_available: false,
    cost_importance: Number(vehicle.costImportance ?? 3),
    space_importance: Number(vehicle.spaceImportance ?? 3),
    fuel_importance: Number(vehicle.fuelImportance ?? 3),
    seating_importance: Number(vehicle.seatingImportance ?? 3),
    purpose_importance: 1,
    minimum_seats: Number(vehicle.minimumSeats ?? 0),
    preferred_size: vehicle.preferredSize ?? 'any',
    preferred_body_type: vehicle.preferredBodyType ?? 'any',
    body_importance: Number(vehicle.bodyImportance ?? 3),
  };
  if (!Array.isArray(loans)) errors.push('대출 내역');
  else for (const loan of loans) {
    if ([loan.balance, loan.payment].every(value => value === '' || value === undefined)) continue;
    profile.existing_monthly_payment += amount(loan.payment, '대출 월 상환액');
  }
  // 사용자 입력이 아닌 유지비 비교 기준. 차량 이용 화면에 같은 기준을 안내한다.
  profile.annual_distance = 15000;
  if (![profile.cost_importance, profile.space_importance, profile.fuel_importance, profile.seating_importance, profile.purpose_importance].every(value => Number.isInteger(value) && value >= 1 && value <= 5)) errors.push('요소 중요도');
  if (!Number.isInteger(profile.minimum_seats) || profile.minimum_seats < 0 || profile.minimum_seats > 9) errors.push('최소 탑승 인원');
  if (!['any', 'small', 'medium', 'large'].includes(profile.preferred_size)) errors.push('선호 크기');
  if (!(vehicle.fuel in fuels)) errors.push('선호 연료');
  if (!['any', 'SEDAN', 'SUV', 'HATCHBACK', 'WAGON', 'MPV', 'BOX', 'PICKUP', 'COUPE', 'CONVERTIBLE', 'ROADSTER', 'OTHER'].includes(profile.preferred_body_type)) errors.push('선호 차체 형태');
  if (!Number.isInteger(profile.body_importance) || profile.body_importance < 1 || profile.body_importance > 5) errors.push('차체 형태 중요도');
  return { errors, request: errors.length ? null : { profile, k: 3 } };
}
