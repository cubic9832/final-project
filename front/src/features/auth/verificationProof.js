// 이메일 인증 일회용 증명 번호 보관 (보완 7 추가 · 10-22)
// 코드 확인에 성공하면 서버가 준 번호를 이 브라우저 탭(sessionStorage)에 30분 보관한다.
// → 인증 후 새로고침해도 다시 인증하지 않고 이어서 가입 · 비밀번호 변경을 할 수 있다 (서버는 이 번호가 있어야 통과시킨다)
// 탭을 닫으면 사라지고, 다른 사람 브라우저에는 없다.

const KEY = 'emailVerificationProof';
const VALID_MS = 30 * 60 * 1000; // 서버의 인증 유효 시간과 같다

function readAll() {
  try {
    return JSON.parse(sessionStorage.getItem(KEY)) ?? {};
  } catch {
    return {}; // 저장소를 쓸 수 없는 환경이면 보관 없이 진행 (새로고침하면 다시 인증)
  }
}

function writeAll(proofs) {
  try {
    sessionStorage.setItem(KEY, JSON.stringify(proofs));
  } catch {
    // 무시 — 보관만 못 할 뿐 지금 화면에서는 그대로 진행된다
  }
}

// 코드 확인 성공 → 이메일별로 번호 저장
export function saveProof(email, token) {
  const proofs = readAll();
  proofs[email.toLowerCase()] = { token, expiresAt: Date.now() + VALID_MS };
  writeAll(proofs);
}

// 아직 기한이 남은 번호 (없으면 null)
export function getProof(email) {
  const proof = readAll()[email.toLowerCase()];
  return proof && proof.expiresAt > Date.now() ? proof.token : null;
}

// 가입 · 비밀번호 변경에 썼거나 서버가 거절하면 지운다
export function clearProof(email) {
  const proofs = readAll();
  delete proofs[email.toLowerCase()];
  writeAll(proofs);
}
