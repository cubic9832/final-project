import { Client } from '@stomp/stompjs';
import { refreshAccessToken } from '../../shared/api/tokenRefresh';
import useAuthStore from '../../stores/useAuthStore';

// 8단계: WebSocket(STOMP) 연결 — 강의 샘플 step4 의 chat/stompClient.js 와 같다
// 지금 열린 페이지 주소로 연결한다 → 개발 중에는 ws://localhost:5173/ws (Vite 가 8080 으로 넘김)
const WS_URL = `${location.protocol === 'https:' ? 'wss' : 'ws'}://${location.host}/ws`;

export const createStompClient = () => {
  const client = new Client({
    brokerURL: WS_URL,
    reconnectDelay: 3000, // 끊기면 3초 뒤 자동으로 다시 연결

    // 연결(재연결 포함)할 때마다 실행 → 항상 "지금" 토큰을 싣는다 (서버 StompAuthInterceptor 가 CONNECT 에서 확인)
    beforeConnect: () => {
      const { accessToken } = useAuthStore.getState();
      client.connectHeaders = { Authorization: `Bearer ${accessToken}` };
    },
  });

  // 서버가 ERROR 로 거절했을 때 (StompErrorHandler 가 오류 코드를 headers.message 에 담는다)
  client.onStompError = (frame) => {
    if (frame.headers.message === 'TOKEN_EXPIRED') {
      // 토큰을 새로 받아 두면, 3초 뒤 재연결할 때 beforeConnect 가 새 토큰을 싣는다 (스터디 2 의 refresh 와 같은 흐름)
      refreshAccessToken().catch(() => client.deactivate()); // 재발급 실패 = 로그아웃 → 재연결 중단
    } else {
      client.deactivate(); // 권한 문제는 다시 연결해도 똑같다
    }
  };

  return client;
};
