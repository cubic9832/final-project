import { useCallback, useEffect, useRef, useState } from 'react';
import { chatErrorMessage, getMessages } from './chatApi';
import { createStompClient } from './stompClient';

// 같은 메시지가 두 번 들어와도 한 번만, 번호 순서대로 (REST 로 읽은 것 + WebSocket 으로 온 것이 겹칠 수 있다 — 샘플과 같음)
const mergeMessages = (prev, incoming) => {
  const map = new Map(prev.map((m) => [m.id, m]));
  incoming.forEach((m) => map.set(m.id, m));
  return [...map.values()].sort((a, b) => a.id - b.id);
};

// 8단계: 상담방 하나의 대화 — 지난 메시지(REST) + 실시간(WebSocket). 회원 상담 화면 · 관리자 상담 탭이 같이 쓴다
// onSystem: 연결 · 넘김 · 종료 안내(SYSTEM)를 받으면 부르는 함수 → 화면이 방 상태를 다시 읽는다
export default function useChatRoom(roomId, onSystem) {
  const [messages, setMessages] = useState([]);
  const [connected, setConnected] = useState(false);
  const [error, setError] = useState('');
  const clientRef = useRef(null);
  const onSystemRef = useRef(onSystem);
  useEffect(() => {
    onSystemRef.current = onSystem; // 최신 함수를 기억 (연결을 다시 맺지 않도록 의존성에서 뺀다)
  }, [onSystem]);

  useEffect(() => {
    if (!roomId) return undefined;

    // 1) 지난 메시지 (REST)
    getMessages(roomId)
      .then((list) => setMessages((prev) => mergeMessages(prev, list)))
      .catch((err) => setError(chatErrorMessage(err, '지난 대화를 불러오지 못했습니다.')));

    // 2) 실시간 메시지 (WebSocket) — 서버 StompAuthInterceptor 가 이 방을 볼 수 있는지 확인한다
    const client = createStompClient();
    client.onConnect = () => {
      setConnected(true);
      client.subscribe(`/topic/chat/rooms/${roomId}`, (frame) => {
        const message = JSON.parse(frame.body);
        setMessages((prev) => mergeMessages(prev, [message]));
        if (message.senderType === 'SYSTEM') onSystemRef.current?.(message);
      });
      // 보내기에 실패하면 (담당이 아님 · 종료됨 · 글자 수) 나에게만 온다
      client.subscribe('/user/queue/errors', (frame) => {
        setError(JSON.parse(frame.body).error.message);
      });
    };
    client.onWebSocketClose = () => setConnected(false);
    client.activate();
    clientRef.current = client;

    // 화면을 떠나거나 방이 바뀌면 연결을 끊고 대화를 비운다 (다음 방의 메시지와 섞이지 않게)
    return () => {
      client.deactivate();
      clientRef.current = null;
      setConnected(false);
      setMessages([]);
      setError('');
    };
  }, [roomId]);

  // 보내기: 화면에는 바로 그리지 않는다 → 서버가 저장하고 돌려준 메시지가 오면 그때 그린다 (번호 · 시각이 정확하게)
  const send = useCallback((text) => {
    if (!text.trim() || !clientRef.current?.connected) return false;
    clientRef.current.publish({ destination: `/app/chat/rooms/${roomId}`, body: JSON.stringify({ content: text }) });
    setError('');
    return true;
  }, [roomId]);

  return { messages, connected, error, send };
}
