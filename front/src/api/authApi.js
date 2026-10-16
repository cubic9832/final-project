import useAuthStore from '../stores/useAuthStore';
import client from './client';

// 회원가입 — 성공하면 가입한 회원 정보 { id, email, nickName, role } 를 돌려준다.
// 가입만 하고 로그인 상태로 만들지는 않는다 (로그인은 로그인 화면에서 따로 한다)
export const signup = async ({ email, password, nickName }) => {
  const res = await client.post('/auth/signup', { email, password, nickName });
  return res.data.data;
};

// 로그인 — 응답의 access token · 회원 정보를 스토어에 넣고, 회원 정보를 돌려준다
// (refresh token 은 서버가 HttpOnly 쿠키로 보내서 브라우저에 이미 저장되어 있다)
export const login = async ({ email, password }) => {
  const res = await client.post('/auth/login', { email, password });
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
