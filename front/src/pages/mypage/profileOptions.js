// 6단계: 개인정보 · 계정 관리와 마이페이지가 함께 쓰는 선택지 · 표시 문구
// value 는 서버(ProfileUpdateRequest)와 같은 값, label 은 화면 문구
import { GENDER_OPTIONS } from '../signup/profileRules';

// 운전 경력 (선택) — 보험료 등 비용 계산에 쓸 수 있는 값
export const DRIVING_OPTIONS = [
  { value: 'NONE', label: '면허 없음', tag: '운전면허 없음' },
  { value: 'UNDER_1Y', label: '1년 미만', tag: '운전 1년 미만' },
  { value: 'YEARS_1_3', label: '1~3년', tag: '운전 1~3년' },
  { value: 'OVER_3Y', label: '3년 이상', tag: '운전 3년 이상' },
];

// 구매 예정 시기 (선택) — 구매계획 목표일에 쓸 수 있는 값
export const PURCHASE_OPTIONS = [
  { value: 'WITHIN_3M', label: '3개월 안', tag: '3개월 안 구매 예정' },
  { value: 'WITHIN_6M', label: '6개월 안', tag: '6개월 안 구매 예정' },
  { value: 'WITHIN_1Y', label: '1년 안', tag: '1년 안 구매 예정' },
  { value: 'UNDECIDED', label: '미정', tag: '구매 시기 미정' },
];

const findOption = (options, value) => options.find((option) => option.value === value);

export const genderLabel = (value) => findOption(GENDER_OPTIONS, value)?.label ?? null;
export const drivingTag = (value) => findOption(DRIVING_OPTIONS, value)?.tag ?? null;
export const purchaseTag = (value) => findOption(PURCHASE_OPTIONS, value)?.tag ?? null;

// 1998-05-14 → 1998.05.14
export const formatDate = (value) => (value ? value.replaceAll('-', '.') : null);

// 서버 시각(2026-10-26T09:41:00) → "오늘 09:41" · "10.24 18:02"
export function formatDateTime(value, now = new Date()) {
  if (!value) return '';
  const date = new Date(value);
  const time = `${String(date.getHours()).padStart(2, '0')}:${String(date.getMinutes()).padStart(2, '0')}`;
  if (date.toDateString() === now.toDateString()) return `오늘 ${time}`;
  return `${String(date.getMonth() + 1).padStart(2, '0')}.${String(date.getDate()).padStart(2, '0')} ${time}`;
}

// 서버가 기기를 알아보지 못하면(User-Agent 없음) null
export const deviceName = (device) => device ?? '알 수 없는 기기';
