import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { ArrowRight, Car, CheckCircle2, Cpu, Database, ListChecks, Server, Users } from 'lucide-react';
import theme from '../../styles/theme';
import { summaryCards } from './adminExampleData';
import { describeLog, formatLogTime, personName } from './adminLogFormat';
import { getAuditLogs, getMemberSummary, getSystemStatus, pingModelServer } from '../../features/admin/adminApi';
import { getVehicles } from '../../features/vehicle/vehicleApi';

const serviceIcons = { api: Server, database: Database, model: Cpu };
const tasks = [
  { title: '차량 정보 검수', note: '가격·연비·트림과 제조사 출처 확인', tab: 'vehicles', icon: Car },
  { title: '추천 카드 품질 확인', note: '이미지·차체·추천 사유 일치 여부 확인', tab: 'recommendations', icon: ListChecks },
  { title: '회원 상태 확인', note: '가입 현황·로그인 잠금·관리 권한 확인', tab: 'members', icon: Users },
];
// 7단계: 요약 카드 중 회원 · 차량 수는 실제 데이터로 바꾼다 (불러오는 중 "…", 실패하면 "-"). 나머지 카드는 예시 그대로
function useLiveCounts() {
  const [counts, setCounts] = useState({ members: '…', vehicles: '…' });
  useEffect(() => {
    const controller = new AbortController();
    const done = (key, value) => { if (!controller.signal.aborted) setCounts((prev) => ({ ...prev, [key]: value })); };
    getMemberSummary(controller.signal).then((summary) => done('members', `${summary.total}명`)).catch(() => done('members', '-'));
    getVehicles(controller.signal).then((vehicles) => done('vehicles', `${vehicles.length}건`)).catch(() => done('vehicles', '-'));
    return () => controller.abort();
  }, []);
  return counts;
}

// 7단계: 서비스 연결 상태 (실제 확인). Spring · MySQL 은 관리자 API 한 번, 추천 서버는 화면이 직접 불러 본다
// 상태: 'checking' 확인 중 · 'up' 정상 · 'down' 연결 안 됨
const CHECKING = { status: 'checking', detail: '확인 중…' };
function useServiceStatus() {
  const [rows, setRows] = useState({ api: CHECKING, database: CHECKING, model: CHECKING, checkedAt: null });
  useEffect(() => {
    const controller = new AbortController();
    const done = (next) => { if (!controller.signal.aborted) setRows((prev) => ({ ...prev, ...next })); };
    getSystemStatus(controller.signal)
      .then((s) => done({
        api: { status: 'up', detail: `회원·차량 서비스 · ${formatLogTime(s.apiStartedAt)} 부터 실행 중` },
        database: s.databaseUp
          ? { status: 'up', detail: `회원·차량 데이터 · 응답 ${s.databaseMillis}ms · DB 번호 V${s.databaseVersion}` }
          : { status: 'down', detail: 'DB 에 연결할 수 없습니다.' },
      }))
      // 관리자 API 자체가 실패 → 서버가 꺼졌거나, 서버가 권한을 확인하는 DB 가 꺼진 경우라 둘 다 확인할 수 없다
      .catch(() => done({
        api: { status: 'down', detail: '서버가 응답하지 않습니다.' },
        database: { status: 'down', detail: '서버를 거쳐 확인하므로 지금은 확인할 수 없습니다.' },
      }))
      .finally(() => done({ checkedAt: new Date() }));
    pingModelServer(controller.signal)
      .then((ms) => done({ model: { status: 'up', detail: `차량 추천 추론 · 응답 ${ms}ms` } }))
      .catch(() => done({ model: { status: 'down', detail: '추천 서버가 켜져 있지 않거나 3초 안에 응답하지 않습니다.' } }));
    return () => controller.abort();
  }, []);
  return rows;
}

const SERVICE_ROWS = [
  { id: 'api', name: 'Spring API' },
  { id: 'database', name: 'MySQL' },
  { id: 'model', name: '추천 서버' },
];
const STATUS_VIEW = {
  checking: { label: '확인 중', className: 'is-neutral' },
  up: { label: '정상', className: 'is-ok' },
  down: { label: '연결 안 됨', className: 'is-check' },
};

// 7단계: 최근 운영 이력 3건 (실제 기록). null = 불러오는 중, [] = 기록 없음 또는 실패
function useRecentLogs() {
  const [logs, setLogs] = useState(null);
  useEffect(() => {
    const controller = new AbortController();
    getAuditLogs({ size: 3 }, controller.signal)
      .then((result) => setLogs(result.logs))
      .catch(() => { if (!controller.signal.aborted) setLogs([]); });
    return () => controller.abort();
  }, []);
  return logs;
}

export default function AdminOverviewPanel() {
  const counts = useLiveCounts();
  const recentLogs = useRecentLogs();
  const serviceStatus = useServiceStatus();
  // 회원 · 차량 카드는 실제 수, 나머지는 예시 값
  const cards = summaryCards.map((card) => (counts[card.destination] ? { ...card, value: counts[card.destination] } : card));
  return <div className="admin-panel-stack">
    <section className="admin-summary" aria-label="운영 요약">{cards.map(card => <Link className="admin-stat" to={`/admin?tab=${card.destination}`} key={card.label}><span>{card.label}</span><strong>{card.value}</strong><small>{card.note}</small></Link>)}</section>
    <div className="admin-grid-2"><section className="admin-card"><div className="admin-card-heading"><div><h3>먼저 확인할 작업</h3><p>검수가 필요한 항목을 확인하세요.</p></div><span className="admin-count-badge">3개 항목</span></div><div className="admin-task-list">{tasks.map(({ title, note, tab, icon: Icon }) => <Link key={tab} to={`/admin?tab=${tab}`} className="admin-task"><span className="admin-icon-box"><Icon size={theme.iconSize.md} aria-hidden="true" /></span><div><strong>{title}</strong><p>{note}</p></div><ArrowRight size={theme.iconSize.sm} aria-hidden="true" /></Link>)}</div></section>
      <section className="admin-card"><div className="admin-card-heading"><div><h3>서비스 연결 상태</h3><p>화면을 열 때 서버 · DB · 추천 서버가 응답하는지 확인합니다.</p></div><span className="admin-count-badge">{serviceStatus.checkedAt ? `${serviceStatus.checkedAt.toTimeString().slice(0, 5)} 확인` : '확인 중'}</span></div><div className="admin-service-list" aria-live="polite">{SERVICE_ROWS.map(service => { const Icon = serviceIcons[service.id]; const row = serviceStatus[service.id]; const view = STATUS_VIEW[row.status]; return <div className="admin-service-row" key={service.id}><Icon size={theme.iconSize.md} aria-hidden="true" /><div><strong>{service.name}</strong><p>{row.detail}</p></div><span className={`admin-status ${view.className}`}>{view.label}</span></div>; })}</div></section></div>
    <section className="admin-card"><div className="admin-card-heading"><div><h3>최근 운영 이력</h3><p>관리자 작업과 서비스 변경 기록</p></div><Link className="admin-text-button" to="/admin?tab=logs">전체 이력 보기<ArrowRight size={theme.iconSize.sm} aria-hidden="true" /></Link></div><div className="admin-activity-list">{recentLogs === null && <p className="admin-empty" role="status">불러오는 중…</p>}{recentLogs?.length === 0 && <p className="admin-empty">아직 기록된 관리자 작업이 없습니다.</p>}{recentLogs?.map(log => <div className="admin-activity" key={log.id}><CheckCircle2 size={theme.iconSize.sm} aria-hidden="true" /><div><strong>{personName(log.targetNickName, log.targetId)} · {describeLog(log)}</strong><span>{personName(log.actorNickName, log.actorId)}</span></div><time>{formatLogTime(log.createdAt)}</time></div>)}</div></section>
  </div>;
}
