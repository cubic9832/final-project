import client from '../../shared/api/client';

// 내 정보 — 로그인한 회원 { id, email, nickName, role }
// 토큰은 client 의 요청 인터셉터가 자동으로 붙인다
export const getMe = async () => {
  const res = await client.get('/members/me');
  return res.data.data;
};

// 닉네임 변경 (보완 3 추가) — 바뀐 회원 정보를 돌려준다. 다른 회원이 쓰는 닉네임이면 409 NICKNAME_DUPLICATED
export const updateNickName = async (nickName) => {
  const res = await client.patch('/members/me', { nickName });
  return res.data.data;
};

// 회원 탈퇴 (보완 4) — 비밀번호를 한 번 더 보내 확인. 틀리면 400 PASSWORD_MISMATCH
// 보완 8: 구글로만 가입한 회원은 비밀번호 대신 confirmText("탈퇴")
// DELETE 요청에 본문을 실을 때 axios 는 data 옵션을 쓴다
export const withdraw = async ({ password, confirmText }) => {
  await client.delete('/members/me', { data: { password, confirmText } });
};
