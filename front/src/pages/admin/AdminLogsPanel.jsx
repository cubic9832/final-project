import { useState } from 'react';
import { Download, Search } from 'lucide-react';
import theme from '../../styles/theme';
import { auditLogs } from './adminExampleData';

function downloadCsv(rows) {
  const values = [['시각', '실행자', '유형', '작업', '대상', '결과'], ...rows.map(row => [row.time, row.actor, row.type, row.action, row.target, row.result])];
  const csv = values.map(row => row.map(value => `"${String(value).replaceAll('"', '""')}"`).join(',')).join('\n');
  const url = URL.createObjectURL(new Blob(['\uFEFF', csv], { type: 'text/csv;charset=utf-8' }));
  const link = document.createElement('a');
  link.href = url;
  link.download = 'admin-example-logs.csv';
  link.click();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
}
export default function AdminLogsPanel() {
  const [type, setType] = useState('');
  const [keyword, setKeyword] = useState('');
  const rows = auditLogs.filter(row => (!type || row.type === type) && `${row.actor} ${row.action} ${row.target}`.toLowerCase().includes(keyword.trim().toLowerCase()));
  return <section className="admin-card"><div className="admin-card-heading"><div><h3>운영 이력</h3><p>화면에 표시된 예시 로그만 내보냅니다.</p></div><button type="button" className="admin-outline-button" disabled={!rows.length} onClick={() => downloadCsv(rows)}><Download size={theme.iconSize.sm} aria-hidden="true" />CSV 내보내기</button></div><div className="admin-filters"><label className="admin-search-field"><Search size={theme.iconSize.sm} aria-hidden="true" /><input type="search" aria-label="운영 로그 검색" placeholder="작업·대상·실행자 검색" value={keyword} onChange={event => setKeyword(event.target.value)} /></label><label className="admin-filter-field">로그 유형<select value={type} onChange={event => setType(event.target.value)}><option value="">전체</option><option>관리자 변경</option><option>서비스 오류</option></select></label></div><div className="admin-table-wrap"><table className="admin-table"><caption className="admin-sr-only">관리자 변경 및 서비스 오류 예시</caption><thead><tr><th scope="col">시각</th><th scope="col">유형</th><th scope="col">작업·대상</th><th scope="col">실행자</th><th scope="col">결과</th></tr></thead><tbody>{rows.map(log => <tr key={log.id}><td>{log.time}</td><td>{log.type}</td><td><strong>{log.action}</strong><small>{log.target}</small></td><td>{log.actor}</td><td><span className={`admin-status ${log.result === '완료' ? 'is-ok' : 'is-check'}`}>{log.result}</span></td></tr>)}</tbody></table></div>{!rows.length && <p className="admin-empty" role="status">조건에 맞는 로그가 없습니다. 검색어나 유형을 변경해 주세요.</p>}<p className="admin-result-count" aria-live="polite">검색 결과 {rows.length}건</p></section>;
}
