import { useCallback, useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import ChatThread from '../../features/chat/components/ChatThread';
import ChatConfirmModal from '../../features/chat/components/ChatConfirmModal';
import ChoiceWithOther from '../../features/chat/components/ChoiceWithOther';
import { choiceText, OTHER } from '../../features/chat/choice';
import {
  chatErrorMessage, closeMyConsultation, getMyRoom, restrictionLabel, startConsultation, submitFeedback,
} from '../../features/chat/chatApi';
import useChatRoom from '../../features/chat/useChatRoom';
import useAuthStore from '../../stores/useAuthStore';
import { showToast } from '../../stores/useToastStore';
import './ConsultationPage.css';

const STATUS_LABELS = { WAITING: '상담원 연결 대기', ACTIVE: '상담 중', CLOSED: '상담 종료' };

// 8단계: /mypage/consultation — 회원의 1:1 상담 (마이페이지 · 콤파의 [1:1 상담] 버튼이 여기로 온다). 로그인 필요(RequireAuth)
// 상태: 상담 전(방 없음) → [상담 시작] → 대기 → 상담원이 맡으면 상담 중 → 종료 → [새로 상담하기] → 대기 (같은 방, 지난 대화가 이어진다)
export default function ConsultationPage() {
  const member = useAuthStore((state) => state.member);
  const [state, setState] = useState({ status: 'loading', room: null, error: '' });
  const [busy, setBusy] = useState(false);
  const [actionError, setActionError] = useState('');
  const [confirmingClose, setConfirmingClose] = useState(false); // [상담 종료] 확인 팝업

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

  // [상담 종료] → 확인 팝업(confirmingClose) → [종료하기] 를 누르면 여기
  async function handleClose() {
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
      {/* 지금 위치 — 개인정보 · 계정 관리(ProfilePage)와 같은 모양: 마이페이지 아래 화면 */}
      <nav className="consult-breadcrumb" aria-label="현재 위치">
        <Link to="/mypage">마이페이지</Link>
        <span aria-hidden="true">/</span>
        <span aria-current="page">1:1 상담</span>
      </nav>
      <header className="consult-heading">
        <h1>1:1 상담</h1>
        <p>재무 진단 결과나 차량 선택이 고민될 때 상담원이 답해 드려요. 상담원이 자리에 없어도 남긴 메시지는 저장됩니다.</p>
        {/* 상담원 보호 안내: 금칙어는 서버가 막고(ChatContentFilter), 반복되면 관리자가 상담을 제한한다 */}
        <p className="consult-policy">욕설 · 비하 · 성적인 표현은 보낼 수 없으며, 반복되면 상담이 일정 기간 제한될 수 있습니다.</p>
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
                : <button type="button" className="consult-outline" onClick={() => setConfirmingClose(true)} disabled={busy}>상담 종료</button>}
            </div>
            {/* 상담원이 맡았던 상담이 끝나면 한 번 — 남기면 서버가 닫고(feedbackOpen=false) 다시 읽는다 */}
            {room.status === 'CLOSED' && room.feedbackOpen && <FeedbackForm onDone={loadRoom} />}
            <ChatThread
              messages={chat.messages}
              viewer="member"
              connected={chat.connected}
              error={chat.error}
              canSend={room.status !== 'CLOSED'}
              disabledText={room.restricted
                ? `운영 정책 위반으로 ${restrictionLabel(room.restrictedUntil)} 중입니다. 새 상담을 시작할 수 없습니다.`
                : '종료된 상담입니다. 더 궁금한 점이 있으면 [새로 상담하기]를 눌러 주세요.'}
              onSend={chat.send}
            />
          </>
        )}
        {actionError && <p className="consult-error" role="alert">{actionError}</p>}
      </section>
      {confirmingClose && (
        <ChatConfirmModal
          title="상담 종료"
          message="상담을 종료할까요? 나중에 [새로 상담하기]로 다시 물어볼 수 있어요."
          confirmLabel="종료하기"
          onConfirm={handleClose}
          onClose={() => setConfirmingClose(false)}
        />
      )}
    </div>
  );
}

// 만족도 의견 · 신고 사유: 자주 있는 것을 고르고, 없으면 [기타] → 직접 쓰기
const COMMENTS = ['친절하고 빨랐어요', '궁금한 점이 해결됐어요', '설명이 이해하기 쉬웠어요', '답변이 늦었어요', '궁금한 점이 해결되지 않았어요', '설명이 어려웠어요', OTHER];
const REPORT_REASONS = ['불친절한 응대', '반말 · 욕설 등 부적절한 말', '성희롱', '잘못된 안내', '불필요한 개인정보 요구', OTHER];
const STARS = [1, 2, 3, 4, 5];

// 상담 만족도 + 상담원 신고 (신고는 총관리자만 본다)
function FeedbackForm({ onDone }) {
  const [rating, setRating] = useState(0);
  const [comment, setComment] = useState({ choice: '', other: '' });
  const [reported, setReported] = useState(false);
  const [reason, setReason] = useState({ choice: '', other: '' });
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');
  const reportReason = choiceText(reason.choice, reason.other);
  const ready = rating > 0 && (!reported || reportReason);

  async function handleSubmit(event) {
    event.preventDefault();
    if (!ready) return;
    setSaving(true);
    setError('');
    try {
      await submitFeedback({ rating, comment: choiceText(comment.choice, comment.other), reported, reportReason: reported ? reportReason : null });
      showToast(reported ? '평가와 신고를 접수했습니다. 감사합니다.' : '평가해 주셔서 감사합니다.');
      onDone();
    } catch (err) {
      setError(chatErrorMessage(err, '저장하지 못했습니다. 잠시 후 다시 시도해 주세요.'));
    } finally {
      setSaving(false);
    }
  }

  return (
    <form className="consult-feedback" onSubmit={handleSubmit}>
      <strong>상담은 어떠셨나요?</strong>
      <div className="consult-stars" role="radiogroup" aria-label="별점">
        {STARS.map((value) => (
          <button key={value} type="button" role="radio" aria-checked={rating === value} aria-label={`${value}점`}
            className={value <= rating ? 'is-on' : undefined} onClick={() => setRating(value)}>★</button>
        ))}
        {rating > 0 && <span>{rating}점</span>}
      </div>
      <ChoiceWithOther label="의견 (선택)" options={COMMENTS} required={false} choice={comment.choice} other={comment.other}
        onChoice={(choice) => setComment((prev) => ({ ...prev, choice }))} onOther={(other) => setComment((prev) => ({ ...prev, other }))} />
      <label className="consult-report-check">
        <input type="checkbox" checked={reported} onChange={(event) => setReported(event.target.checked)} />
        상담원의 응대를 신고합니다 (운영 관리자만 확인해요)
      </label>
      {reported && (
        <ChoiceWithOther label="신고 사유" options={REPORT_REASONS} choice={reason.choice} other={reason.other}
          onChoice={(choice) => setReason((prev) => ({ ...prev, choice }))} onOther={(other) => setReason((prev) => ({ ...prev, other }))} />
      )}
      {error && <p className="consult-error" role="alert">{error}</p>}
      <button type="submit" className="consult-button" disabled={saving || !ready}>{reported ? '평가 · 신고 보내기' : '평가 보내기'}</button>
    </form>
  );
}
