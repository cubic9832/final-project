import client from './client';

// 내 정보 — 로그인한 회원 { id, email, nickName, role }
// 토큰은 client 의 요청 인터셉터가 자동으로 붙인다
export const getMe = async () => {
  const res = await client.get('/members/me');
  return res.data.data;
};
