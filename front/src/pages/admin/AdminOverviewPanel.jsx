import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { ArrowRight, Car, CheckCircle2, Cpu, Database, ListChecks, Server, Users } from 'lucide-react';
import theme from '../../styles/theme';
import { services, summaryCards } from './adminExampleData';
import { describeLog, formatLogTime, personName } from './adminLogFormat';
import { getAuditLogs, getMemberSummary } from '../../features/admin/adminApi';
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
  // 회원 · 차량 카드는 실제 수, 나머지는 예시 값
  const cards = summaryCards.map((card) => (counts[card.destination] ? { ...card, value: counts[card.destination] } : card));
  return <div className="admin-panel-stack">
    <section className="admin-summary" aria-label="운영 요약">{cards.map(card => <Link className="admin-stat" to={`/admin?tab=${card.destination}`} key={card.label}><span>{card.label}</span><strong>{card.value}</strong><small>{card.note}</small></Link>)}</section>
    <div className="admin-grid-2"><section className="admin-card"><div className="admin-card-heading"><div><h3>먼저 확인할 작업</h3><p>검수가 필요한 항목을 확인하세요.</p></div><span className="admin-count-badge">3개 항목</span></div><div className="admin-task-list">{tasks.map(({ title, note, tab, icon: Icon }) => <Link key={tab} to={`/admin?tab=${tab}`} className="admin-task"><span className="admin-icon-box"><Icon size={theme.iconSize.md} aria-hidden="true" /></span><div><strong>{title}</strong><p>{note}</p></div><ArrowRight size={theme.iconSize.sm} aria-hidden="true" /></Link>)}</div></section>
      <section className="admin-card"><div className="admin-card-heading"><div><h3>서비스 연결 상태</h3><p>연결 상태 표시 예시입니다.</p></div><span className="admin-count-badge">예시</span></div><div className="admin-service-list">{services.map(service => { const Icon = serviceIcons[service.id]; return <div className="admin-service-row" key={service.id}><Icon size={theme.iconSize.md} aria-hidden="true" /><div><strong>{service.name}</strong><p>{service.detail}</p></div><span className={`admin-status ${service.status === '정상' ? 'is-ok' : 'is-check'}`}>{service.status}</span></div>; })}</div></section></div>
    <section className="admin-card"><div className="admin-card-heading"><div><h3>최근 운영 이력</h3><p>관리자 작업과 서비스 변경 기록</p></div><Link className="admin-text-button" to="/admin?tab=logs">전체 이력 보기<ArrowRight size={theme.iconSize.sm} aria-hidden="true" /></Link></div><div className="admin-activity-list">{recentLogs === null && <p className="admin-empty" role="status">불러오는 중…</p>}{recentLogs?.length === 0 && <p className="admin-empty">아직 기록된 관리자 작업이 없습니다.</p>}{recentLogs?.map(log => <div className="admin-activity" key={log.id}><CheckCircle2 size={theme.iconSize.sm} aria-hidden="true" /><div><strong>{personName(log.targetNickName, log.targetId)} · {describeLog(log)}</strong><span>{personName(log.actorNickName, log.actorId)}</span></div><time>{formatLogTime(log.createdAt)}</time></div>)}</div></section>
  </div>;
}
