import { useState } from 'react';
import { Link, useSearchParams } from 'react-router-dom';
import { ArrowUpRight, Car, Cpu, LayoutDashboard, ListChecks, RefreshCw, ScrollText, ShieldCheck, Users } from 'lucide-react';
import theme from '../../styles/theme';
import AdminOverviewPanel from './AdminOverviewPanel';
import AdminVehiclesPanel from './AdminVehiclesPanel';
import AdminRecommendationsPanel from './AdminRecommendationsPanel';
import AdminMembersPanel from './AdminMembersPanel';
import AdminModelsPanel from './AdminModelsPanel';
import AdminLogsPanel from './AdminLogsPanel';
import './AdminPage.css';

const sections = [
  { id: 'overview', label: '운영 현황', icon: LayoutDashboard, description: '데이터와 서비스 상태를 한눈에 살펴보세요.', panel: AdminOverviewPanel },
  { id: 'vehicles', label: '차량 관리', icon: Car, description: '차량별 주요 정보와 공개 상태를 확인합니다.', panel: AdminVehiclesPanel },
  { id: 'recommendations', label: '추천 관리', icon: ListChecks, description: '추천 서버가 고르는 후보 차량의 가격 출처와 확인 상태를 검수합니다.', panel: AdminRecommendationsPanel },
  { id: 'members', label: '회원 관리', icon: Users, description: '가입 현황과 회원 상태, 운영 권한을 확인합니다.', panel: AdminMembersPanel },
  { id: 'models', label: '모델 관리', icon: Cpu, description: '적용 중인 모델의 평가 결과와 학습 기록을 확인합니다.', panel: AdminModelsPanel },
  { id: 'logs', label: '운영 로그', icon: ScrollText, description: '관리자 변경 이력과 서비스 오류를 추적합니다.', panel: AdminLogsPanel },
];

// 관리자 대시보드. 7단계: 회원 관리 · 운영 로그 탭, 운영 현황의 회원 · 차량 수 · 서비스 연결 상태 · 최근 이력은 실제 데이터(/api/v1/admin/**)
// 10-27: 화면의 "예시" 표시 · 안내 문구는 지웠다 (사용자 요청). 10-27 오후: 추천 · 모델 탭도 실제 데이터 (추천 서버 학습 결과 · DB)
export default function AdminPage() {
  const [params] = useSearchParams();
  const [updatedAt, setUpdatedAt] = useState(() => new Date());
  const section = sections.find(item => item.id === params.get('tab')) || sections[0];
  const Panel = section.panel;
  return <div className="admin-page">
    <div className="admin-workspace-heading"><div><span className="admin-eyebrow">ADMIN WORKSPACE</span><h1>관리자 대시보드</h1><p>차량과 추천 서비스를 한곳에서 관리하세요.</p></div></div>
    <div className="admin-workspace">
      <aside className="admin-sidebar"><div className="admin-sidebar-heading"><ShieldCheck size={theme.iconSize.md} aria-hidden="true" /><div><strong>운영 관리</strong><span>CreditComPass Auto</span></div></div>
        <nav className="admin-navigation" aria-label="관리자 메뉴">{sections.map(({ id, label, icon: Icon }) => <Link key={id} to={`/admin?tab=${id}`} aria-current={section.id === id ? 'page' : undefined}><Icon size={theme.iconSize.md} aria-hidden="true" /><span>{label}</span></Link>)}</nav>
        <div className="admin-sidebar-footer"><Link to="/">서비스 홈 보기<ArrowUpRight size={theme.iconSize.sm} aria-hidden="true" /></Link></div>
      </aside>
      <div className="admin-content"><header className="admin-heading"><div><h2>{section.label}</h2><p>{section.description}</p></div><button className="admin-outline-button" type="button" onClick={() => setUpdatedAt(new Date())}><RefreshCw size={theme.iconSize.sm} aria-hidden="true" />화면 새로고침</button></header><div className="admin-preview-note"><span role="status">표시 시각 {updatedAt.toLocaleTimeString('ko-KR', { hour: '2-digit', minute: '2-digit', second: '2-digit', hour12: false })}</span></div><Panel key={`${section.id}-${updatedAt.getTime()}`} /></div>
    </div>
  </div>;
}
