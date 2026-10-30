import { useCallback, useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import ChatThread from '../../features/chat/components/ChatThread';
import {
  assignRoom, chatErrorMessage, closeRoom, formatRestrictedUntil, getAdminRooms, getChatAdmins, restrictRoom,
  transferRoom, unrestrictRoom,
} from '../../features/chat/chatApi';
import { createStompClient } from '../../features/chat/stompClient';
import useChatRoom from '../../features/chat/useChatRoom';
import { ROLE_LABELS } from '../../features/auth/roles';
import useAuthStore from '../../stores/useAuthStore';
import { showToast } from '../../stores/useToastStore';
import './AdminChatPanel.css';

const FILTERS = [
  { value: 'WAITING', label: '대기' },
  { value: 'ACTIVE', label: '진행 중' },
  { value: 'CLOSED', label: '종료' },
  { value: '', label: '전체' },
];
const STATUS_LABELS = { WAITING: '대기', ACTIVE: '진행 중', CLOSED: '종료' };

// "2026-10-30T13:05:12" → "10.30 13:05"
const shortTime = (value) => (value ? `${value.slice(5, 10).replace('-', '.')} ${value.slice(11, 16)}` : '');

// 8단계: 관리자 대시보드 [1:1 상담] 탭 — 왼쪽 상담 목록, 오른쪽 대화
// 목록은 /topic/admin/chat 알림(새 상담 · 맡기 · 넘기기 · 종료 · 새 메시지)을 받으면 다시 불러온다 → 새로고침 없이 대기 목록이 바뀐다
// 관리자 · 총관리자 모두 [맡기] 가능(먼저 누른 사람이 담당), 답장은 담당자만, 넘기기 · 종료는 담당자 또는 총관리자
export default function AdminChatPanel() {
  const me = useAuthStore((state) => state.member);
  const isSuper = me?.role === 'SUPER_ADMIN';
  const [filter, setFilter] = useState('WAITING');
  const [list, setList] = useState({ status: 'loading', rooms: [], error: '' });
  const [selectedId, setSelectedId] = useState(null);
  const [version, setVersion] = useState(0); // 알림이 오면 +1 → 목록 다시 불러오기

  useEffect(() => {
    const controller = new AbortController();
    getAdminRooms(filter, controller.signal)
      .then((rooms) => setList({ status: 'done', rooms, error: '' }))
      .catch((error) => {
        if (!controller.signal.aborted) setList({ status: 'error', rooms: [], error: chatErrorMessage(error, '상담 목록을 불러오지 못했습니다.') });
      });
    return () => controller.abort();
  }, [filter, version]);

  // 실시간 목록 알림 구독 (관리자만 — 서버 StompAuthInterceptor 가 확인)
  useEffect(() => {
    const client = createStompClient();
    client.onConnect = () => client.subscribe('/topic/admin/chat', () => setVersion((v) => v + 1));
    client.activate();
    return () => client.deactivate();
  }, []);

  const reload = useCallback(() => setVersion((v) => v + 1), []);

  // 선택한 상담은 지금 필터 목록에 없을 수 있어서(예: 맡으면 대기 → 진행 중) 전체 목록에서 다시 찾는다
  const [selected, setSelected] = useState(null);
  useEffect(() => {
    if (!selectedId) return;
    getAdminRooms('').then((rooms) => setSelected(rooms.find((room) => room.id === selectedId) ?? null)).catch(() => {});
  }, [selectedId, version]);

  return (
    <div className="admin-chat">
      <section className="admin-card admin-chat-list" aria-label="상담 목록">
        <div className="admin-chat-filters" role="tablist">
          {FILTERS.map(({ value, label }) => (
            <button key={label} type="button" role="tab" aria-selected={filter === value}
              className={filter === value ? 'is-active' : undefined} onClick={() => setFilter(value)}>{label}</button>
          ))}
        </div>
        {list.status === 'loading' && <p className="admin-chat-note">불러오는 중…</p>}
        {list.status === 'error' && <p className="admin-chat-note is-error">{list.error}</p>}
        {list.status === 'done' && list.rooms.length === 0 && <p className="admin-chat-note">상담이 없습니다.</p>}
        <ul>
          {list.rooms.map((room) => (
            <li key={room.id}>
              <button type="button" className={selectedId === room.id ? 'is-selected' : undefined} onClick={() => setSelectedId(room.id)}>
                <span className="admin-chat-row">
                  <strong>{room.userNickName}</strong>
                  <span className="admin-chat-badges">
                    {room.restricted && <span className="admin-chat-badge is-restricted">제한</span>}
                    <span className={`admin-chat-badge is-${room.status.toLowerCase()}`}>{STATUS_LABELS[room.status]}</span>
                  </span>
                </span>
                <span className="admin-chat-preview">{room.lastMessage ?? '메시지 없음'}</span>
                <span className="admin-chat-meta">
                  {room.assignedAdminNickName ? `담당 ${room.assignedAdminId === me?.id ? '나' : room.assignedAdminNickName}` : '담당 없음'}
                  {' · '}{shortTime(room.lastMessageAt ?? room.createdAt)}
                </span>
              </button>
            </li>
          ))}
        </ul>
      </section>

      <section className="admin-card admin-chat-detail" aria-label="상담 대화">
        {selected
          ? <RoomDetail key={selected.id} room={selected} meId={me?.id} isSuper={isSuper} onChanged={reload} />
          : <p className="admin-chat-note">왼쪽 목록에서 상담을 고르세요.</p>}
      </section>
    </div>
  );
}

// 오른쪽: 선택한 상담 — 회원 정보 · [맡기] · [넘기기] · [상담 종료] + 대화
function RoomDetail({ room, meId, isSuper, onChanged }) {
  const navigate = useNavigate();
  const chat = useChatRoom(room.id, onChanged);
  const [busy, setBusy] = useState(false);
  const [openForm, setOpenForm] = useState(''); // 'transfer' · 'restrict' · '' (한 번에 하나만 펼친다)
  const mine = room.assignedAdminId === meId;
  const canManage = mine || isSuper; // 넘기기 · 종료 · 상담 제한
  const toggleForm = (name) => setOpenForm((open) => (open === name ? '' : name));

  async function run(action, done) {
    setBusy(true);
    try {
      await action();
      showToast(done);
      onChanged();
    } catch (error) {
      showToast(chatErrorMessage(error, '처리하지 못했습니다. 목록을 새로고침해 주세요.'));
      onChanged();
    } finally {
      setBusy(false);
    }
  }

  const disabledText = room.status === 'CLOSED'
    ? '종료된 상담입니다. 회원이 [새로 상담하기]를 누르면 다시 대기로 돌아옵니다.'
    : room.status === 'WAITING'
      ? '[맡기]를 누르면 답장할 수 있습니다.'
      : `${room.assignedAdminNickName ?? '다른 상담원'}님이 맡은 상담입니다. 보기만 할 수 있어요.`;

  return (
    <>
      <div className="admin-chat-head">
        <div>
          <h3>{room.userNickName}</h3>
          <p>
            {STATUS_LABELS[room.status]} · 담당 {room.assignedAdminNickName ? (mine ? '나' : room.assignedAdminNickName) : '없음'}
            {room.restricted && ` · ${formatRestrictedUntil(room.restrictedUntil)}까지 상담 제한`}
          </p>
        </div>
        <div className="admin-chat-actions">
          {/* 회원 관리 탭에서 이 회원 찾기 (주소에 개인정보를 싣지 않고 화면 이동 상태로 넘긴다) */}
          <button type="button" className="admin-outline-button"
            onClick={() => navigate('/console?tab=members', { state: { memberKeyword: room.userNickName } })}>회원 정보</button>
          {room.status === 'WAITING' && (
            <button type="button" className="admin-primary-button" disabled={busy}
              onClick={() => run(() => assignRoom(room.id), '상담을 맡았습니다.')}>맡기</button>
          )}
          {room.status === 'ACTIVE' && canManage && (
            <button type="button" className="admin-outline-button" disabled={busy} onClick={() => toggleForm('transfer')}>넘기기</button>
          )}
          {room.status !== 'CLOSED' && (room.status === 'ACTIVE' ? canManage : isSuper) && (
            <button type="button" className="admin-outline-button" disabled={busy}
              onClick={() => window.confirm('이 상담을 종료할까요?') && run(() => closeRoom(room.id), '상담을 종료했습니다.')}>상담 종료</button>
          )}
          {/* 욕설 · 성희롱 등: 상담을 끝내고 며칠간 새 상담을 막는다 (잘못 눌렀으면 [제한 풀기]) */}
          {canManage && !room.restricted && (
            <button type="button" className="admin-outline-button admin-chat-danger" disabled={busy} onClick={() => toggleForm('restrict')}>상담 제한</button>
          )}
          {canManage && room.restricted && (
            <button type="button" className="admin-outline-button" disabled={busy}
              onClick={() => window.confirm('상담 제한을 풀까요?') && run(() => unrestrictRoom(room.id), '상담 제한을 풀었습니다.')}>제한 풀기</button>
          )}
        </div>
      </div>

      {openForm === 'transfer' && (
        <TransferForm
          room={room}
          busy={busy}
          onCancel={() => setOpenForm('')}
          onSubmit={(adminId, reason) => run(() => transferRoom(room.id, adminId, reason), '상담을 넘겼습니다.').then(() => setOpenForm(''))}
        />
      )}
      {openForm === 'restrict' && (
        <RestrictForm
          busy={busy}
          onCancel={() => setOpenForm('')}
          onSubmit={(days, reason) => run(() => restrictRoom(room.id, days, reason), `${days}일 동안 상담을 제한했습니다.`).then(() => setOpenForm(''))}
        />
      )}

      <ChatThread
        messages={chat.messages}
        viewer="admin"
        memberName={room.userNickName}
        connected={chat.connected}
        error={chat.error}
        canSend={room.status === 'ACTIVE' && mine}
        disabledText={disabledText}
        onSend={chat.send}
      />
    </>
  );
}

// 상담 제한: 기간 + 이유(선택, 운영 로그에만 남는다). 진행 중이면 종료되고, 회원은 기간이 끝날 때까지 새 상담을 못 한다
const RESTRICT_DAYS = [1, 3, 7, 30];

function RestrictForm({ busy, onCancel, onSubmit }) {
  const [days, setDays] = useState(3);
  const [reason, setReason] = useState('');

  function handleSubmit(event) {
    event.preventDefault();
    if (window.confirm(`${days}일 동안 이 회원의 상담을 제한할까요? 진행 중인 상담은 종료됩니다.`)) onSubmit(days, reason.trim());
  }

  return (
    <form className="admin-chat-transfer" onSubmit={handleSubmit}>
      <label>
        제한 기간
        <select value={days} onChange={(event) => setDays(Number(event.target.value))}>
          {RESTRICT_DAYS.map((value) => <option key={value} value={value}>{value}일</option>)}
        </select>
      </label>
      <label>
        이유 (선택 · 운영 로그에만 남아요)
        <input value={reason} onChange={(event) => setReason(event.target.value)} maxLength={100} placeholder="예: 욕설 반복" />
      </label>
      <div className="admin-chat-transfer-actions">
        <button type="button" className="admin-outline-button" onClick={onCancel}>취소</button>
        <button type="submit" className="admin-outline-button admin-chat-danger" disabled={busy}>제한하기</button>
      </div>
    </form>
  );
}

// 넘기기: 받을 관리자 + 이유(선택, 운영 로그에만 남는다). 받는 사람의 수락 없이 바로 넘어간다
function TransferForm({ room, busy, onCancel, onSubmit }) {
  const [admins, setAdmins] = useState([]);
  const [adminId, setAdminId] = useState('');
  const [reason, setReason] = useState('');

  useEffect(() => {
    getChatAdmins()
      .then((list) => setAdmins(list.filter((admin) => admin.id !== room.assignedAdminId)))
      .catch(() => setAdmins([]));
  }, [room.assignedAdminId]);

  function handleSubmit(event) {
    event.preventDefault();
    if (adminId) onSubmit(Number(adminId), reason.trim());
  }

  return (
    <form className="admin-chat-transfer" onSubmit={handleSubmit}>
      <label>
        넘겨받을 관리자
        <select value={adminId} onChange={(event) => setAdminId(event.target.value)} required>
          <option value="">선택하세요</option>
          {admins.map((admin) => (
            <option key={admin.id} value={admin.id}>{admin.nickName} ({ROLE_LABELS[admin.role] ?? admin.role})</option>
          ))}
        </select>
      </label>
      <label>
        이유 (선택 · 운영 로그에만 남아요)
        <input value={reason} onChange={(event) => setReason(event.target.value)} maxLength={100} placeholder="예: 휴가" />
      </label>
      <div className="admin-chat-transfer-actions">
        <button type="button" className="admin-outline-button" onClick={onCancel}>취소</button>
        <button type="submit" className="admin-primary-button" disabled={busy || !adminId}>넘기기</button>
      </div>
    </form>
  );
}
