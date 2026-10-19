// 이메일 도메인 오타 안내 (보완 2 · 보완 목록 ⑨)
// 형식은 맞지만 자주 틀리는 도메인이면 맞는 도메인을 제안한다. 가입을 막지는 않는다.
// (진짜 주소인지는 이메일 인증 — 보완 7 에서 확인)
const TYPO_DOMAINS = {
  'gmail.co': 'gmail.com',
  'gmail.con': 'gmail.com',
  'gmail.cm': 'gmail.com',
  'gmial.com': 'gmail.com',
  'gmai.com': 'gmail.com',
  'gamil.com': 'gmail.com',
  'naver.co': 'naver.com',
  'naver.con': 'naver.com',
  'navr.com': 'naver.com',
  'naer.com': 'naver.com',
  'hanmail.ne': 'hanmail.net',
  'hanmail.com': 'hanmail.net',
  'daum.ne': 'daum.net',
  'nate.co': 'nate.com',
  'kakao.co': 'kakao.com',
  'hotmail.co': 'hotmail.com',
  'outlook.co': 'outlook.com',
};

// 오타로 보이면 고친 이메일 전체를, 아니면 빈 문자열을 돌려준다
export function suggestEmail(email) {
  const [id, domain] = email.trim().toLowerCase().split('@');
  if (!id || !domain) return '';
  const fixed = TYPO_DOMAINS[domain];
  return fixed ? `${id}@${fixed}` : '';
}
