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

// 서버 실패 봉투의 안내 문구 (없으면 fallback)
export const chatErrorMessage = (error, fallback) => error?.response?.data?.error?.message ?? fallback;
