const purposes = { 출퇴근: '출퇴근', '주말 여가': '여가', '가족 이동': '가족이동', 업무: '업무' };

// 진단 UI에서 이미 수집한 값만 사용한다. 없는 인구·자산 정보는 만들지 않는다.
export function buildFinancialRecommendation(state = {}) {
  const { values = {}, assets = {}, loans, vehicle = {} } = state;
  const errors = [];
  function amount(value, label, optional = false) {
    if (optional && (value === undefined || value === '')) return 0;
    if (value === undefined || value === '' || value === null || typeof value === 'boolean' || !Number.isFinite(Number(value)) || Number(value) < 0) {
      errors.push(label);
      return 0;
    }
    return Number(value);
  }
  const netIncome = amount(values.income, '월 실수령액') + amount(values.extraIncome, '기타 정기 소득', true);
  const housing = amount(values.housing, '월 주거비');
  const otherLiving = amount(values.fixed, '월 고정 지출') + amount(values.living, '월 생활비')
    + amount(values.transport, '교통비', true) + amount(values.phone, '통신비', true);
  const cash = amount(assets.deposit, '사용 가능 예금');
  const payment = amount(values.loan, '현재 대출 월 상환액', true);
  let debt = 0;
  if (!Array.isArray(loans)) errors.push('자산·부채 내역');
  else {
    for (const loan of loans) {
      // 기존 UI가 처음에 보여주는 미입력 대출 행은 계산에서도 빈 행이다.
      if (['balance', 'rate', 'payment', 'months'].every((key) => loan[key] === '' || loan[key] === undefined)) continue;
      debt += amount(loan.balance, '대출 잔액');
    }
  }
  const purpose = purposes[vehicle.purpose];
  if (!purpose) errors.push('차량 이용목적');
  const distanceText = String(vehicle.annualDistance ?? '');
  const distance = /^\d[\d,]*km$/.test(distanceText) ? Number(distanceText.replace(/[^0-9]/g, '')) : NaN;
  if (!Number.isFinite(distance)) errors.push('연간 주행거리');
  return {
    errors,
    request: errors.length ? null : { segment: 'all-cars', profile: {
      '개인_평균월실수령소득_원': Math.round(netIncome * 10000),
      '개인_현금성자산_원': Math.round(cash * 10000),
      '개인_평균월주거비_원': Math.round(housing * 10000),
      '개인_평균월기타생활소비_원': Math.round(otherLiving * 10000),
      '기존대출잔액_보정전_원': Math.round(debt * 10000),
      '기존월상환액_보정전_원': Math.round(payment * 10000),
      '연간_주행거리_km': distance, '차량_이용목적': purpose,
    } },
  };
}
