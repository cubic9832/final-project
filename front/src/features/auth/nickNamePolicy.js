// 닉네임 금지어 (보완 3 추가 · 10-20)
// 서버 back/.../auth/NickNamePolicy.java 와 같은 목록을 쓴다.
// 화면 검사는 바로 알려 주기 위한 편의, 서버 검사가 실제로 막는다.

// 운영자로 오해될 수 있는 단어 (사칭 방지)
const RESERVED_WORDS = [
  'admin', 'root', 'system', 'operator', 'staff', 'official', 'creditcompass',
  '관리자', '운영자', '운영진', '운영팀', '고객센터', '시스템', '크레딧컴퍼스', '크레딧컴패스', '공식계정',
];

// 욕설 · 비속어 (대표적인 것만. 변형까지 모두 막을 수는 없다)
const BAD_WORDS = [
  '시발', '씨발', '씨바', 'ㅅㅂ', '병신', '븅신', 'ㅂㅅ', 'ㅄ', '좆', '존나', '새끼', '지랄',
  '미친놈', '미친년', '애미', '느금', '섹스', 'fuck', 'shit', 'bitch', 'sex',
];

// 소문자로 바꾸고 공백 · 숫자 · 기호를 지운다 → "관 리 자", "Admin_01", "시1발" 도 걸린다
function normalize(nickName) {
  return nickName.toLowerCase().replace(/[\s\d!-/:-@[-`{-~]/g, '');
}

// 금지어가 들어 있으면 오류 문구, 없으면 빈 문자열
export function checkNickNameWords(nickName) {
  const normalized = normalize(nickName);
  if (RESERVED_WORDS.some((word) => normalized.includes(word))) {
    return '운영자로 오해할 수 있는 닉네임은 쓸 수 없습니다.';
  }
  if (BAD_WORDS.some((word) => normalized.includes(word))) {
    return '사용할 수 없는 단어가 들어 있습니다.';
  }
  return '';
}
