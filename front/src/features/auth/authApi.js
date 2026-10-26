import useAuthStore from '../../stores/useAuthStore';
import client from '../../shared/api/client';

// 회원가입 — 성공하면 가입한 회원 정보 { id, email, nickName, role, phoneMasked, birthDate, gender } 를 돌려준다.
// 보완 5: phone(010-1234-5678) · birthDate(YYYY-MM-DD) · gender(MALE · FEMALE · NONE) 추가
// 가입만 하고 로그인 상태로 만들지는 않는다 (로그인은 로그인 화면에서 따로 한다)
// 보완 7 추가(10-22): verificationToken = 인증 코드 확인 때 받은 일회용 증명 번호
export const signup = async ({ email, password, nickName, phone, birthDate, gender, verificationToken }) => {
  const res = await client.post('/auth/signup', { email, password, nickName, phone, birthDate, gender, verificationToken });
  return res.data.data;
};

// 보완 3: 중복 확인 — 사용할 수 있으면 true, 이미 사용 중이면 false
// (params 로 넘기면 axios 가 한글 · 특수문자를 주소에 맞게 바꿔 준다)
export const checkEmail = async (email) => {
  const res = await client.get('/auth/check-email', { params: { email } });
  return res.data.data.available;
};

export const checkNickName = async (nickName) => {
  const res = await client.get('/auth/check-nickname', { params: { nickName } });
  return res.data.data.available;
};

// 보완 7: 이메일 인증 코드 받기 — 이미 가입된 이메일이면 409, 너무 자주 요청하면 429
// 성공하면 { expiresInSeconds, resendAfterSeconds, mailEnabled } (mailEnabled false = 개발 모드, 코드는 서버 로그)
export const sendEmailCode = async (email) => {
  const res = await client.post('/auth/email-verification', { email });
  return res.data.data;
};

// 보완 7: 인증 코드 확인 — 틀리면 400 (남은 횟수 안내), 만료 · 5번 틀림도 400
// 보완 7 추가(10-22): 맞으면 일회용 증명 번호를 돌려준다 → 가입 요청에 같이 보낸다
export const confirmEmailCode = async (email, code) => {
  const res = await client.post('/auth/email-verification/confirm', { email, code });
  return res.data.data.verificationToken;
};

// 보완 7 추가: 비밀번호 찾기 — 가입한 이메일로 코드 받기({ expiresInSeconds, resendAfterSeconds, mailEnabled }) · 확인 · 새 비밀번호
// 가입 안 한 이메일 400 EMAIL_NOT_FOUND, 구글로만 가입한 계정 400 SOCIAL_ACCOUNT
export const sendPasswordResetCode = async (email) => {
  const res = await client.post('/auth/password-reset/code', { email });
  return res.data.data;
};

export const confirmPasswordResetCode = async (email, code) => {
  const res = await client.post('/auth/password-reset/confirm', { email, code });
  return res.data.data.verificationToken; // 일회용 증명 번호 (보완 7 추가 · 10-22)
};

// 성공하면 모든 기기 로그인이 끊긴다 → 새 비밀번호로 다시 로그인
export const resetPassword = async (email, newPassword, verificationToken) => {
  await client.post('/auth/password-reset', { email, newPassword, verificationToken });
};

// 보완 2 추가: 마이페이지 비밀번호 변경 — 성공하면 이 기기의 새 토큰을 저장한다 (다른 기기 로그인은 서버가 끊는다)
// 현재 비밀번호 틀림 400 PASSWORD_MISMATCH, 같은 비밀번호 400 SAME_PASSWORD, 규칙 위반 400 PASSWORD_POLICY
export const changePassword = async ({ currentPassword, newPassword }) => {
  const res = await client.post('/auth/password', { currentPassword, newPassword });
  useAuthStore.getState().setAuth(res.data.data);
};

// 보완 8: 구글 로그인 — 연결된 회원 · 동의한 처음 온 사람이면 로그인 처리 후 { member, newMember } 를 돌려준다
// consent: 로그인 화면의 동의 체크(만 18세 이상 · 약관 · 개인정보)를 모두 했는지. 처음 온 사람인데 false 면 400 SIGNUP_CONSENT_REQUIRED
// (10-22: 추가 정보 화면을 없애고 한 번에 가입 — 닉네임은 구글 이름, 생년월일 · 성별은 마이페이지에서)
export const googleLogin = async (idToken, consent) => {
  const res = await client.post('/auth/google', { idToken, consent });
  useAuthStore.getState().setAuth(res.data.data);
  return { member: res.data.data.member, newMember: res.data.data.newMember }; // newMember: 방금 새로 가입했는지
};

// 로그인 — 응답의 access token · 회원 정보를 스토어에 넣고, 회원 정보를 돌려준다
// (refresh token 은 서버가 HttpOnly 쿠키로 보내서 브라우저에 이미 저장되어 있다)
// 보완 6: 여러 번 실패한 뒤에는 recaptchaToken("로봇이 아닙니다" 체크 결과)도 함께 보낸다
export const login = async ({ email, password, recaptchaToken }) => {
  const res = await client.post('/auth/login', { email, password, recaptchaToken });
  useAuthStore.getState().setAuth(res.data.data);
  return res.data.data.member;
};

// 로그아웃 — 서버가 refresh token 을 DB · 쿠키에서 지운다.
// 서버 요청이 실패해도(서버 꺼짐 등) 화면은 로그아웃 상태로 만든다
export const logout = async () => {
  try {
    await client.post('/auth/logout');
  } catch {
    // 화면 로그아웃은 아래 finally 에서 진행한다
  } finally {
    useAuthStore.getState().clearAuth();
  }
};

// 6단계: 로그인된 기기 — refresh 쿠키 경로(/api/v1/auth) 아래라 서버가 "지금 기기" 를 알아본다
// 목록: [{ id, device, loggedInAt, lastUsedAt, current }]
export const getSessions = async () => {
  const res = await client.get('/auth/sessions');
  return res.data.data;
};

// 기기 하나 로그아웃 (남의 기기면 403 SESSION_FORBIDDEN, 지금 기기면 400 CURRENT_SESSION)
export const logoutSession = async (id) => {
  await client.delete(`/auth/sessions/${id}`);
};

// 다른 기기 모두 로그아웃 — 로그아웃한 기기 수를 돌려준다
export const logoutOtherSessions = async () => {
  const res = await client.post('/auth/sessions/logout-others');
  return res.data.data;
};
