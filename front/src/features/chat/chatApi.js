import client from '../../shared/api/client';

// 8단계: 1:1 상담 (REST). 실시간 메시지는 stompClient.js (WebSocket)

// ── 회원 ──
// 내 상담방 → { id, status: WAITING · ACTIVE · CLOSED, ... } 또는 null (아직 상담한 적 없음)
export const getMyRoom = async () => (await client.get('/chat/me')).data.data;

// [상담 시작] · [새로 상담하기] → 내 상담방 (대기)
export const startConsultation = async () => (await client.post('/chat/me')).data.data;

// 회원이 [상담 종료]
export const closeMyConsultation = async () => {
  await client.post('/chat/me/close');
};

// 끝난 상담의 만족도 { rating, comment, reported, reportReason } (상담 1번에 한 번)
export const submitFeedback = async (feedback) => {
  await client.post('/chat/me/feedback', feedback);
};

// ── 회원 · 관리자 공통 ──
// 지난 메시지 (오래된 → 최근). beforeId 를 주면 그보다 오래된 30개
export const getMessages = async (roomId, beforeId) =>
  (await client.get(`/chat/rooms/${roomId}/messages`, { params: { beforeId } })).data.data;

// ── 관리자 (/api/v1/admin/** — 관리자 · 총관리자만) ──
// 상담 목록. status: WAITING · ACTIVE · CLOSED (비우면 전체)
export const getAdminRooms = async (status, signal) =>
  (await client.get('/admin/chat/rooms', { params: { status: status || undefined }, signal })).data.data;

// 넘겨받을 수 있는 관리자 목록 → [{ id, nickName, role }]
export const getChatAdmins = async () => (await client.get('/admin/chat/admins')).data.data;

export const assignRoom = async (roomId) => {
  await client.post(`/admin/chat/rooms/${roomId}/assign`);
};

export const transferRoom = async (roomId, adminId, reason) => {
  await client.post(`/admin/chat/rooms/${roomId}/transfer`, { adminId, reason: reason || undefined });
};

export const closeRoom = async (roomId) => {
  await client.post(`/admin/chat/rooms/${roomId}/close`);
};

// [상담 제한]: days 일 동안 새 상담 불가 (진행 중이면 종료). 이유는 운영 로그에만
export const restrictRoom = async (roomId, days, reason) => {
  await client.post(`/admin/chat/rooms/${roomId}/restrict`, { days, reason: reason || undefined });
};

// [경고]: 제한 전 단계. 회원에게 사유 · 횟수가 안내된다
export const warnRoom = async (roomId, reason) => {
  await client.post(`/admin/chat/rooms/${roomId}/warn`, { reason });
};

// 만족도 · 신고 (총관리자만): 상담원별 평균 → [{ adminId, nickName, count, averageRating, reportCount }]
export const getFeedbackSummary = async () => (await client.get('/admin/chat/feedback/summary')).data.data;

// 이 회원이 남긴 만족도 · 신고 → [{ rating, comment, reported, reportReason, adminNickName, createdAt }]
export const getRoomFeedback = async (roomId) => (await client.get(`/admin/chat/rooms/${roomId}/feedback`)).data.data;

// 자주 쓰는 문구 (내 것만) → [{ id, content }]. 등록 · 삭제는 바뀐 목록을 돌려준다
export const getQuickReplies = async () => (await client.get('/admin/chat/quick-replies')).data.data;

export const addQuickReply = async (content) => (await client.post('/admin/chat/quick-replies', { content })).data.data;

export const deleteQuickReply = async (id) => (await client.delete(`/admin/chat/quick-replies/${id}`)).data.data;

export const unrestrictRoom = async (roomId) => {
  await client.post(`/admin/chat/rooms/${roomId}/unrestrict`);
};

// 제한 끝나는 시각 "2026-11-02T15:00:00" → "11월 2일 15:00까지 상담 제한" (서버 안내 문구와 같은 모양)
// 영구 제한은 서버가 9999년으로 저장한다 → "영구 상담 제한"
export const restrictionLabel = (value) => {
  if (!value) return '';
  if (value.startsWith('9999')) return '영구 상담 제한';
  return `${Number(value.slice(5, 7))}월 ${Number(value.slice(8, 10))}일 ${value.slice(11, 16)}까지 상담 제한`;
};

// 서버 실패 봉투의 안내 문구 (없으면 fallback)
export const chatErrorMessage = (error, fallback) => error?.response?.data?.error?.message ?? fallback;
