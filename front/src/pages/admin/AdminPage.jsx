// 관리자 대시보드 (Figma: ADMIN 01 · 관리자 대시보드)
// 백엔드·권한(관리자만 접근) 연결 전이라 예시 데이터로 화면만 구성한다.
// API 연결 시 adminExampleData 대신 서버 응답을 쓰고, 라우트를 관리자 전용으로 감싼다.
import { useEffect, useState } from 'react';
import { Car, Cpu, Monitor, Search, Server, Users } from 'lucide-react';
import {
  auditLogs,
  deployments,
  managementCards,
  modelInfo,
  modelMetrics,
  modelScoreCards,
  pipelineSteps,
  pipelineWarning,
  services,
  summaryCards,
} from './adminExampleData';
import ModelMetricChart from './ModelMetricChart';
import theme from '../../styles/theme';
import './AdminPage.css';

const SERVICE_ICONS = { model: Cpu, api: Server, web: Monitor, search: Search };
const MANAGEMENT_ICONS = { vehicle: Car, user: Users };
const PERIOD_OPTIONS = ['최근 7일', '최근 30일', '최근 90일'];

// 예: 2026.10.14 13:05
function formatNow() {
  const now = new Date();
  const pad = (n) => String(n).padStart(2, '0');
  return `${now.getFullYear()}.${pad(now.getMonth() + 1)}.${pad(now.getDate())} ${pad(now.getHours())}:${pad(now.getMinutes())}`;
}

// 감사 로그를 CSV 파일로 내려받는다 (지금 화면에 걸러진 목록 기준)
function downloadCsv(rows) {
  const header = ['시각', '실행자', '작업', '대상'];
  const lines = rows.map((log) => [log.time, log.actor, log.action, log.target]);
  const csv = [header, ...lines]
    .map((cells) => cells.map((cell) => `"${String(cell).replaceAll('"', '""')}"`).join(','))
    .join('\n');
  // 엑셀에서 한글이 깨지지 않도록 BOM(\uFEFF)을 앞에 붙인다
  const url = URL.createObjectURL(new Blob([String.fromCharCode(0xfeff) + csv], { type: 'text/csv;charset=utf-8' }));
  const link = document.createElement('a');
  link.href = url;
  link.download = 'audit-log.csv';
  link.click();
  URL.revokeObjectURL(url);
}

export default function AdminPage() {
  const [period, setPeriod] = useState('최근 30일');
  const [updatedAt, setUpdatedAt] = useState(formatNow); // 마지막 갱신 시각
  const [notice, setNotice] = useState(''); // 서버 연결 전 기능 안내
  // 감사 로그 필터: 실행자, 작업 종류, 검색어
  const [actorFilter, setActorFilter] = useState('');
  const [actionFilter, setActionFilter] = useState('');
  const [keyword, setKeyword] = useState('');

  // 안내 문구는 4초 뒤 자동으로 지운다
  useEffect(() => {
    if (!notice) return undefined;
    const timer = setTimeout(() => setNotice(''), 4000);
    return () => clearTimeout(timer);
  }, [notice]);

  const actors = [...new Set(auditLogs.map((log) => log.actor))];
  const actions = [...new Set(auditLogs.map((log) => log.action))];

  // 세 조건을 모두 만족하는 로그만 보여 준다 (빈 값이면 조건 없음)
  const filteredLogs = auditLogs.filter((log) => {
    const text = `${log.actor} ${log.action} ${log.target}`.toLowerCase();
    return (
      (!actorFilter || log.actor === actorFilter) &&
      (!actionFilter || log.action === actionFilter) &&
      (!keyword.trim() || text.includes(keyword.trim().toLowerCase()))
    );
  });

  // 아직 연결할 화면·API가 없는 버튼은 안내만 한다
  function showPending(label) {
    setNotice(`${label}은(는) 서버 연결 후 사용할 수 있습니다.`);
  }

  function handleRefresh() {
    setUpdatedAt(formatNow());
    setNotice('예시 데이터를 다시 표시했습니다.');
  }

  return (
    <div className="admin-page">
      <header className="admin-heading">
        <div>
          <div className="admin-title-row">
            <h1>관리자 대시보드</h1>
            <span className="admin-example-badge">예시 데이터</span>
          </div>
          <p>데이터 파이프라인, 모델, 서비스 API와 운영 이력을 실시간으로 확인합니다.</p>
        </div>
        <div className="admin-heading-side">
          <label className="admin-period">
            <span>조회 기간</span>
            <select value={period} onChange={(event) => setPeriod(event.target.value)}>
              {PERIOD_OPTIONS.map((option) => (
                <option key={option}>{option}</option>
              ))}
            </select>
          </label>
          <span className="admin-updated">마지막 갱신 {updatedAt}</span>
        </div>
      </header>

      {/* 운영 요약 */}
      <section className="admin-summary" aria-label="운영 요약">
        {summaryCards.map((card) => (
          <article className={card.tone === 'good' ? 'admin-stat is-good' : 'admin-stat'} key={card.label}>
            <span>{card.label}</span>
            <strong>{card.value}</strong>
            <small>{card.note}</small>
          </article>
        ))}
      </section>

      {/* 데이터 파이프라인 + 모델 성능 */}
      <div className="admin-grid-2">
        <section className="admin-card" aria-labelledby="admin-pipeline-title">
          <div className="admin-card-heading">
            <div>
              <h2 id="admin-pipeline-title">데이터 수집·전처리·DB 적재</h2>
              <p>정기 작업의 최신 실행 상태</p>
            </div>
            <button className="admin-text-button" type="button" onClick={() => showPending('작업 상세')}>
              작업 상세
            </button>
          </div>

          <ul className="admin-pipeline">
            {pipelineSteps.map((step) => {
              const percent = Math.round((step.done / step.total) * 100);
              return (
                <li key={step.label}>
                  <div className="admin-pipeline-label">
                    <span>{step.label}</span>
                    <strong>
                      {step.done.toLocaleString()} / {step.total.toLocaleString()}
                    </strong>
                  </div>
                  <div
                    className={`admin-progress is-${step.tone}`}
                    role="progressbar"
                    aria-label={`${step.label} 진행률`}
                    aria-valuemin={0}
                    aria-valuemax={100}
                    aria-valuenow={percent}
                  >
                    <span style={{ width: `${percent}%` }} />
                  </div>
                </li>
              );
            })}
          </ul>

          <div className="admin-warning-box">
            <strong>{pipelineWarning.title}</strong>
            <p>{pipelineWarning.message}</p>
          </div>
        </section>

        <section className="admin-card" aria-labelledby="admin-model-title">
          <div className="admin-card-heading">
            <div>
              <h2 id="admin-model-title">모델 버전과 성능</h2>
              <p>
                Production {modelInfo.production} · {modelInfo.deployedAt} 배포
              </p>
            </div>
            <button className="admin-text-button" type="button" onClick={() => showPending('모델 관리')}>
              모델 관리
            </button>
          </div>

          <ModelMetricChart
            metrics={modelMetrics}
            previousLabel={modelInfo.previous}
            currentLabel={modelInfo.production}
          />

          <div className="admin-score-cards">
            {modelScoreCards.map((card) => (
              <div className={card.highlight ? 'admin-score is-good' : 'admin-score'} key={card.label}>
                <span>{card.label}</span>
                <strong>{card.value}</strong>
              </div>
            ))}
          </div>
        </section>
      </div>

      {/* 서비스 연동 상태 */}
      <section aria-labelledby="admin-service-title">
        <div className="admin-section-heading">
          <h2 id="admin-service-title">서비스 연동 상태</h2>
          <p>외부에서 내부까지 요청 경로의 상태를 확인합니다.</p>
        </div>
        <div className="admin-services">
          {services.map((service) => {
            const Icon = SERVICE_ICONS[service.id];
            const isOk = service.status === 'ok';
            return (
              <article className="admin-card admin-service" key={service.id}>
                <div className="admin-service-top">
                  <span className="admin-icon-box" aria-hidden="true">
                    <Icon size={theme.iconSize.md} />
                  </span>
                  <span className={isOk ? 'admin-status is-ok' : 'admin-status is-check'}>
                    {isOk ? '정상' : '점검'}
                  </span>
                </div>
                <h3>{service.name}</h3>
                <p>{service.detail}</p>
              </article>
            );
          })}
        </div>
      </section>

      {/* 재학습·배포 이력 + 관리 바로가기 */}
      <div className="admin-grid-deploy">
        <section className="admin-card" aria-labelledby="admin-deploy-title">
          <div className="admin-card-heading">
            <div>
              <h2 id="admin-deploy-title">재학습·배포 이력</h2>
              <p>최근 작업과 롤백 기록</p>
            </div>
            <button className="admin-text-button" type="button" onClick={() => showPending('전체 이력')}>
              전체 이력
            </button>
          </div>
          <div className="admin-table-wrap">
            <table className="admin-table">
              <thead>
                <tr>
                  <th scope="col">시각</th>
                  <th scope="col">버전</th>
                  <th scope="col">작업</th>
                  <th scope="col">상태</th>
                  <th scope="col">실행자</th>
                </tr>
              </thead>
              <tbody>
                {deployments.map((row) => (
                  <tr key={row.id}>
                    <td>{row.time}</td>
                    <td>{row.version}</td>
                    <td>{row.task}</td>
                    <td className={row.status === 'success' ? 'admin-result-success' : 'admin-result-rollback'}>
                      {row.status === 'success' ? '성공' : '롤백'}
                    </td>
                    <td>{row.actor}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>

        <div className="admin-management">
          {managementCards.map((card) => {
            const Icon = MANAGEMENT_ICONS[card.id];
            return (
              <section className="admin-card admin-manage-card" key={card.id} aria-labelledby={`admin-${card.id}-title`}>
                <div className="admin-manage-top">
                  <Icon size={theme.iconSize.lg} strokeWidth={1.5} aria-hidden="true" />
                  <strong>{card.count}</strong>
                </div>
                <h2 id={`admin-${card.id}-title`}>{card.title}</h2>
                <p>{card.note}</p>
                <button className="admin-outline-button" type="button" onClick={() => showPending(card.title)}>
                  {card.action}
                </button>
              </section>
            );
          })}
        </div>
      </div>

      {/* 감사 로그 */}
      <section className="admin-card" aria-labelledby="admin-audit-title">
        <div className="admin-card-heading">
          <div>
            <h2 id="admin-audit-title">감사 로그</h2>
            <p>관리자 작업과 중요 시스템 접근을 변경 불가능한 이력으로 기록합니다.</p>
          </div>
          <button
            className="admin-text-button"
            type="button"
            onClick={() => downloadCsv(filteredLogs)}
            disabled={filteredLogs.length === 0}
          >
            CSV 내보내기
          </button>
        </div>

        <div className="admin-filters">
          <span className="admin-chip is-selected">오늘</span>
          <select
            className="admin-chip"
            aria-label="실행자"
            value={actorFilter}
            onChange={(event) => setActorFilter(event.target.value)}
          >
            <option value="">전체 관리자</option>
            {actors.map((actor) => (
              <option key={actor}>{actor}</option>
            ))}
          </select>
          <select
            className="admin-chip"
            aria-label="작업 종류"
            value={actionFilter}
            onChange={(event) => setActionFilter(event.target.value)}
          >
            <option value="">전체 작업</option>
            {actions.map((action) => (
              <option key={action}>{action}</option>
            ))}
          </select>
          <input
            className="admin-chip admin-search"
            type="search"
            placeholder="검색"
            aria-label="감사 로그 검색"
            value={keyword}
            onChange={(event) => setKeyword(event.target.value)}
          />
        </div>

        {filteredLogs.length === 0 ? (
          <p className="admin-empty">조건에 맞는 로그가 없습니다.</p>
        ) : (
          <div className="admin-table-wrap">
            <table className="admin-table admin-audit-table">
              <thead>
                <tr>
                  <th scope="col">시각</th>
                  <th scope="col">실행자</th>
                  <th scope="col">작업</th>
                  <th scope="col">대상</th>
                </tr>
              </thead>
              <tbody>
                {filteredLogs.map((log) => (
                  <tr key={log.id}>
                    <td>{log.time}</td>
                    <td><strong>{log.actor}</strong></td>
                    <td>{log.action}</td>
                    <td>{log.target}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>

      <div className="admin-actions">
        <button className="admin-outline-button" type="button" onClick={handleRefresh}>
          상태 새로고침
        </button>
        <button className="admin-primary-button" type="button" onClick={() => showPending('재학습 작업 시작')}>
          재학습 작업 시작
        </button>
      </div>

      {/* 안내 문구: 화면 아래에 잠깐 표시 (어느 위치의 버튼을 눌러도 보이도록) */}
      <p className={notice ? 'admin-notice is-visible' : 'admin-notice'} role="status">
        {notice}
      </p>
    </div>
  );
}
