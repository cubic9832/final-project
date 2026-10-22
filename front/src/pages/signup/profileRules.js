// 보완 5: 회원가입 개인 정보(전화번호 · 생년월일 · 성별) 입력 규칙
// 서버 SignupRequest · AuthServiceImpl 과 같은 규칙을 쓴다 (화면 검사는 편의, 서버 검사가 최종)

// 가입 가능 나이: 운전면허를 딸 수 있는 만 18세(1·2종 보통 기준)부터. 도로교통법 기준 — 법 조항은 확인 필요
export const MIN_SIGNUP_AGE = 18;

export const GENDER_OPTIONS = [
  { value: 'MALE', label: '남성' },
  { value: 'FEMALE', label: '여성' },
  { value: 'NONE', label: '선택 안 함' },
];

const PHONE_PATTERN = /^010-\d{4}-\d{4}$/;

// 숫자만 남겨 010-1234-5678 모양으로 하이픈을 넣는다 (입력할 때마다 호출)
export function formatPhone(value) {
  const digits = value.replace(/\D/g, '').slice(0, 11);
  if (digits.length <= 3) return digits;
  if (digits.length <= 7) return `${digits.slice(0, 3)}-${digits.slice(3)}`;
  return `${digits.slice(0, 3)}-${digits.slice(3, 7)}-${digits.slice(7)}`;
}

// 전화번호는 선택 항목 (10-22: 문자 인증은 비용이 들어 하지 않으므로 필수에서 뺌) — 비워 두면 통과
export function validatePhone(value) {
  if (!value) return '';
  if (!PHONE_PATTERN.test(value)) return '전화번호는 010-1234-5678 형식으로 입력해 주세요.';
  return '';
}

// 만 나이: 올해 생일이 아직 안 지났으면 1살 뺀다
export function getAge(birthDate, today = new Date()) {
  const birth = new Date(`${birthDate}T00:00:00`);
  let age = today.getFullYear() - birth.getFullYear();
  const birthdayPassed =
    today.getMonth() > birth.getMonth() ||
    (today.getMonth() === birth.getMonth() && today.getDate() >= birth.getDate());
  if (!birthdayPassed) age -= 1;
  return age;
}

// 생년월일 입력칸(type="date")의 값은 'YYYY-MM-DD' 문자열
export function validateBirthDate(value, today = new Date()) {
  if (!value) return '생년월일을 입력해 주세요.';
  const birth = new Date(`${value}T00:00:00`);
  if (Number.isNaN(birth.getTime()) || birth >= today || birth.getFullYear() < 1900) {
    return '생년월일이 올바르지 않습니다.';
  }
  if (getAge(value, today) < MIN_SIGNUP_AGE) {
    return `만 ${MIN_SIGNUP_AGE}세 이상만 가입할 수 있습니다. (운전면허 취득 가능 나이 기준)`;
  }
  return '';
}

export function validateGender(value) {
  return GENDER_OPTIONS.some((option) => option.value === value) ? '' : '성별을 선택해 주세요.';
}

// 오늘 날짜 'YYYY-MM-DD' (생년월일 입력칸 max 값 — 미래 날짜를 고를 수 없게)
export function todayString(today = new Date()) {
  const month = String(today.getMonth() + 1).padStart(2, '0');
  const day = String(today.getDate()).padStart(2, '0');
  return `${today.getFullYear()}-${month}-${day}`;
}
