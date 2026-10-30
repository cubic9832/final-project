import { useEffect, useRef, useState } from 'react';
import './ChatThread.css';

// "2026-10-30T13:05:12" → "13:05"
const timeOf = (value) => value?.slice(11, 16) ?? '';

// 8단계: 대화 목록 + 입력칸 (회원 상담 화면 · 관리자 상담 탭이 같이 쓴다)
// viewer: 'member' 면 내 말 = USER, 'admin' 이면 내 말 = ADMIN. 상대 이름: 회원 화면은 "상담원", 관리자 화면은 회원 닉네임
// canSend 가 false 면 입력칸을 막고 disabledText 를 보여 준다 (종료된 상담 · 담당이 아닌 관리자)
export default function ChatThread({ messages, viewer, memberName, connected, error, canSend, disabledText, onSend }) {
  const [text, setText] = useState('');
  const boardRef = useRef(null);
  const mineType = viewer === 'member' ? 'USER' : 'ADMIN';

  // 새 메시지가 오면 맨 아래로 스크롤
  useEffect(() => {
    boardRef.current?.scrollTo({ top: boardRef.current.scrollHeight });
  }, [messages]);

  function handleSubmit(event) {
    event.preventDefault();
    if (onSend(text)) setText('');
  }

  function senderLabel(message) {
    if (message.senderType === mineType) return '나';
    return message.senderType === 'ADMIN' ? '상담원' : memberName;
  }

  return (
    <div className="chat-thread">
      <p className={`chat-connection${connected ? ' is-on' : ''}`} role="status">
        {connected ? '● 실시간 연결됨' : '연결 중… 끊기면 자동으로 다시 연결합니다.'}
      </p>
      <ul className="chat-board" ref={boardRef} aria-label="상담 대화" aria-live="polite">
        {messages.length === 0 && <li className="chat-empty">아직 대화가 없습니다.</li>}
        {messages.map((m) => (m.senderType === 'SYSTEM'
          ? <li key={m.id} className="chat-system">{m.content}</li>
          : (
            <li key={m.id} className={`chat-bubble${m.senderType === mineType ? ' is-mine' : ''}`}>
              <small>{senderLabel(m)} · {timeOf(m.createdAt)}</small>
              {/* 글자로만 그린다 — 상대가 보낸 <script> 가 실행되지 않게 */}
              <p>{m.content}</p>
            </li>
          )))}
      </ul>
      {error && <p className="chat-error" role="alert">{error}</p>}
      {canSend ? (
        <form className="chat-send" onSubmit={handleSubmit}>
          <input
            value={text}
            onChange={(event) => setText(event.target.value)}
            placeholder={connected ? '메시지를 입력하세요 (최대 1000자)' : '연결 중…'}
            maxLength={1000}
            disabled={!connected}
            aria-label="메시지"
          />
          <button type="submit" disabled={!connected || !text.trim()}>보내기</button>
        </form>
      ) : <p className="chat-disabled">{disabledText}</p>}
    </div>
  );
}
