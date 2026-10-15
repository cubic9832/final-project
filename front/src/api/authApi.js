import client from './client';

// 회원가입 — 성공하면 가입한 회원 정보 { id, email, nickName, role } 를 돌려준다.
// 가입만 하고 로그인 상태로 만들지는 않는다 (로그인은 로그인 화면에서 따로 한다)
export const signup = async ({ email, password, nickName }) => {
  const res = await client.post('/auth/signup', { email, password, nickName });
  return res.data.data;
};
