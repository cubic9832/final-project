import client from '../../shared/api/client';

// 7단계: 관리자 API — /api/v1/admin/** 는 서버가 ADMIN 에게만 준다 (일반 회원 403, 비회원 401)

// 회원 목록 한 페이지 (최근 가입 순). keyword: 닉네임 · 이메일 일부, role: USER · ADMIN (비우면 전체)
// → { members: [...], meta: { page, size, total, totalPages } }
export const getAdminMembers = async ({ keyword, role, page, size = 10 }, signal) => {
  const res = await client.get('/admin/members', {
    params: { keyword: keyword || undefined, role: role || undefined, page, size },
    signal,
  });
  return { members: res.data.data, meta: res.data.meta };
};

// 회원 현황 → { total, admins, newLast7Days, google, daily: [{ date, count }], ageBands, genders }
export const getMemberSummary = async (signal) => {
  const res = await client.get('/admin/members/summary', { signal });
  return res.data.data;
};
