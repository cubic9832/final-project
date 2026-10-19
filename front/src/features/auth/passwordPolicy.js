// 회원가입 비밀번호 규칙 (보완 2 · 보완 목록 ⑤ ⑥)
// 서버 back/.../auth/validation/PasswordPolicy.java 와 같은 규칙을 쓴다.
// 화면 검사는 바로 알려 주기 위한 편의, 서버 검사가 실제로 막는다.

export const PASSWORD_MIN = 8;
export const PASSWORD_MAX = 20;

// 너무 흔해서 금지하는 비밀번호 (소문자로 바꿔 포함 여부를 본다)
const COMMON_WORDS = ['password', 'passw0rd', 'p@ssw0rd', 'qwerty', '1q2w3e4r', 'iloveyou', 'admin', 'letmein', 'welcome'];

// 이어진 문자로 볼 줄: 숫자 · 알파벳 순서, 키보드 가로줄 (거꾸로도 검사)
const SEQUENCES = ['0123456789', 'abcdefghijklmnopqrstuvwxyz', 'qwertyuiop', 'asdfghjkl', 'zxcvbnm'];

// 같은 문자가 3번 이어지면 true (예: 111, aaa)
function hasTripleRepeat(password) {
  return /(.)\1\1/.test(password);
}

// 이어진 문자 4개가 있으면 true (예: 1234, abcd, qwer, 4321)
function hasSequence(password) {
  const lower = password.toLowerCase();
  for (let i = 0; i + 4 <= lower.length; i++) {
    const part = lower.slice(i, i + 4);
    const reversed = [...part].reverse().join('');
    if (SEQUENCES.some((line) => line.includes(part) || line.includes(reversed))) return true;
  }
  return false;
}

// 이메일 @ 앞부분(3자 이상)이 비밀번호에 들어 있으면 true
function containsEmailId(password, email) {
  const id = (email ?? '').trim().toLowerCase().split('@')[0];
  return id.length >= 3 && password.toLowerCase().includes(id);
}

function isCommon(password) {
  const lower = password.toLowerCase();
  return COMMON_WORDS.some((word) => lower.includes(word));
}

// 규칙별 충족 여부 (가입 화면 체크리스트에 그대로 표시)
export function getPasswordRules(password, email) {
  return [
    { label: `${PASSWORD_MIN}~${PASSWORD_MAX}자`, met: password.length >= PASSWORD_MIN && password.length <= PASSWORD_MAX },
    {
      label: '영문 · 숫자 · 특수문자 포함',
      met: /[a-z]/i.test(password) && /\d/.test(password) && /[^a-z0-9\s]/i.test(password) && !/\s/.test(password),
    },
    { label: '같은 문자 3번 · 연속 문자 4개 없음', met: password.length > 0 && !hasTripleRepeat(password) && !hasSequence(password) },
    { label: '이메일 아이디 · 흔한 비밀번호 제외', met: password.length > 0 && !containsEmailId(password, email) && !isCommon(password) },
  ];
}

// 처음 어긋난 규칙의 오류 문구. 모두 맞으면 빈 문자열
export function validatePassword(password, email) {
  if (!password) return '비밀번호를 입력해 주세요.';
  if (password.length < PASSWORD_MIN || password.length > PASSWORD_MAX) {
    return `비밀번호는 ${PASSWORD_MIN}~${PASSWORD_MAX}자로 입력해 주세요.`;
  }
  if (/\s/.test(password)) return '비밀번호에 공백을 넣을 수 없습니다.';
  if (!(/[a-z]/i.test(password) && /\d/.test(password) && /[^a-z0-9]/i.test(password))) {
    return '비밀번호는 영문 · 숫자 · 특수문자를 모두 포함해야 합니다.';
  }
  if (hasTripleRepeat(password)) return '같은 문자를 3번 이상 이어서 쓸 수 없습니다. (예: 111, aaa)';
  if (hasSequence(password)) return '이어진 문자 4개는 쓸 수 없습니다. (예: 1234, abcd, qwer)';
  if (containsEmailId(password, email)) return '비밀번호에 이메일 아이디를 넣을 수 없습니다.';
  if (isCommon(password)) return '너무 흔한 비밀번호입니다. 다른 비밀번호를 입력해 주세요.';
  return '';
}
