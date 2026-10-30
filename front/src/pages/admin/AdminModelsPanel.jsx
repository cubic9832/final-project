import { useEffect, useState } from 'react';
import { Cpu, Database, History } from 'lucide-react';
import theme from '../../styles/theme';
import ModelMetricChart from './ModelMetricChart';
import { formatLogTime } from './adminLogFormat';
import { getModelReport, getModelServerInfo } from '../../features/admin/adminApi';

// 7단계 모델 관리 — 모두 실제 값 (10-27: 고정 예시 값을 바꿈)
// 학습 · 평가 결과 = 조원(ML)이 git 에 올린 학습 결과 파일을 서버가 읽은 것 (GET /admin/model-report)
// 적용 중인 버전 · 후보 차량 수 = 추천 서버가 지금 응답하는 값, 모델 버전 기록 = DB(model_versions)
const percent = (value) => `${(value * 100).toFixed(1)}%`;
const count = (value) => (value == null ? '-' : value.toLocaleString('ko-KR'));

export default function AdminModelsPanel() {
  const [report, setReport] = useState(); // undefined 불러오는 중 · null 실패
  const [server, setServer] = useState();
  useEffect(() => {
    const controller = new AbortController();
    getModelReport(controller.signal).then(setReport).catch(() => !controller.signal.aborted && setReport(null));
    getModelServerInfo(controller.signal).then(setServer).catch(() => !controller.signal.aborted && setServer(null));
    return () => controller.abort();
  }, []);

  if (report === undefined) return <p className="admin-empty" role="status">모델 정보를 불러오는 중…</p>;
  if (report === null) return <p className="admin-empty" role="alert">모델 정보를 불러오지 못했습니다.</p>;

  const split = report.splitProfiles;
  return <div className="admin-panel-stack">
    <div className="admin-grid-2">
      <section className="admin-card"><div className="admin-card-heading"><div><h3>현재 적용 모델</h3><p>추천 서버가 지금 쓰는 모델과 학습 정보</p></div><Cpu size={theme.iconSize.md} aria-hidden="true" /></div>
        <div className="admin-model-version"><strong>{server ? server.info.modelVersion : report.runName ?? '-'}</strong>
          <span className={`admin-status ${server ? 'is-ok' : 'is-check'}`}>{server === undefined ? '확인 중' : server ? '적용 중' : '추천 서버 연결 안 됨'}</span></div>
        <dl className="admin-detail-list">
          <div><dt>학습 결과 폴더</dt><dd>{report.runName ?? '-'}</dd></div>
          <div><dt>입력 구조</dt><dd>{report.schema ?? '-'}</dd></div>
          <div><dt>학습일</dt><dd>{report.trainedAt ? formatLogTime(report.trainedAt) : '-'}</dd></div>
          <div><dt>추천 후보 차량</dt><dd>{server ? `${count(server.info.catalogCount)}건 · 차종 ${server.info.modelNames}개` : '-'}</dd></div>
          <div><dt>학습 데이터</dt><dd>{report.available ? `가상 가구 ${count(report.profiles)} (학습 ${count(split?.train)} · 검증 ${count(split?.validation)} · 시험 ${count(split?.test)})` : '-'}</dd></div>
          <div><dt>처음 보는 차종 평가</dt><dd>{report.heldOutModels != null ? `${report.heldOutModels}개 차종을 학습에서 빼고 평가` : '-'}</dd></div>
          <div><dt>시험 비교 정확도</dt><dd>{report.testPairAccuracy != null ? percent(report.testPairAccuracy) : '-'}</dd></div>
          <div><dt>재무 조건 위반 추천</dt><dd>{report.financialViolations != null ? `${report.financialViolations}건` : '-'}</dd></div>
        </dl>
        {!report.available && <p className="admin-empty" role="alert">학습 결과 파일을 찾지 못했습니다 (ml/outputs/models/…).</p>}
      </section>
      <section className="admin-card"><div className="admin-card-heading"><div><h3>모델 성능 비교</h3><p>이전 모델 대비 상위 3대 추천 지표 (0~1, 높을수록 좋음)</p></div></div>
        {report.metrics.length > 0
          ? <ModelMetricChart metrics={report.metrics} previousLabel="이전 모델" currentLabel="현재 모델" />
          : <p className="admin-empty">비교 지표가 없습니다.</p>}
        {/* 학습 파일의 설명(영문, 예: "synthetic teacher agreement, not observed user satisfaction")을 한국어로 풀어 쓴다 */}
        {report.meaning && <p className="admin-empty" title={report.meaning}>평가 기준: 가상 가구 데이터로 만든 정답과의 일치도이며, 실제 사용자 만족도는 아닙니다.</p>}
      </section>
    </div>
    <section className="admin-card"><div className="admin-card-heading"><div><h3>학습 기록</h3><p>에포크(학습 반복)별 손실과 검증 비교 정확도</p></div><History size={theme.iconSize.md} aria-hidden="true" /></div>
      {report.history.length === 0 ? <p className="admin-empty">학습 기록이 없습니다.</p> : <div className="admin-table-wrap"><table className="admin-table"><caption className="admin-sr-only">에포크별 학습 기록</caption>
        <thead><tr><th scope="col">에포크</th><th scope="col">손실</th><th scope="col">검증 비교 정확도</th></tr></thead>
        <tbody>{report.history.map(row => <tr key={row.epoch}><td><strong>{row.epoch}</strong></td><td>{row.loss.toFixed(4)}</td><td>{percent(row.validationPairAccuracy)}</td></tr>)}</tbody></table></div>}
    </section>
    <section className="admin-card"><div className="admin-card-heading"><div><h3>모델 버전 기록</h3><p>재무 진단을 저장할 때 쓰인 모델 버전 (DB)</p></div><Database size={theme.iconSize.md} aria-hidden="true" /></div>
      {report.versions.length === 0 ? <p className="admin-empty">아직 재무 진단에 쓰인 모델 버전이 없습니다.</p> : <div className="admin-table-wrap"><table className="admin-table"><caption className="admin-sr-only">모델 버전 기록</caption>
        <thead><tr><th scope="col">처음 쓰인 시각</th><th scope="col">버전</th><th scope="col">방식</th><th scope="col">저장된 재무 진단</th></tr></thead>
        <tbody>{report.versions.map(row => <tr key={row.versionLabel}><td>{formatLogTime(row.createdAt)}</td><td><strong>{row.versionLabel}</strong></td><td>{row.executionType}</td><td>{row.diagnoses}건</td></tr>)}</tbody></table></div>}
    </section>
  </div>;
}
