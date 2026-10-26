// 7단계: 운영 로그 탭 (실제 데이터, V13 admin_audit_logs)
// 지금 기록되는 작업은 총관리자의 관리자 권한 주기 · 빼기. 이름은 지금 회원 정보에서 읽고, 탈퇴했으면 "탈퇴한 회원"
import { useEffect, useState } from 'react';
import { Download } from 'lucide-react';
import theme from '../../styles/theme';
import { getAuditLogs } from '../../features/admin/adminApi';
import { ACTION_LABELS, describeLog, formatLogTime, personName } from './adminLogFormat';
import './AdminMembersPanel.css';

const PAGE_SIZE = 20;
// 지금 화면에 보이는 기록만 CSV 로 내려받는다 (엑셀에서 한글이 깨지지 않게 BOM 을 붙인다)
function downloadCsv(logs) {
  const values = [
    ['시각', '관리자', '작업', '대상', '내용'],
    ...logs.map((log) => [formatLogTime(log.createdAt), personName(log.actorNickName, log.actorId),
      ACTION_LABELS[log.action] ?? log.action, personName(log.targetNickName, log.targetId), describeLog(log)]),
  ];
  const csv = values.map((row) => row.map((value) => `"${String(value).replaceAll('"', '""')}"`).join(',')).join('\n');
  const url = URL.createObjectURL(new Blob(['﻿', csv], { type: 'text/csv;charset=utf-8' }));
  const link = document.createElement('a');
  link.href = url;
  link.download = 'admin-audit-logs.csv';
  link.click();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
}

export default function AdminLogsPanel() {
  const [query, setQuery] = useState({ action: '', page: 1 });
  const [state, setState] = useState({ status: 'loading', logs: [], meta: null, error: '' });
  const [reloadKey, setReloadKey] = useState(0);

  useEffect(() => {
    const controller = new AbortController();
    getAuditLogs({ ...query, size: PAGE_SIZE }, controller.signal)
      .then(({ logs, meta }) => setState({ status: 'done', logs, meta, error: '' }))
      .catch((error) => {
        if (!controller.signal.aborted) {
          setState({ status: 'error', logs: [], meta: null, error: error.response?.data?.error?.message ?? '운영 로그를 불러오지 못했습니다.' });
        }
      });
    return () => controller.abort();
  }, [query, reloadKey]);

  function changeQuery(next) {
    setState((prev) => ({ ...prev, status: 'loading' }));
    setQuery((prev) => ({ ...prev, ...next }));
  }

  const { logs, meta } = state;
  const totalPages = meta?.totalPages ?? 1;

  return (
    <section className="admin-card">
      <div className="admin-card-heading">
        <div><h3>운영 이력</h3><p>관리자 작업 기록 (최근 순). 지금은 관리자 권한 주기 · 빼기가 기록됩니다.</p></div>
        <button type="button" className="admin-outline-button" disabled={!logs.length} onClick={() => downloadCsv(logs)}>
          <Download size={theme.iconSize.sm} aria-hidden="true" />CSV 내보내기
        </button>
      </div>

      <div className="admin-filters">
        <label className="admin-filter-field">
          작업
          <select value={query.action} onChange={(event) => changeQuery({ action: event.target.value, page: 1 })}>
            <option value="">전체</option>
            <option value="ROLE_CHANGE">권한 변경</option>
          </select>
        </label>
      </div>

      {state.status === 'loading' && <p className="admin-empty" role="status">운영 로그를 불러오는 중…</p>}
      {state.status === 'error' && (
        <p className="admin-empty" role="alert">
          {state.error}{' '}
          <button type="button" className="admin-text-button" onClick={() => { changeQuery({}); setReloadKey((key) => key + 1); }}>
            다시 시도
          </button>
        </p>
      )}
      {state.status === 'done' && logs.length === 0 && (
        <p className="admin-empty" role="status">아직 기록된 관리자 작업이 없습니다.</p>
      )}
      {state.status === 'done' && logs.length > 0 && (
        <div className="admin-table-wrap">
          <table className="admin-table">
            <caption className="admin-sr-only">관리자 작업 기록</caption>
            <thead>
              <tr><th scope="col">시각</th><th scope="col">작업</th><th scope="col">대상 · 내용</th><th scope="col">관리자</th></tr>
            </thead>
            <tbody>
              {logs.map((log) => (
                <tr key={log.id}>
                  <td>{formatLogTime(log.createdAt)}</td>
                  <td>{ACTION_LABELS[log.action] ?? log.action}</td>
                  <td><strong>{personName(log.targetNickName, log.targetId)}</strong><small>{describeLog(log)}</small></td>
                  <td>{personName(log.actorNickName, log.actorId)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
      {meta && <p className="admin-result-count" aria-live="polite">전체 {meta.total}건</p>}

      {totalPages > 1 && (
        <nav className="admin-member-pagination" aria-label="운영 로그 페이지">
          <button type="button" disabled={query.page <= 1} onClick={() => changeQuery({ page: query.page - 1 })}>이전</button>
          <span>{query.page} / {totalPages}</span>
          <button type="button" disabled={query.page >= totalPages} onClick={() => changeQuery({ page: query.page + 1 })}>다음</button>
        </nav>
      )}
    </section>
  );
}
