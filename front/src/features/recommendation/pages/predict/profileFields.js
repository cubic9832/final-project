export const profileGroups = [
  { title: '기본 정보', fields: [
    { key: '나이_세', label: '나이', unit: '세', min: 18, max: 100 },
    { key: '경력_년', label: '경력', unit: '년', min: 0, max: 80 },
    { key: '가구원수_명', label: '가구원 수', unit: '명', min: 1, max: 30 },
    { key: '부양인원_명', label: '부양 인원', unit: '명', min: 0, max: 30 },
  ] },
  { title: '소득과 월 지출', fields: [
    { key: '개인_연간세전소득_원', label: '연간 세전소득', unit: '만 원/년', scale: 10000 },
    { key: '개인_평균월주거비_원', label: '월 주거비', unit: '만 원/월', scale: 10000 },
    { key: '개인_평균월기타생활소비_원', label: '월 기타 생활비', unit: '만 원/월', scale: 10000 },
    { key: '개인_평균월저축액_원', label: '월 저축액', unit: '만 원/월', scale: 10000 },
  ] },
  { title: '자산과 기존 대출', fields: [
    { key: '개인_현금성자산_원', label: '현금성 자산', unit: '만 원', scale: 10000 },
    { key: '개인_기타금융자산_원', label: '기타 금융자산', unit: '만 원', scale: 10000 },
    { key: '개인_주거보증금자산_원', label: '주거 보증금', unit: '만 원', scale: 10000 },
    { key: '개인_부동산자산_원', label: '부동산 자산', unit: '만 원', scale: 10000 },
    { key: '기존대출잔액_보정전_원', label: '차량 구매 전 대출잔액', unit: '만 원', scale: 10000 },
  ] },
  { title: '차량 이용 조건', fields: [
    { key: '연간_주행거리_km', label: '연간 주행거리', unit: 'km/년', min: 0, max: 300000 },
  ] },
];

export const categoryFields = [
  { key: '성별', label: '성별' }, { key: '직업_유형', label: '직업 유형' },
  { key: '차량_이용목적', label: '차량 이용목적' },
];

export const numericFields = profileGroups.flatMap((group) => group.fields);

export const emptyProfile = Object.fromEntries([...numericFields, ...categoryFields].map(({ key }) => [key, '']));

export function validateProfile(values) {
  const errors = {};
  for (const field of numericFields) {
    const value = Number(values[field.key]);
    if (values[field.key] === '' || !Number.isFinite(value) || value < (field.min ?? 0)
      || (field.max !== undefined && value > field.max) || (!field.scale && !Number.isInteger(value))) {
      const range = field.max ? `${field.min ?? 0}~${field.max} 범위의` : `${field.min ?? 0} 이상의`;
      errors[field.key] = `${field.label}: ${range} ${field.scale ? '숫자' : '정수'}를 입력해 주세요.`;
    }
  }
  for (const field of categoryFields) {
    if (!values[field.key]) errors[field.key] = `${field.label} 항목을 선택해 주세요.`;
  }
  return errors;
}

export function toModelProfile(values) {
  return { ...Object.fromEntries(numericFields.map(({ key, scale = 1 }) => [key, Number(values[key]) * scale])),
    ...Object.fromEntries(categoryFields.map(({ key }) => [key, values[key]])) };
}
