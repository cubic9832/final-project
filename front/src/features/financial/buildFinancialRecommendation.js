const purposeLabels = { 출퇴근: '출퇴근', '주말 여가': '여가', '가족 이동': '가족이동', 업무: '업무' };

export function buildFinancialRecommendation(state = {}) {
  const { values = {}, assets = {}, loans, vehicle = {} } = state;
  const errors = [];
  function read(value, label, path, optional = false) {
    if (optional && (value === undefined || value === '')) return 0;
    const amount = Number(value);
    if (value === undefined || value === '' || !Number.isFinite(amount) || amount < 0) {
      errors.push({ label, path });
      return 0;
    }
    return amount;
  }
  const income = (key, label, optional = false) => read(values[key], label, '/financial', optional);
  const asset = (key, label) => read(assets[key], label, '/financial/assets');
  const otherLiving = income('fixed', '월 고정 지출') + income('living', '월 생활비')
    + income('transport', '교통비', true) + income('phone', '통신비', true);
  let loanBalance = 0;
  if (!Array.isArray(loans)) errors.push({ label: '기존 대출 내역', path: '/financial/assets' });
  else loanBalance = loans.reduce((sum, loan) => sum + read(loan.balance, '대출 잔액', '/financial/assets'), 0);
  const gender = values.gender;
  const employment = values.employment;
  if (!gender) errors.push({ label: '성별', path: '/financial' });
  if (!employment) errors.push({ label: '직업 유형', path: '/financial' });
  const purpose = purposeLabels[vehicle.purpose];
  if (!purpose) errors.push({ label: '이용목적', path: '/financial/vehicle' });
  const distanceText = String(vehicle.annualDistance ?? '');
  const distance = /^\d[\d,]*km$/.test(distanceText)
    ? Number(distanceText.replace(/[^0-9]/g, '')) : NaN;
  if (!Number.isFinite(distance)) errors.push({ label: '연간 주행거리', path: '/financial/vehicle' });
  const segment = vehicle.segment ?? 'domestic-car';
  if (!['domestic-car', 'imported-car'].includes(segment)) errors.push({ label: '추천 차량 범위', path: '/financial/vehicle' });
  const profile = {
    '나이_세': income('age', '나이'), '경력_년': income('career', '경력'),
    '가구원수_명': income('householdSize', '가구원 수'), '부양인원_명': income('dependents', '부양 인원'),
    '개인_연간세전소득_원': income('annualGrossIncome', '연간 세전소득') * 10000,
    '개인_현금성자산_원': asset('deposit', '현금·예금') * 10000,
    '개인_기타금융자산_원': asset('financialAssets', '기타 금융자산') * 10000,
    '개인_주거보증금자산_원': asset('housingDeposit', '주거 보증금') * 10000,
    '개인_부동산자산_원': asset('realEstate', '부동산 자산') * 10000,
    '개인_평균월주거비_원': income('housing', '월 주거비') * 10000,
    '개인_평균월기타생활소비_원': otherLiving * 10000,
    '개인_평균월저축액_원': income('averageSavings', '실제 월평균 저축액') * 10000,
    '기존대출잔액_보정전_원': loanBalance * 10000,
    '연간_주행거리_km': distance, '성별': gender, '직업_유형': employment, '차량_이용목적': purpose,
  };
  return { request: errors.length ? null : { segment, profile }, errors };
}
