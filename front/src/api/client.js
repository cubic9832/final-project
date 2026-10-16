import axios from 'axios';
import useAuthStore from '../stores/useAuthStore';
import { refreshAccessToken } from './tokenRefresh';

// 모든 API 호출이 이 인스턴스를 거친다.
// baseURL 이 상대 경로('/api/v1')라서 요청은 Vite 개발 서버(5173)로 가고,
// vite.config.js 의 proxy 가 실제 백엔드로 전달한다.
const client = axios.create({
  baseURL: '/api/v1',
  timeout: 10000,
});

// 요청 인터셉터: 로그인 상태라면 모든 요청에 access token 을 붙인다
// (로그인이 필요 없는 조회 API 에 붙어도 서버는 그대로 처리한다)
client.interceptors.request.use((config) => {
  const { accessToken } = useAuthStore.getState();
  if (accessToken) {
    config.headers.Authorization = `Bearer ${accessToken}`;
  }
  return config;
});

// 토큰 문제로 거절된 경우의 오류 코드 (로그인 실패 LOGIN_FAILED 는 해당하지 않는다)
const TOKEN_ERROR_CODES = ['AUTH_REQUIRED', 'TOKEN_EXPIRED', 'TOKEN_INVALID'];

// 응답 인터셉터
// ① access token 이 만료(TOKEN_EXPIRED)됐으면 refresh token 으로 새로 받아 원래 요청을 한 번 더 보낸다
//    → 사용자는 만료를 느끼지 못한다
// ② 재발급도 실패했거나 토큰이 없음 · 위조(401)면 화면의 로그인 정보를 지운다
//    → 로그인이 필요한 화면(RequireAuth)은 로그인 화면으로 이동한다
client.interceptors.response.use(
  (response) => response,
  async (error) => {
    const original = error.config;
    const code = error.response?.data?.error?.code;

    // _retry: 다시 보낸 요청이 또 실패해도 무한 반복하지 않도록 표시
    if (code === 'TOKEN_EXPIRED' && original && !original._retry) {
      original._retry = true;
      try {
        const accessToken = await refreshAccessToken(); // 실패하면 tokenRefresh 가 로그인 정보를 지운다
        original.headers.Authorization = `Bearer ${accessToken}`;
        return client(original);
      } catch {
        return Promise.reject(error); // 원래 오류(401)를 화면 코드에 넘긴다
      }
    }

    if (error.response?.status === 401 && TOKEN_ERROR_CODES.includes(code)) {
      useAuthStore.getState().clearAuth();
    }
    return Promise.reject(error); // 화면 코드도 실패를 알 수 있게 그대로 넘긴다
  },
);

export default client;