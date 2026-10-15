import axios from 'axios';
import useAuthStore from '../stores/useAuthStore';

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

// 응답 인터셉터: 토큰이 만료 · 무효(401)면 화면의 로그인 정보를 지운다
// → 로그인이 필요한 화면(RequireAuth)은 로그인 화면으로 이동한다.
// refresh token 단계에서 이 자리를 "자동 재발급 후 다시 요청"으로 바꾼다.
client.interceptors.response.use(
  (response) => response,
  (error) => {
    const code = error.response?.data?.error?.code;
    if (error.response?.status === 401 && TOKEN_ERROR_CODES.includes(code)) {
      useAuthStore.getState().clearAuth();
    }
    return Promise.reject(error); // 화면 코드도 실패를 알 수 있게 그대로 넘긴다
  },
);

export default client;