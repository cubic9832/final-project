export const importanceLevels = [
  { value: '5', label: '매우 중요함' }, { value: '4', label: '중요함' }, { value: '3', label: '중간' },
  { value: '2', label: '중요하지 않음' }, { value: '1', label: '매우 중요하지 않음' },
];
export const sizeOptions = [
  { value: 'any', label: '상관없음 · 크기 평가 제외' },
  { value: 'small', label: '작은 크기 · 전장 4.2m 이하' },
  { value: 'medium', label: '보통 크기 · 전장 4.2~4.8m' },
  { value: 'large', label: '큰 크기 · 전장 4.8m 이상' },
];
export const importanceLabel = value => importanceLevels.find(item => item.value === String(value ?? '3'))?.label ?? '중간';
export const sizeLabel = value => sizeOptions.find(item => item.value === value)?.label ?? sizeOptions[0].label;
