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

// 총관리자만: 회원 권한 바꾸기 (ADMIN = 관리자로 지정, USER = 관리자 해제). 바뀐 회원은 다시 로그인해야 적용된다
export const changeMemberRole = async (id, role) => {
  await client.patch(`/admin/members/${id}/role`, { role });
};

// 관리자 · 총관리자: 회원의 로그인 5번 실패 잠금 풀기 (운영 로그에 남는다)
export const unlockMemberLogin = async (id) => {
  await client.post(`/admin/members/${id}/unlock`);
};

// 회원 현황 → { total, admins, newLast7Days, google, daily: [{ date, count }], ageBands, genders }
export const getMemberSummary = async (signal) => {
  const res = await client.get('/admin/members/summary', { signal });
  return res.data.data;
};

// 운영 로그 (관리자 작업 기록, 최근 순) → { logs: [...], meta }. action: ROLE_CHANGE (비우면 전체)
export const getAuditLogs = async ({ action, page = 1, size = 20 } = {}, signal) => {
  const res = await client.get('/admin/audit-logs', { params: { action: action || undefined, page, size }, signal });
  return { logs: res.data.data, meta: res.data.meta };
};

// 서비스 연결 상태 → { apiStartedAt, databaseUp, databaseMillis, databaseVersion }
export const getSystemStatus = async (signal) => {
  const res = await client.get('/admin/system-status', { signal });
  return res.data.data;
};

// 추천 서버(FastAPI) 상태 · 정보: 화면이 추천을 받을 때와 같은 길(Vite proxy /api/v2)로 선택지 정보를 불러 본다
// → { ms: 응답 시간, info: { modelVersion, catalogCount, modelNames, rankerSchema, ... } }. 3초 안에 응답이 없거나 실패하면 오류
export const getModelServerInfo = async (signal) => {
  const start = performance.now();
  const res = await client.get('/recommendation-options', { baseURL: '/api/v2', timeout: 3000, signal });
  return { ms: Math.round(performance.now() - start), info: res.data.data };
};

// 운영 현황: 먼저 확인할 작업(개인정보 미입력 · 로그인 잠금 회원 수) · 재무 진단 이용 현황
// → { profileMissing, lockedMembers, diagnoses: { total, last7Days, members, avgMonthlyAvailable, daily: [{ date, count }] } }
export const getAdminOverview = async (signal) => {
  const res = await client.get('/admin/overview', { signal });
  return res.data.data;
};

// 모델 관리: 학습 · 평가 결과(ml 학습 결과 파일) + 모델 버전 기록(DB)
// → { available, runName, schema, trainedAt, testPairAccuracy, metrics: [{ name, previous, current }], history, versions, ... }
export const getModelReport = async (signal) => {
  const res = await client.get('/admin/model-report', { signal });
  return res.data.data;
};
