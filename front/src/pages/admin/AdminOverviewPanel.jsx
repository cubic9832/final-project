import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { ArrowRight, CheckCircle2, Cpu, Database, Lock, Server, UserRoundPen } from 'lucide-react';
import theme from '../../styles/theme';
import { describeLog, formatLogTime, personName } from './adminLogFormat';
import { getAdminOverview, getAuditLogs, getMemberSummary, getModelServerInfo, getSystemStatus } from '../../features/admin/adminApi';
import { getVehicles } from '../../features/vehicle/vehicleApi';
import './AdminMembersPanel.css'; // 7일 막대(admin-member-trend) 같이 씀

// 7단계 운영 현황 — 화면의 모든 값은 실제 데이터 (10-27: 남아 있던 고정 값도 모두 바꿈)
// 회원 · 진단 · 할 일 = 관리자 API(DB), 차량 = 차량 API(DB), 추천 후보 · 모델 = 추천 서버(FastAPI) 정보
// 각 값은 따로 불러온다: 불러오는 중 undefined, 실패하면 null → 화면에는 "…" / "-"

// 불러오기 하나를 { key: 결과 } 로 모아 두는 작은 도우미 (화면을 떠나면 응답을 버린다)
function useLoads(loaders) {
  const [data, setData] = useState({});
  useEffect(() => {
    const controller = new AbortController();
    for (const [key, load] of Object.entries(loaders)) {
      load(controller.signal)
        .then((value) => !controller.signal.aborted && setData((prev) => ({ ...prev, [key]: value })))
        .catch(() => !controller.signal.aborted && setData((prev) => ({ ...prev, [key]: null })));
    }
    return () => controller.abort();
  }, [loaders]);
  return data;
}

// 컴포넌트 밖에 두어 매번 새로 만들어지지 않게 (useEffect 가 한 번만 돈다)
const LOADERS = {
  members: getMemberSummary,
  vehicles: getVehicles,
  overview: getAdminOverview,
  system: getSystemStatus,
  model: getModelServerInfo,
  logs: (signal) => getAuditLogs({ size: 3 }, signal).then((result) => result.logs),
};

// 값 표시: 불러오는 중 "…", 실패 "-"
const show = (value, format) => (value === undefined ? '…' : value === null ? '-' : format(value));
const formatManwon = (won) => `${Math.round(won / 10000).toLocaleString('ko-KR')}만 원`;

const serviceIcons = { api: Server, database: Database, model: Cpu };
const STATUS_VIEW = {
  checking: { label: '확인 중', className: 'is-neutral' },
  up: { label: '정상', className: 'is-ok' },
  down: { label: '연결 안 됨', className: 'is-check' },
};

// 서비스 연결 상태 3줄. Spring · MySQL 은 관리자 API 한 번, 추천 서버는 화면이 직접 불러 본다
function serviceRows({ system, model }) {
  const apiRow = system === undefined ? { status: 'checking', detail: '확인 중…' }
    : system ? { status: 'up', detail: `회원·차량 서비스 · ${formatLogTime(system.apiStartedAt)} 부터 실행 중` }
      : { status: 'down', detail: '서버가 응답하지 않습니다.' };
  const dbRow = system === undefined ? { status: 'checking', detail: '확인 중…' }
    : system?.databaseUp ? { status: 'up', detail: `회원·차량 데이터 · 응답 ${system.databaseMillis}ms · DB 번호 V${system.databaseVersion}` }
      // 관리자 API 자체가 실패하면 권한 확인에 쓰는 DB 도 확인할 수 없다
      : { status: 'down', detail: system ? 'DB 에 연결할 수 없습니다.' : '서버를 거쳐 확인하므로 지금은 확인할 수 없습니다.' };
  const modelRow = model === undefined ? { status: 'checking', detail: '확인 중…' }
    : model ? { status: 'up', detail: `차량 추천 추론 · ${model.info.modelVersion} · 응답 ${model.ms}ms` }
      : { status: 'down', detail: '추천 서버가 켜져 있지 않거나 3초 안에 응답하지 않습니다.' };
  return [
    { id: 'api', name: 'Spring API', ...apiRow },
    { id: 'database', name: 'MySQL', ...dbRow },
    { id: 'model', name: '추천 서버', ...modelRow },
  ];
}

export default function AdminOverviewPanel() {
  const data = useLoads(LOADERS);
  const { members, vehicles, overview, model, logs } = data;

  const cards = [
    { label: '차량 데이터', value: show(vehicles, (list) => `${list.length}건`), note: '차량·트림 정보 관리', tab: 'vehicles' },
    { label: '추천 후보 차량', value: show(model, (m) => `${m.info.catalogCount}건`), note: model ? `차종 ${model.info.modelNames}개 · 추천 서버 기준` : '추천 서버 기준', tab: 'recommendations' },
    { label: '회원 현황', value: show(members, (s) => `${s.total}명`), note: members ? `최근 7일 가입 ${members.newLast7Days}명` : '가입·상태·권한 확인', tab: 'members' },
    { label: '적용 모델', value: show(model, (m) => m.info.modelVersion), note: model ? `학습 구조 ${model.info.rankerSchema}` : '차량 추천 모델', tab: 'models' },
  ];

  // 먼저 확인할 작업: 실제 개수. 0 이면 "없음" 으로 흐리게
  const tasks = [
    { title: '생년월일 · 성별 미입력 회원', count: overview?.profileMissing, note: '연령대 통계와 추천에 쓰이는 정보 — 구글 가입 직후 등', tab: 'members', icon: UserRoundPen },
    { title: '로그인이 잠긴 회원', count: overview?.lockedMembers, note: '비밀번호 5번 실패로 10분 잠금 — 회원 상세에서 잠금 해제', tab: 'members', icon: Lock },
    { title: '추천 서버 연결', count: model === null ? 1 : model ? 0 : undefined, note: model === null ? '추천 서버가 응답하지 않습니다 (ml/serve-candidates.ps1)' : '추천 서버가 정상 응답합니다', tab: 'models', icon: Cpu },
  ];
  const todo = tasks.filter((task) => task.count > 0).length;

  const stats = overview?.diagnoses;
  const maxDaily = Math.max(1, ...(stats?.daily ?? []).map((day) => day.count));
  const services = serviceRows(data);

  return <div className="admin-panel-stack">
    <section className="admin-summary" aria-label="운영 요약">{cards.map(card => <Link className="admin-stat" to={`/console?tab=${card.tab}`} key={card.label}><span>{card.label}</span><strong>{card.value}</strong><small>{card.note}</small></Link>)}</section>
    <div className="admin-grid-2">
      <section className="admin-card"><div className="admin-card-heading"><div><h3>먼저 확인할 작업</h3><p>지금 처리가 필요한 항목입니다.</p></div><span className="admin-count-badge">{overview === undefined ? '확인 중' : `할 일 ${todo}개`}</span></div>
        <div className="admin-task-list">{tasks.map(({ title, count, note, tab, icon: Icon }) => <Link key={title} to={`/console?tab=${tab}`} className="admin-task"><span className="admin-icon-box"><Icon size={theme.iconSize.md} aria-hidden="true" /></span><div><strong>{title} · {count === undefined ? '…' : title === '추천 서버 연결' ? (count ? '확인 필요' : '정상') : count ? `${count}명` : '없음'}</strong><p>{note}</p></div><ArrowRight size={theme.iconSize.sm} aria-hidden="true" /></Link>)}</div>
      </section>
      <section className="admin-card"><div className="admin-card-heading"><div><h3>서비스 연결 상태</h3><p>화면을 열 때 서버 · DB · 추천 서버가 응답하는지 확인합니다.</p></div></div>
        <div className="admin-service-list" aria-live="polite">{services.map(service => { const Icon = serviceIcons[service.id]; const view = STATUS_VIEW[service.status]; return <div className="admin-service-row" key={service.id}><Icon size={theme.iconSize.md} aria-hidden="true" /><div><strong>{service.name}</strong><p>{service.detail}</p></div><span className={`admin-status ${view.className}`}>{view.label}</span></div>; })}</div>
      </section>
    </div>
    {/* 재무 진단 이용 현황 — 회원이 재무 진단 결과 화면에서 저장한 기록 (탈퇴 회원 제외) */}
    <section className="admin-card"><div className="admin-card-heading"><div><h3>재무 진단 이용 현황</h3><p>회원이 재무 진단을 마칠 때 저장되는 기록입니다.</p></div></div>
      {overview === null && <p className="admin-empty" role="alert">재무 진단 현황을 불러오지 못했습니다.</p>}
      {stats && <div className="admin-grid-2">
        <dl className="admin-detail-list">
          <div><dt>전체 진단</dt><dd>{stats.total}건</dd></div>
          <div><dt>최근 7일</dt><dd>{stats.last7Days}건</dd></div>
          <div><dt>진단한 회원</dt><dd>{stats.members}명</dd></div>
          <div><dt>평균 구매 전 월 여유금</dt><dd>{stats.avgMonthlyAvailable == null ? '기록 없음' : formatManwon(stats.avgMonthlyAvailable)}</dd></div>
        </dl>
        <ol className="admin-member-trend" aria-label="최근 7일 날짜별 진단 수">{stats.daily.map(day => <li key={day.date}><span className="admin-member-trend-count">{day.count}</span><span className="admin-member-trend-bar" style={{ height: `${(day.count / maxDaily) * 100}%` }} /><span className="admin-member-trend-date">{day.date.slice(5).replace('-', '.')}</span></li>)}</ol>
      </div>}
    </section>
    <section className="admin-card"><div className="admin-card-heading"><div><h3>최근 운영 이력</h3><p>관리자 작업과 서비스 변경 기록</p></div><Link className="admin-text-button" to="/console?tab=logs">전체 이력 보기<ArrowRight size={theme.iconSize.sm} aria-hidden="true" /></Link></div><div className="admin-activity-list">{logs === undefined && <p className="admin-empty" role="status">불러오는 중…</p>}{(logs === null || logs?.length === 0) && <p className="admin-empty">아직 기록된 관리자 작업이 없습니다.</p>}{logs?.map(log => <div className="admin-activity" key={log.id}><CheckCircle2 size={theme.iconSize.sm} aria-hidden="true" /><div><strong>{personName(log.targetNickName, log.targetId)} · {describeLog(log)}</strong><span>{personName(log.actorNickName, log.actorId)}</span></div><time>{formatLogTime(log.createdAt)}</time></div>)}</div></section>
  </div>;
}
