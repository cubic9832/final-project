import { useCallback, useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import ChatThread from '../../features/chat/components/ChatThread';
import {
  chatErrorMessage, closeMyConsultation, formatRestrictedUntil, getMyRoom, startConsultation,
} from '../../features/chat/chatApi';
import useChatRoom from '../../features/chat/useChatRoom';
import useAuthStore from '../../stores/useAuthStore';
import './ConsultationPage.css';

const STATUS_LABELS = { WAITING: '상담원 연결 대기', ACTIVE: '상담 중', CLOSED: '상담 종료' };

// 8단계: /consultation — 회원의 1:1 상담 (마이페이지 · 콤파의 [1:1 상담] 버튼이 여기로 온다). 로그인 필요(RequireAuth)
// 상태: 상담 전(방 없음) → [상담 시작] → 대기 → 상담원이 맡으면 상담 중 → 종료 → [새로 상담하기] → 대기 (같은 방, 지난 대화가 이어진다)
export default function ConsultationPage() {
  const member = useAuthStore((state) => state.member);
  const [state, setState] = useState({ status: 'loading', room: null, error: '' });
  const [busy, setBusy] = useState(false);
  const [actionError, setActionError] = useState('');

  // 방 상태 다시 읽기 — 처음 열 때 · 연결 / 넘김 / 종료 안내(SYSTEM)를 받을 때
  const loadRoom = useCallback(() => {
    getMyRoom()
      .then((room) => setState({ status: 'done', room, error: '' }))
      .catch((error) => setState({ status: 'error', room: null, error: chatErrorMessage(error, '상담 정보를 불러오지 못했습니다.') }));
  }, []);

  useEffect(() => {
    loadRoom();
  }, [loadRoom]);

  const { room } = state;
  const chat = useChatRoom(room?.id, loadRoom);

  // [상담 시작] · [새로 상담하기] → 대기
  async function handleStart() {
    setBusy(true);
    setActionError('');
    try {
      const next = await startConsultation();
      setState({ status: 'done', room: next, error: '' });
    } catch (error) {
      setActionError(chatErrorMessage(error, '상담을 시작하지 못했습니다. 잠시 후 다시 시도해 주세요.'));
    } finally {
      setBusy(false);
    }
  }

  async function handleClose() {
    if (!window.confirm('상담을 종료할까요? 나중에 [새로 상담하기]로 다시 물어볼 수 있어요.')) return;
    setBusy(true);
    setActionError('');
    try {
      await closeMyConsultation();
      loadRoom();
    } catch (error) {
      setActionError(chatErrorMessage(error, '상담을 종료하지 못했습니다.'));
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="consult-page">
      <header className="consult-heading">
        <div>
          <span className="consult-eyebrow">1:1 상담</span>
          <h1>상담원에게 직접 물어보세요</h1>
          <p>재무 진단 결과나 차량 선택이 고민될 때 상담원이 답해 드려요. 상담원이 자리에 없어도 남긴 메시지는 저장됩니다.</p>
          {/* 상담원 보호 안내: 금칙어는 서버가 막고(ChatContentFilter), 반복되면 관리자가 상담을 제한한다 */}
          <p className="consult-policy">욕설 · 비하 · 성적인 표현은 보낼 수 없으며, 반복되면 상담이 일정 기간 제한될 수 있습니다.</p>
        </div>
        <Link className="consult-back" to="/mypage">마이페이지로</Link>
      </header>

      <section className="consult-card" aria-label="상담">
        {state.status === 'loading' && <p className="consult-info">상담 정보를 불러오는 중…</p>}
        {state.status === 'error' && (
          <div className="consult-info">
            <p>{state.error}</p>
            <button type="button" className="consult-button" onClick={loadRoom}>다시 시도</button>
          </div>
        )}

        {/* 상담한 적 없음 */}
        {state.status === 'done' && !room && (
          <div className="consult-start">
            <p><strong>{member?.nickName}님</strong>, 궁금한 점을 상담원에게 남겨 주세요.</p>
            <button type="button" className="consult-button" onClick={handleStart} disabled={busy}>상담 시작</button>
          </div>
        )}

        {state.status === 'done' && room && (
          <>
            <div className="consult-status">
              <span className={`consult-badge is-${room.status.toLowerCase()}`}>{STATUS_LABELS[room.status]}</span>
              {room.status === 'CLOSED'
                ? <button type="button" className="consult-button" onClick={handleStart} disabled={busy || room.restricted}>새로 상담하기</button>
                : <button type="button" className="consult-outline" onClick={handleClose} disabled={busy}>상담 종료</button>}
            </div>
            <ChatThread
              messages={chat.messages}
              viewer="member"
              connected={chat.connected}
              error={chat.error}
              canSend={room.status !== 'CLOSED'}
              disabledText={room.restricted
                ? `운영 정책 위반으로 ${formatRestrictedUntil(room.restrictedUntil)}까지 새 상담을 시작할 수 없습니다.`
                : '종료된 상담입니다. 더 궁금한 점이 있으면 [새로 상담하기]를 눌러 주세요.'}
              onSend={chat.send}
            />
          </>
        )}
        {actionError && <p className="consult-error" role="alert">{actionError}</p>}
      </section>
    </div>
  );
}
