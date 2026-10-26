// 7단계: 관리자 대시보드 — 회원 관리 탭 (실제 데이터)
// 위: 회원 현황 (전체 · 최근 7일 가입 · 구글 · 관리자, 7일 가입 추이, 나이대 · 성별)
// 아래: 회원 목록 (검색 · 권한 · 페이지) + 상세. 이메일은 서버가 가려서 보낸다. 권한 변경 · 잠금 해제는 아직 없음
import { useEffect, useState } from 'react';
import { Search, ShieldCheck, X } from 'lucide-react';
import theme from '../../styles/theme';
import { getAdminMembers, getMemberSummary } from '../../features/admin/adminApi';
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
  return (
    <div className="admin-panel-stack">
      <MemberSummary />
      <MemberList />
    </div>
  );
}

// ① 회원 현황 — 화면이 열릴 때 한 번 불러온다 ([다시 시도] 로 다시)
function MemberSummary() {
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
  }, [reloadKey]);

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
        <div className="admin-stat"><span>관리자</span><strong>{summary.admins}명</strong><small>DB 에서 role 지정</small></div>
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
function MemberList() {
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
  }, [query, reloadKey]);

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
  const selected = members.find((member) => member.id === selectedId);
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
                {members.map((member) => (
                  <tr key={member.id}>
                    <td><strong>{member.nickName}</strong><small>{member.emailMasked}</small></td>
                    <td>{formatDate(member.joinedAt)}</td>
                    <td>{LOGIN_METHODS[member.loginMethod]}</td>
                    <td>{member.role === 'ADMIN' ? '관리자' : '일반 회원'}</td>
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
                        onClick={() => setSelectedId(member.id)}
                      >
                        상세 보기
                      </button>
                    </td>
                  </tr>
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

      {selected && (
        <section className="admin-card">
          <div className="admin-card-heading">
            <div><h3>{selected.nickName} 회원 상세</h3><p>회원 번호 {selected.id}</p></div>
            <button type="button" className="admin-icon-button" aria-label="회원 상세 닫기" onClick={() => setSelectedId(null)}>
              <X size={theme.iconSize.md} aria-hidden="true" />
            </button>
          </div>
          <dl className="admin-detail-list">
            <div><dt>이메일</dt><dd>{selected.emailMasked}</dd></div>
            <div><dt>가입일</dt><dd>{formatDate(selected.joinedAt)}</dd></div>
            <div><dt>로그인 방법</dt><dd>{LOGIN_METHODS[selected.loginMethod]}</dd></div>
            <div><dt>권한</dt><dd>{selected.role === 'ADMIN' ? '관리자' : '일반 회원'}</dd></div>
            <div><dt>나이대 · 성별</dt><dd>{selected.ageBand ?? '미입력'} · {GENDER_LABELS[selected.gender] ?? '미입력'}</dd></div>
            <div>
              <dt>로그인된 기기</dt>
              <dd>{selected.activeSessions}대{selected.lastUsedAt ? ` · 마지막 사용 ${formatDateTime(selected.lastUsedAt)}` : ''}</dd>
            </div>
            <div><dt>로그인 잠금</dt><dd>{selected.lockedMinutes > 0 ? `${selected.lockedMinutes}분 남음 (5번 실패)` : '잠금 없음'}</dd></div>
          </dl>
          <div className="admin-inline-note">
            <ShieldCheck size={theme.iconSize.sm} aria-hidden="true" />
            <span>권한 변경 · 로그인 잠금 해제는 아직 화면에서 할 수 없습니다. 권한은 DB 에서 바꿉니다.</span>
          </div>
        </section>
      )}
    </>
  );
}
