import { useCallback, useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { ChevronDown } from 'lucide-react';
import ChatConfirmModal from '../../features/chat/components/ChatConfirmModal';
import ChatThread from '../../features/chat/components/ChatThread';
import ChoiceWithOther from '../../features/chat/components/ChoiceWithOther';
import { choiceText, OTHER } from '../../features/chat/choice';
import {
  assignRoom, chatErrorMessage, closeRoom, getAdminRooms, getAllFeedback, getChatAdmins, getFeedbackSummary, getRoomFeedback,
  restrictionLabel, restrictRoom, transferRoom, unrestrictRoom, warnRoom,
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
      {/* 상담원별 만족도 · 신고 — 총관리자만 (신고당한 상담원 본인이 보지 않게) */}
      {isSuper && <FeedbackSummary version={version} />}
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
                    {room.reportCount > 0 && <span className="admin-chat-badge is-restricted">신고 {room.reportCount}</span>}
                    {room.warningCount > 0 && <span className="admin-chat-badge is-warned">경고 {room.warningCount}</span>}
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

// 오른쪽: 선택한 상담 — 회원 정보 · [맡기] · [넘기기] · [상담 종료] · [경고] · [상담 제한] + 대화
function RoomDetail({ room, meId, isSuper, onChanged }) {
  const navigate = useNavigate();
  const chat = useChatRoom(room.id, onChanged);
  const [busy, setBusy] = useState(false);
  const [openForm, setOpenForm] = useState(''); // 'transfer' · 'warn' · 'restrict' · '' (한 번에 하나만 펼친다)
  const mine = room.assignedAdminId === meId;
  const canManage = mine || isSuper; // 넘기기 · 종료 · 상담 제한
  const toggleForm = (name) => setOpenForm((open) => (open === name ? '' : name));
  // 확인 팝업 (상담 종료 · 제한 · 제한 풀기) — { title, message, confirmLabel, danger, onConfirm } 또는 null
  const [confirm, setConfirm] = useState(null);

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
            {room.warningCount > 0 && ` · 경고 ${room.warningCount}회`}
            {room.restricted && ` · ${restrictionLabel(room.restrictedUntil)}`}
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
              onClick={() => setConfirm({
                title: '상담 종료',
                message: `${room.userNickName}님과의 상담을 종료할까요?`,
                confirmLabel: '종료하기',
                onConfirm: () => run(() => closeRoom(room.id), '상담을 종료했습니다.'),
              })}>상담 종료</button>
          )}
          {/* 경고 → 그래도 반복되면 상담 제한 */}
          {room.status === 'ACTIVE' && canManage && (
            <button type="button" className="admin-outline-button admin-chat-danger" disabled={busy} onClick={() => toggleForm('warn')}>경고</button>
          )}
          {/* 욕설 · 성희롱 등: 상담을 끝내고 며칠간 새 상담을 막는다 (잘못 눌렀으면 [제한 풀기]) */}
          {canManage && !room.restricted && (
            <button type="button" className="admin-outline-button admin-chat-danger" disabled={busy} onClick={() => toggleForm('restrict')}>상담 제한</button>
          )}
          {/* 제한 풀기는 총관리자만 (채팅 기록을 보고 판단) */}
          {isSuper && room.restricted && (
            <button type="button" className="admin-outline-button" disabled={busy}
              onClick={() => setConfirm({
                title: '상담 제한 풀기',
                message: `${room.userNickName}님의 상담 제한을 풀까요? 바로 새 상담을 시작할 수 있게 됩니다.`,
                confirmLabel: '제한 풀기',
                onConfirm: () => run(() => unrestrictRoom(room.id), '상담 제한을 풀었습니다.'),
              })}>제한 풀기</button>
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
      {openForm === 'warn' && (
        <WarnForm
          busy={busy}
          count={room.warningCount}
          onCancel={() => setOpenForm('')}
          onSubmit={(reason) => run(() => warnRoom(room.id, reason), '경고를 보냈습니다.').then(() => setOpenForm(''))}
        />
      )}
      {openForm === 'restrict' && (
        <RestrictForm
          busy={busy}
          isSuper={isSuper}
          onCancel={() => setOpenForm('')}
          onSubmit={(days, reason) => setConfirm({
            title: '상담 제한',
            message: `${days === 0 ? '영구적으로' : `${days}일 동안`} ${room.userNickName}님의 상담을 제한할까요? 진행 중인 상담은 종료됩니다.`,
            confirmLabel: '제한하기',
            danger: true,
            onConfirm: () => run(() => restrictRoom(room.id, days, reason), days === 0 ? '상담을 영구 제한했습니다.' : `${days}일 동안 상담을 제한했습니다.`)
              .then(() => setOpenForm('')),
          })}
        />
      )}
      {confirm && <ChatConfirmModal {...confirm} onClose={() => setConfirm(null)} />}

      <ChatThread
        messages={chat.messages}
        viewer="admin"
        memberName={room.userNickName}
        connected={chat.connected}
        error={chat.error}
        canSend={room.status === 'ACTIVE' && mine}
        disabledText={disabledText}
        onSend={chat.send}
        quickReplies
      />
      {isSuper && <RoomFeedback roomId={room.id} reportCount={room.reportCount} />}
    </>
  );
}

const stars = (rating) => '★'.repeat(rating) + '☆'.repeat(5 - rating);
const shortDate = (value) => (value ? value.slice(0, 10).replaceAll('-', '.') : '');

const FEEDBACK_SORTS = [
  { value: 'latest', label: '최신순' },
  { value: 'low', label: '평점 낮은순' },
  { value: 'high', label: '평점 높은순' },
];

// 평가 1건 한 줄 (전체 목록 · 회원별 목록이 같이 쓴다)
function FeedbackItem({ item, showMember }) {
  return (
    <li>
      <span className="admin-chat-stars" aria-label={`${item.rating}점`}>{stars(item.rating)}</span>
      {' '}{item.comment ?? '의견 없음'}
      <span className="admin-chat-feedback-meta">
        {showMember && `${item.memberNickName} → `}상담원 {item.adminNickName ?? '(탈퇴)'} · {shortDate(item.createdAt)}
      </span>
      {item.reported && <span className="admin-chat-report">신고: {item.reportReason}</span>}
    </li>
  );
}

// 상담원 만족도 · 신고 (총관리자) — 평소엔 접어 두고 한 줄 요약만. 펼치면 상담원별 표 + 전체 평가(정렬 · 신고만 · 스크롤)
function FeedbackSummary({ version }) {
  const [open, setOpen] = useState(false);
  const [rows, setRows] = useState(null);
  const [sort, setSort] = useState('latest');
  const [reportedOnly, setReportedOnly] = useState(false);
  const [items, setItems] = useState(null);

  useEffect(() => {
    getFeedbackSummary().then(setRows).catch(() => setRows([]));
  }, [version]);

  // 펼쳤을 때만 전체 평가를 읽는다 (정렬 · 신고만 을 바꾸면 다시)
  useEffect(() => {
    if (!open) return;
    getAllFeedback(sort, reportedOnly).then(setItems).catch(() => setItems([]));
  }, [open, sort, reportedOnly, version]);

  const total = rows?.reduce((sum, row) => sum + row.count, 0) ?? 0;
  const reports = rows?.reduce((sum, row) => sum + row.reportCount, 0) ?? 0;

  return (
    <section className="admin-card admin-chat-summary" aria-label="상담원 만족도">
      <button type="button" className="admin-chat-summary-toggle" aria-expanded={open} onClick={() => setOpen((v) => !v)}>
        <span>
          <strong>상담원 만족도 · 신고</strong>
          <small>평가 {total}건 · 신고 <b className={reports > 0 ? 'is-reported' : undefined}>{reports}건</b> · 총관리자만</small>
        </span>
        <ChevronDown size={18} aria-hidden="true" className={open ? 'is-open' : undefined} />
      </button>

      {open && (
        <div className="admin-chat-summary-body">
          {total === 0 ? <p className="admin-chat-note">아직 받은 평가가 없습니다.</p> : (
            <>
              <table>
                <thead><tr><th>상담원</th><th>평가 수</th><th>평균 별점</th><th>신고</th></tr></thead>
                <tbody>
                  {rows.map((row) => (
                    <tr key={row.adminId ?? 'none'}>
                      <td>{row.nickName}</td>
                      <td>{row.count}</td>
                      <td>★ {row.averageRating}</td>
                      <td className={row.reportCount > 0 ? 'is-reported' : undefined}>{row.reportCount}</td>
                    </tr>
                  ))}
                </tbody>
              </table>

              <div className="admin-chat-feedback-tools">
                <strong>전체 평가</strong>
                <select value={sort} onChange={(event) => setSort(event.target.value)} aria-label="정렬">
                  {FEEDBACK_SORTS.map((option) => <option key={option.value} value={option.value}>{option.label}</option>)}
                </select>
                <label>
                  <input type="checkbox" checked={reportedOnly} onChange={(event) => setReportedOnly(event.target.checked)} />
                  신고만
                </label>
              </div>
              {items === null && <p className="admin-chat-note">불러오는 중…</p>}
              {items?.length === 0 && <p className="admin-chat-note">조건에 맞는 평가가 없습니다.</p>}
              {items?.length > 0 && (
                <ul className="admin-chat-feedback-list">
                  {items.map((item) => <FeedbackItem key={item.id} item={item} showMember />)}
                </ul>
              )}
            </>
          )}
        </div>
      )}
    </section>
  );
}

// 이 회원이 남긴 만족도 · 신고 (총관리자) — 접어 두고 "n건" 만. 신고 수가 바뀌면 다시 읽는다
function RoomFeedback({ roomId, reportCount }) {
  const [list, setList] = useState([]);
  useEffect(() => {
    getRoomFeedback(roomId).then(setList).catch(() => setList([]));
  }, [roomId, reportCount]);

  if (list.length === 0) return null;
  return (
    <details className="admin-chat-feedback">
      <summary>이 회원이 남긴 평가 {list.length}건{reportCount > 0 && ` · 신고 ${reportCount}건`} (총관리자만)</summary>
      <ul className="admin-chat-feedback-list">
        {list.map((item) => <FeedbackItem key={item.id} item={item} />)}
      </ul>
    </details>
  );
}

// 경고: 사유를 골라 보내면 회원에게 "운영 정책 위반 경고 n회: 사유" 가 안내된다 (제한 전 단계)
function WarnForm({ busy, count, onCancel, onSubmit }) {
  const [choice, setChoice] = useState('');
  const [other, setOther] = useState('');
  const reason = reasonText(choice, other);

  function handleSubmit(event) {
    event.preventDefault();
    if (reason) onSubmit(reason);
  }

  return (
    <form className="admin-chat-transfer" onSubmit={handleSubmit}>
      <p className="admin-chat-form-note">
        회원에게 <strong>경고 {count + 1}회</strong>와 사유가 안내됩니다. 계속 반복되면 [상담 제한]을 쓰세요.
      </p>
      <ReasonField label="경고 사유" note="회원에게도 보여요" options={RESTRICT_REASONS} choice={choice} other={other} onChoice={setChoice} onOther={setOther} />
      <div className="admin-chat-transfer-actions">
        <button type="button" className="admin-outline-button" onClick={onCancel}>취소</button>
        <button type="submit" className="admin-outline-button admin-chat-danger" disabled={busy || !reason}>경고 보내기</button>
      </div>
    </form>
  );
}

// 사유: 자주 있는 것을 고르고, 없으면 [기타] → 직접 쓰기 (제한 · 넘기기는 운영 로그에만, 경고는 회원에게도)
const RESTRICT_REASONS = ['욕설 · 비속어', '부모 · 가족 비하', '성희롱 · 음란', '상담원 인격 모독 · 협박', '같은 말 반복 · 도배', '상담과 무관한 내용 반복', OTHER];
const TRANSFER_REASONS = ['휴가', '퇴근 · 교대', '퇴사 · 업무 변경', '상담이 몰림', '다른 상담원이 더 잘 아는 내용', OTHER];
const reasonText = choiceText;

function ReasonField({ label, note = '운영 로그에만 남아요', ...props }) {
  return <ChoiceWithOther label={`${label} (${note})`} otherLabel="기타 사유" maxLength={100} {...props} />;
}

// 상담 제한: 기간 + 사유. 진행 중이면 종료되고, 회원은 기간이 끝날 때까지 새 상담을 못 한다
// 영구(0)는 총관리자만 — 서버도 한 번 더 확인한다
const RESTRICT_DAYS = [
  { value: 1, label: '1일' }, { value: 3, label: '3일' }, { value: 7, label: '7일' }, { value: 30, label: '30일' },
  { value: 0, label: '영구 (총관리자)', superOnly: true },
];

function RestrictForm({ busy, isSuper, onCancel, onSubmit }) {
  const [days, setDays] = useState(3);
  const [choice, setChoice] = useState('');
  const [other, setOther] = useState('');
  const reason = reasonText(choice, other);

  function handleSubmit(event) {
    event.preventDefault();
    if (reason) onSubmit(days, reason); // 확인 팝업은 RoomDetail 이 띄운다
  }

  return (
    <form className="admin-chat-transfer" onSubmit={handleSubmit}>
      <label>
        제한 기간
        <select value={days} onChange={(event) => setDays(Number(event.target.value))}>
          {RESTRICT_DAYS.filter((option) => isSuper || !option.superOnly)
            .map((option) => <option key={option.value} value={option.value}>{option.label}</option>)}
        </select>
      </label>
      <ReasonField label="제한 사유" options={RESTRICT_REASONS} choice={choice} other={other} onChoice={setChoice} onOther={setOther} />
      <div className="admin-chat-transfer-actions">
        <button type="button" className="admin-outline-button" onClick={onCancel}>취소</button>
        <button type="submit" className="admin-outline-button admin-chat-danger" disabled={busy || !reason}>제한하기</button>
      </div>
    </form>
  );
}

// 넘기기: 받을 관리자 + 사유(운영 로그에만 남는다). 받는 사람의 수락 없이 바로 넘어간다
function TransferForm({ room, busy, onCancel, onSubmit }) {
  const [admins, setAdmins] = useState([]);
  const [adminId, setAdminId] = useState('');
  const [choice, setChoice] = useState('');
  const [other, setOther] = useState('');
  const reason = reasonText(choice, other);

  useEffect(() => {
    getChatAdmins()
      .then((list) => setAdmins(list.filter((admin) => admin.id !== room.assignedAdminId)))
      .catch(() => setAdmins([]));
  }, [room.assignedAdminId]);

  function handleSubmit(event) {
    event.preventDefault();
    if (adminId && reason) onSubmit(Number(adminId), reason);
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
      <ReasonField label="넘기는 사유" options={TRANSFER_REASONS} choice={choice} other={other} onChoice={setChoice} onOther={setOther} />
      <div className="admin-chat-transfer-actions">
        <button type="button" className="admin-outline-button" onClick={onCancel}>취소</button>
        <button type="submit" className="admin-primary-button" disabled={busy || !adminId || !reason}>넘기기</button>
      </div>
    </form>
  );
}
