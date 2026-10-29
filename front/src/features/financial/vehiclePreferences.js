export const importanceLevels = [
  { value: '5', label: '매우 중요함' }, { value: '4', label: '중요함' }, { value: '3', label: '중간' },
  { value: '2', label: '중요하지 않음' }, { value: '1', label: '매우 중요하지 않음' },
];
export const fuelOptions = ['상관없음', '가솔린', '하이브리드', '디젤', '전기', 'LPG'];
export const bodyTypeOptions = [
  { value: 'any', label: '상관없음' }, { value: 'SEDAN', label: '세단' },
  { value: 'SUV', label: 'SUV' }, { value: 'HATCHBACK', label: '해치백' },
  { value: 'WAGON', label: '왜건' }, { value: 'MPV', label: '미니밴·승합' },
  { value: 'BOX', label: '박스카' }, { value: 'PICKUP', label: '픽업트럭' },
  { value: 'COUPE', label: '쿠페' }, { value: 'CONVERTIBLE', label: '컨버터블' },
  { value: 'ROADSTER', label: '로드스터' },
];
export const bodyPreferenceOptions = [
  { value: 'any', label: '상관없음' }, { value: 'SEDAN', label: '세단' },
  { value: 'SUV', label: 'SUV' }, { value: 'OTHER', label: '그 외 차체' },
];
export const normalizeBodyPreference = value => ['HATCHBACK', 'WAGON', 'MPV', 'BOX', 'PICKUP', 'COUPE', 'CONVERTIBLE', 'ROADSTER'].includes(value) ? 'OTHER' : (bodyPreferenceOptions.some(item => item.value === value) ? value : 'any');
export const bodyTypeLabel = value => [...bodyTypeOptions, ...bodyPreferenceOptions].find(item => item.value === value)?.label ?? '형태 미확인';
export const sizeOptions = [
  { value: 'any', label: '상관없음 · 크기 평가 제외' },
  { value: 'small', label: '작은 크기 · 전장 4.2m 이하' },
  { value: 'medium', label: '보통 크기 · 전장 4.2~4.8m' },
  { value: 'large', label: '큰 크기 · 전장 4.8m 이상' },
];
export const importanceLabel = value => importanceLevels.find(item => item.value === String(value ?? '3'))?.label ?? '중간';
export const sizeLabel = value => sizeOptions.find(item => item.value === value)?.label ?? sizeOptions[0].label;
