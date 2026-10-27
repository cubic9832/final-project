// 7단계: 관리자 대시보드 — 회원 관리 탭 (실제 데이터)
// 위: 회원 현황 (전체 · 최근 7일 가입 · 구글 · 관리자, 7일 가입 추이, 나이대 · 성별)
// 아래: 회원 목록 (검색 · 권한 · 페이지) + 상세. 이메일은 서버가 가려서 보낸다.
// 총관리자(SUPER_ADMIN)만 상세에서 관리자 권한을 주고 뺄 수 있다. 잠금 해제는 아직 없음
import { Fragment, useEffect, useState } from 'react';
import { Search, ShieldCheck, X } from 'lucide-react';
import theme from '../../styles/theme';
import { changeMemberRole, getAdminMembers, getMemberSummary, unlockMemberLogin } from '../../features/admin/adminApi';
import { ROLE_LABELS } from '../../features/auth/roles';
import useAuthStore from '../../stores/useAuthStore';
import { showToast } from '../../stores/useToastStore';
import './AdminMembersPanel.css';

const PAGE_SIZE = 10;
const GENDER_LABELS = { MALE: '남성', FEMALE: '여성', NONE: '선택 안 함', 미입력: '미입력' };
const LOGIN_METHODS = { EMAIL: '이메일', GOOGLE: '구글', BOTH: '이메일 · 구글' };

// "2026-10-26T14:22:05" → "2026.10.26"
const formatDate = (value) => (value ? value.slice(0, 10).replaceAll('-', '.') : '-');
// "2026-10-26T14:22:05" → "10.26 14:22"
const formatDateTime = (value) => (value ? `${value.slice(5, 10).replace('-', '.')} ${value.slice(11, 16)}` : '-');

// 서버 오류 문구 (403 이면 관리자 권한이 없다는 뜻)
const errorMessage = (error, fallback) => error.response?.data?.error?.message ?? fallback;

export default function AdminMembersPanel() {
  // 권한을 바꾸면 현황(관리자 수)과 목록을 함께 다시 불러오도록 version 을 올린다
  const [version, setVersion] = useState(0);
  const refresh = () => setVersion((value) => value + 1);
  return (
    <div className="admin-panel-stack">
      <MemberSummary version={version} />
      <MemberList version={version} onChanged={refresh} />
    </div>
  );
}

// ① 회원 현황 — 화면이 열릴 때 한 번 불러온다 ([다시 시도] 로 다시)
function MemberSummary({ version }) {
  const [state, setState] = useState({ status: 'loading', data: null, error: '' });
  const [reloadKey, setReloadKey] = useState(0);

  useEffect(() => {
    const controller = new AbortController();
    getMemberSummary(controller.signal)
      .then((data) => setState({ status: 'done', data, error: '' }))
      .catch((error) => {
        if (!controller.signal.aborted) {
          setState({ status: 'error', data: null, error: errorMessage(error, '회원 현황을 불러오지 못했습니다.') });
        }
      });
    return () => controller.abort(); // 화면을 떠나면 응답을 버린다
  }, [reloadKey, version]);

  function retry() {
    setState({ status: 'loading', data: null, error: '' });
    setReloadKey((key) => key + 1);
  }

  if (state.status === 'loading') {
    return <section className="admin-card"><p className="admin-empty" role="status">회원 현황을 불러오는 중…</p></section>;
  }
  if (state.status === 'error') {
    return (
      <section className="admin-card">
        <p className="admin-empty" role="alert">
          {state.error} <button type="button" className="admin-text-button" onClick={retry}>다시 시도</button>
        </p>
      </section>
    );
  }

  const summary = state.data;
  const maxDaily = Math.max(1, ...summary.daily.map((day) => day.count)); // 막대 높이 기준 (0명만 있어도 나누기 0 방지)
  return (
    <>
      <section className="admin-summary" aria-label="회원 현황 요약">
        <div className="admin-stat"><span>전체 회원</span><strong>{summary.total}명</strong><small>관리자 {summary.admins}명 포함</small></div>
        <div className="admin-stat"><span>최근 7일 가입</span><strong>{summary.newLast7Days}명</strong><small>오늘 포함 7일</small></div>
        <div className="admin-stat"><span>구글 로그인</span><strong>{summary.google}명</strong><small>구글 전용 + 연결</small></div>
        <div className="admin-stat"><span>관리자</span><strong>{summary.admins}명</strong><small>총관리자 포함 · 총관리자가 지정</small></div>
      </section>

      <div className="admin-grid-2">
        <section className="admin-card">
          <div className="admin-card-heading"><div><h3>가입 추이</h3><p>최근 7일 날짜별 가입 수</p></div></div>
          <ol className="admin-member-trend" aria-label="최근 7일 날짜별 가입 수">
            {summary.daily.map((day) => (
              <li key={day.date}>
                <span className="admin-member-trend-count">{day.count}</span>
                <span className="admin-member-trend-bar" style={{ height: `${(day.count / maxDaily) * 100}%` }} />
                <span className="admin-member-trend-date">{day.date.slice(5).replace('-', '.')}</span>
              </li>
            ))}
          </ol>
        </section>

        <section className="admin-card">
          <div className="admin-card-heading"><div><h3>나이대 · 성별</h3><p>개인정보를 입력한 회원 기준 (없으면 미입력)</p></div></div>
          <GroupBars title="나이대" groups={summary.ageBands} total={summary.total} />
          <GroupBars
            title="성별"
            groups={summary.genders.map((group) => ({ ...group, label: GENDER_LABELS[group.label] ?? group.label }))}
            total={summary.total}
          />
        </section>
      </div>
    </>
  );
}

// 묶음별 가로 막대 (전체 회원 중 비율)
function GroupBars({ title, groups, total }) {
  return (
    <div className="admin-member-groups">
      <h4>{title}</h4>
      <ul>
        {groups.map((group) => (
          <li key={group.label}>
            <span>{group.label}</span>
            <span className="admin-member-group-track">
              <span style={{ width: `${total ? (group.count / total) * 100 : 0}%` }} />
            </span>
            <strong>{group.count}명</strong>
          </li>
        ))}
      </ul>
    </div>
  );
}

// ② 회원 목록 — 검색어는 [검색] 을 눌렀을 때, 권한 · 페이지는 바꾸는 즉시 다시 불러온다
function MemberList({ version, onChanged }) {
  const [draft, setDraft] = useState(''); // 입력 중인 검색어
  const [query, setQuery] = useState({ keyword: '', role: '', page: 1 }); // 실제로 요청한 조건
  const [state, setState] = useState({ status: 'loading', members: [], meta: null, error: '' });
  const [selectedId, setSelectedId] = useState(null);
  const [reloadKey, setReloadKey] = useState(0);

  useEffect(() => {
    const controller = new AbortController();
    getAdminMembers({ ...query, size: PAGE_SIZE }, controller.signal)
      .then(({ members, meta }) => setState({ status: 'done', members, meta, error: '' }))
      .catch((error) => {
        if (!controller.signal.aborted) {
          setState({ status: 'error', members: [], meta: null, error: errorMessage(error, '회원 목록을 불러오지 못했습니다.') });
        }
      });
    return () => controller.abort();
  }, [query, reloadKey, version]);

  // 조건이 바뀌면 불러오는 중으로 바꾸고 상세는 닫는다
  function changeQuery(next) {
    setState((prev) => ({ ...prev, status: 'loading' }));
    setSelectedId(null);
    setQuery((prev) => ({ ...prev, ...next }));
  }

  function handleSearch(event) {
    event.preventDefault();
    changeQuery({ keyword: draft.trim(), page: 1 });
  }

  function retry() {
    setState((prev) => ({ ...prev, status: 'loading' }));
    setReloadKey((key) => key + 1);
  }

  const { members, meta } = state;
  const totalPages = meta?.totalPages ?? 1;

  return (
    <>
      <section className="admin-card">
        <div className="admin-card-heading">
          <div><h3>회원 목록</h3><p>최근 가입 순. 이메일은 일부를 가려서 보여 줍니다.</p></div>
          {meta && <span className="admin-count-badge">{meta.total}명</span>}
        </div>

        <form className="admin-filters" onSubmit={handleSearch}>
          <label className="admin-search-field">
            <Search size={theme.iconSize.sm} aria-hidden="true" />
            <input
              type="search"
              aria-label="닉네임 또는 이메일 검색"
              placeholder="닉네임 또는 이메일 검색"
              value={draft}
              onChange={(event) => setDraft(event.target.value)}
            />
          </label>
          <button type="submit" className="admin-outline-button">검색</button>
          <label className="admin-filter-field">
            권한
            <select value={query.role} onChange={(event) => changeQuery({ role: event.target.value, page: 1 })}>
              <option value="">전체</option>
              <option value="USER">일반 회원</option>
              <option value="ADMIN">관리자</option>
            </select>
          </label>
        </form>

        {state.status === 'loading' && <p className="admin-empty" role="status">회원 목록을 불러오는 중…</p>}
        {state.status === 'error' && (
          <p className="admin-empty" role="alert">
            {state.error} <button type="button" className="admin-text-button" onClick={retry}>다시 시도</button>
          </p>
        )}
        {state.status === 'done' && members.length === 0 && (
          <p className="admin-empty" role="status">조건에 맞는 회원이 없습니다. 검색어나 권한을 바꿔 주세요.</p>
        )}
        {state.status === 'done' && members.length > 0 && (
          <div className="admin-table-wrap">
            <table className="admin-table">
              <caption className="admin-sr-only">회원 목록</caption>
              <thead>
                <tr>
                  <th scope="col">회원</th>
                  <th scope="col">가입일</th>
                  <th scope="col">로그인 방법</th>
                  <th scope="col">권한</th>
                  <th scope="col">상태</th>
                  <th scope="col">작업</th>
                </tr>
              </thead>
              <tbody>
                {/* 상세는 누른 회원 바로 아래 줄에 펼친다 (예전: 목록 맨 아래라 화면 밖에 열려 안 눌린 것처럼 보였다) */}
                {members.map((member) => (
                  <Fragment key={member.id}>
                  <tr className={selectedId === member.id ? 'is-selected' : undefined}>
                    <td><strong>{member.nickName}</strong><small>{member.emailMasked}</small></td>
                    <td>{formatDate(member.joinedAt)}</td>
                    <td>{LOGIN_METHODS[member.loginMethod]}</td>
                    <td>{ROLE_LABELS[member.role] ?? member.role}</td>
                    <td>
                      <span className={`admin-status ${member.lockedMinutes > 0 ? 'is-check' : 'is-ok'}`}>
                        {member.lockedMinutes > 0 ? `로그인 잠금 ${member.lockedMinutes}분` : '정상'}
                      </span>
                    </td>
                    <td>
                      <button
                        type="button"
                        className="admin-text-button"
                        aria-expanded={selectedId === member.id}
                        onClick={() => setSelectedId(selectedId === member.id ? null : member.id)}
                      >
                        {selectedId === member.id ? '닫기' : '상세 보기'}
                      </button>
                    </td>
                  </tr>
                  {selectedId === member.id && (
                    <tr className="admin-member-detail-row">
                      <td colSpan={6}>
                        <MemberDetail member={member} onClose={() => setSelectedId(null)} onChanged={onChanged} />
                      </td>
                    </tr>
                  )}
                  </Fragment>
                ))}
              </tbody>
            </table>
          </div>
        )}

        {totalPages > 1 && (
          <nav className="admin-member-pagination" aria-label="회원 목록 페이지">
            <button type="button" disabled={query.page <= 1} onClick={() => changeQuery({ page: query.page - 1 })}>이전</button>
            <span>{query.page} / {totalPages}</span>
            <button type="button" disabled={query.page >= totalPages} onClick={() => changeQuery({ page: query.page + 1 })}>다음</button>
          </nav>
        )}
      </section>

    </>
  );
}

// 회원 상세 (목록에서 누른 회원 바로 아래 줄)
function MemberDetail({ member, onClose, onChanged }) {
  return (
    <div className="admin-member-detail">
      <div className="admin-card-heading">
        <div><h3>{member.nickName} 회원 상세</h3><p>회원 번호 {member.id}</p></div>
        <button type="button" className="admin-icon-button" aria-label="회원 상세 닫기" onClick={onClose}>
          <X size={theme.iconSize.md} aria-hidden="true" />
        </button>
      </div>
      <dl className="admin-detail-list">
        <div><dt>이메일</dt><dd>{member.emailMasked}</dd></div>
        <div><dt>가입일</dt><dd>{formatDate(member.joinedAt)}</dd></div>
        <div><dt>로그인 방법</dt><dd>{LOGIN_METHODS[member.loginMethod]}</dd></div>
        <div><dt>권한</dt><dd>{ROLE_LABELS[member.role] ?? member.role}</dd></div>
        <div><dt>나이대 · 성별</dt><dd>{member.ageBand ?? '미입력'} · {GENDER_LABELS[member.gender] ?? '미입력'}</dd></div>
        <div>
          <dt>로그인된 기기</dt>
          <dd>{member.activeSessions}대{member.lastUsedAt ? ` · 마지막 사용 ${formatDateTime(member.lastUsedAt)}` : ''}</dd>
        </div>
        <div>
          <dt>로그인 잠금</dt>
          <dd>
            {member.lockedMinutes > 0 ? `${member.lockedMinutes}분 남음 (5번 실패) ` : '잠금 없음'}
            {member.lockedMinutes > 0 && <UnlockButton member={member} onChanged={onChanged} />}
          </dd>
        </div>
      </dl>
      <RoleActions member={member} onChanged={onChanged} />
    </div>
  );
}

// 로그인 잠금 해제 (관리자 · 총관리자) — 5번 실패로 잠긴 회원이 문의했을 때. 운영 로그에 남는다
function UnlockButton({ member, onChanged }) {
  const [busy, setBusy] = useState(false);

  async function handleUnlock() {
    setBusy(true);
    try {
      await unlockMemberLogin(member.id);
      showToast(`${member.nickName} 님의 로그인 잠금을 풀었어요.`);
      onChanged();
    } catch (err) {
      showToast(errorMessage(err, '잠금을 풀지 못했습니다.'));
      if (err.response?.data?.error?.code === 'TARGET_MEMBER_NOT_FOUND') onChanged(); // 그사이 탈퇴한 회원 → 목록 새로고침
    } finally {
      setBusy(false);
    }
  }

  return (
    <button type="button" className="admin-text-button" onClick={handleUnlock} disabled={busy}>
      {busy ? '푸는 중…' : '잠금 해제'}
    </button>
  );
}

// 상세 아래 권한 영역 — 총관리자에게만 [관리자로 지정] / [관리자 해제] 버튼, 누르면 한 번 더 확인한다
// 자기 자신 · 총관리자는 바꿀 수 없다 (서버도 같은 규칙으로 막는다)
function RoleActions({ member, onChanged }) {
  const me = useAuthStore((state) => state.member);
  const [confirming, setConfirming] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');

  const canChange = me?.role === 'SUPER_ADMIN' && me.id !== member.id && member.role !== 'SUPER_ADMIN';
  if (!canChange) {
    const reason = me?.role !== 'SUPER_ADMIN'
      ? '관리자 권한은 총관리자만 주고 뺄 수 있습니다.'
      : member.role === 'SUPER_ADMIN' ? '총관리자의 권한은 바꿀 수 없습니다.' : '자기 자신의 권한은 바꿀 수 없습니다.';
    return (
      <div className="admin-inline-note">
        <ShieldCheck size={theme.iconSize.sm} aria-hidden="true" />
        <span>{reason}</span>
      </div>
    );
  }

  const nextRole = member.role === 'ADMIN' ? 'USER' : 'ADMIN';
  const actionLabel = nextRole === 'ADMIN' ? '관리자로 지정' : '관리자 해제';

  async function handleConfirm() {
    setBusy(true);
    setError('');
    try {
      await changeMemberRole(member.id, nextRole);
      showToast(`${member.nickName} 님을 ${nextRole === 'ADMIN' ? '관리자로 지정했어요' : '관리자에서 해제했어요'}. 다시 로그인하면 적용됩니다.`);
      setConfirming(false);
      onChanged(); // 현황 · 목록 다시 불러오기
    } catch (err) {
      setError(errorMessage(err, '권한을 바꾸지 못했습니다.'));
      if (err.response?.data?.error?.code === 'TARGET_MEMBER_NOT_FOUND') onChanged(); // 그사이 탈퇴한 회원 → 목록 새로고침
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="admin-member-role">
      {confirming ? (
        <>
          <p>
            <strong>{member.nickName}</strong> 님을 {actionLabel}할까요? 이 회원의 로그인된 기기는 모두 로그아웃되고, 다시 로그인하면 바뀐 권한이 적용됩니다.
          </p>
          <div className="admin-member-role-buttons">
            <button type="button" className="admin-outline-button" onClick={() => setConfirming(false)} disabled={busy}>취소</button>
            <button type="button" className="admin-primary-button" onClick={handleConfirm} disabled={busy}>
              {busy ? '바꾸는 중…' : actionLabel}
            </button>
          </div>
        </>
      ) : (
        <div className="admin-member-role-buttons">
          <span>총관리자 권한: 관리자 권한을 주거나 뺄 수 있습니다.</span>
          <button type="button" className="admin-outline-button" onClick={() => setConfirming(true)}>{actionLabel}</button>
        </div>
      )}
      {error && <p className="admin-member-role-error" role="alert">{error}</p>}
    </div>
  );
}
