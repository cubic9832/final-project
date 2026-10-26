import { Link } from 'react-router-dom';
import { ArrowRight, Car, CheckCircle2, Cpu, Database, ListChecks, Server, Users } from 'lucide-react';
import theme from '../../styles/theme';
import { auditLogs, services, summaryCards } from './adminExampleData';

const serviceIcons = { api: Server, database: Database, model: Cpu };
const tasks = [
  { title: '차량 정보 검수', note: '가격·연비·트림과 제조사 출처 확인', tab: 'vehicles', icon: Car },
  { title: '추천 카드 품질 확인', note: '이미지·차체·추천 사유 일치 여부 확인', tab: 'recommendations', icon: ListChecks },
  { title: '회원 상태 확인', note: '가입 현황·로그인 잠금·관리 권한 확인', tab: 'members', icon: Users },
];
export default function AdminOverviewPanel() {
  return <div className="admin-panel-stack">
    <section className="admin-summary" aria-label="운영 요약">{summaryCards.map(card => <Link className="admin-stat" to={`/admin?tab=${card.destination}`} key={card.label}><span>{card.label}</span><strong>{card.value}</strong><small>{card.note}</small></Link>)}</section>
    <div className="admin-grid-2"><section className="admin-card"><div className="admin-card-heading"><div><h3>먼저 확인할 작업</h3><p>검수가 필요한 항목을 확인하세요.</p></div><span className="admin-count-badge">3개 항목</span></div><div className="admin-task-list">{tasks.map(({ title, note, tab, icon: Icon }) => <Link key={tab} to={`/admin?tab=${tab}`} className="admin-task"><span className="admin-icon-box"><Icon size={theme.iconSize.md} aria-hidden="true" /></span><div><strong>{title}</strong><p>{note}</p></div><ArrowRight size={theme.iconSize.sm} aria-hidden="true" /></Link>)}</div></section>
      <section className="admin-card"><div className="admin-card-heading"><div><h3>서비스 연결 상태</h3><p>연결 상태 표시 예시입니다.</p></div><span className="admin-count-badge">예시</span></div><div className="admin-service-list">{services.map(service => { const Icon = serviceIcons[service.id]; return <div className="admin-service-row" key={service.id}><Icon size={theme.iconSize.md} aria-hidden="true" /><div><strong>{service.name}</strong><p>{service.detail}</p></div><span className={`admin-status ${service.status === '정상' ? 'is-ok' : 'is-check'}`}>{service.status}</span></div>; })}</div></section></div>
    <section className="admin-card"><div className="admin-card-heading"><div><h3>최근 운영 이력</h3><p>관리자 작업과 서비스 변경 기록</p></div><Link className="admin-text-button" to="/admin?tab=logs">전체 이력 보기<ArrowRight size={theme.iconSize.sm} aria-hidden="true" /></Link></div><div className="admin-activity-list">{auditLogs.slice(0, 3).map(log => <div className="admin-activity" key={log.id}><CheckCircle2 size={theme.iconSize.sm} aria-hidden="true" /><div><strong>{log.action}</strong><span>{log.target} · {log.actor}</span></div><time>{log.time}</time></div>)}</div></section>
  </div>;
}
