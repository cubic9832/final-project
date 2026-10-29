import { useState } from 'react';
import { Navigate, useLocation, useNavigate } from 'react-router-dom';
import { ArrowLeft } from 'lucide-react';
import theme from '../../../../styles/theme.js';
import { calculateFinancialSummary } from '../../calculateFinancialSummary.js';
import { lifestyleSummary } from '../../lifestylePreferences.js';
import { candidateMoney } from './candidatePresentation.js';
import FinancialFlowHeader from '../../components/FinancialFlowHeader.jsx';
import CandidateComparisonTable from './CandidateComparisonTable.jsx';
import { buildRecommendationView, conditionSummary, selectComparisonViews } from './buildRecommendationView.js';
import RecommendationGrid from './RecommendationGrid.jsx';
import './FinancialRecommendationsPage.css';


export default function FinancialRecommendationsPage() {
  const { state } = useLocation();
  const navigate = useNavigate();
  const diagnosis = state?.diagnosis;
  const result = state?.result;
  const [comparisonIds, setComparisonIds] = useState(() => (state?.comparisonIds ?? []).slice(0, 3));
  const [visibleCount, setVisibleCount] = useState(3);
  if (!diagnosis?.values || result?.modelVersion !== 'candidate-v2' || !Array.isArray(result?.recommendations)) return <Navigate to="/financial" replace />;
  const totals = calculateFinancialSummary(diagnosis.values, diagnosis.loans ?? []);
  const candidates = result.recommendations.slice(0, 9);
  const views = buildRecommendationView({ ...result, recommendations: candidates });
  const additionalRows = [];
  for (let start = 3; start < Math.min(visibleCount, candidates.length); start += 3) additionalRows.push({ start, candidates: candidates.slice(start, Math.min(start + 3, visibleCount)) });
  const selectedViews = selectComparisonViews(views, comparisonIds);
  const conditionMessage = conditionSummary(result.evaluationSummary);
  const toggleComparison = id => setComparisonIds(previous => previous.includes(id) ? previous.filter(value => value !== id) : previous.length < 3 ? [...previous, id] : previous);
  function openComparison() {
    if (!selectedViews) return;
    const query = new URLSearchParams({ source: 'financial' });
    comparisonIds.forEach(id => query.append('vehicle', id));
    navigate(`/vehicles/compare?${query}`, { state: { recommendationResult: result, diagnosis } });
  }

  return <div className={`financial-recommendations-page${views.length > 1 ? ' has-comparison-tray' : ''}`}>
    <FinancialFlowHeader current={4} title="내 예산에 맞는 추천 차량" description="예산과 취향에 맞는 차량을 비교해 보세요." />
    <button type="button" className="financial-recommendations-back" onClick={() => navigate('/financial/result', { state: { diagnosis, result, comparisonIds } })}>종합 분석 결과 보기</button>
    <section className="financial-recommendations-summary" aria-label="진단 결과 요약">
      <dl>
        <div><dt>차량 구매·유지에 사용할 예금</dt><dd>{candidateMoney(result.budgetPolicy?.availablePurchaseFunds ?? Math.max(0, Number(diagnosis.assets?.deposit || 0) * 10000))}</dd></div>
        <div><dt>월 유지비 가용액</dt><dd>{candidateMoney(totals.available * 10000)}</dd></div>
        <div><dt>내 차량 취향</dt><dd className="lifestyle-summary-text">{lifestyleSummary(diagnosis.vehicle)}</dd></div>
      </dl>
    </section>
    {views.length > 1 && <aside className="candidate-comparison-tray" aria-label="선택 차량 비교">
      <div className="candidate-comparison-tray-content"><strong aria-live="polite">비교 차량 {comparisonIds.length} / 3대</strong>
      <p>{comparisonIds.length === 3 ? '최대 3대를 선택했어요. 다른 차량을 넣으려면 선택을 해제해 주세요.' : '카드에서 2~3대를 선택하면 가격·유지비·조건을 나란히 비교할 수 있어요.'}</p>
      <div className="candidate-comparison-chips">{views.filter(view => comparisonIds.includes(view.id)).map(view => <button type="button" key={view.id} onClick={() => toggleComparison(view.id)} aria-label={`${view.candidate.vehicle.model} 비교 선택 해제`}>{view.candidate.vehicle.model} · 선택 해제</button>)}</div></div>
      <button type="button" className="financial-next-button" disabled={!selectedViews} onClick={openComparison}>선택한 {comparisonIds.length}대 비교하기</button>
    </aside>}

    <section className="candidate-decision-summary" aria-labelledby="decision-summary-title">
      <h2 id="decision-summary-title">선택하신 조건으로 비교했어요</h2>
      <p>{diagnosis.vehicle?.scenarioMode ? '예산과 탑승 인원을 먼저 확인하고, 비용 성향·차체·연료·크기와 주행·충전 여건을 반영했습니다.' : '예산과 탑승 인원을 먼저 확인하고, 선택하신 디자인·가속·차체·연료·크기 선호를 반영했습니다.'}</p>
      {conditionMessage && <p className="candidate-condition-summary">{conditionMessage}</p>}
    </section>
    <section id="recommended-vehicles" aria-label="추천 차량 목록">
      <div className="financial-recommendations-list-heading"><h2>상위 추천 차량</h2><span>추천 후보 총 {candidates.length}대 · 최대 9대</span></div>
      {candidates.length ? <RecommendationGrid candidates={candidates.slice(0, 3)} preferences={diagnosis.vehicle} views={views} comparisonIds={comparisonIds} onToggleComparison={toggleComparison} /> : <div className="financial-recommendations-empty"><h2>추천 가능한 차량이 없습니다.</h2><p>구매 예산·월 유지비와 최소 탑승 인원을 충족하는 차량이 없습니다. 조건을 조정하거나 아래 사양 확인 필요 후보를 확인해 주세요.</p></div>}
    </section>
    {candidates.length > 3 && <section aria-labelledby="additional-candidates-title">
      <div className="financial-recommendations-list-heading"><h2 id="additional-candidates-title">다른 추천 후보</h2><span>4위부터 최대 9위까지</span></div>
      <p>구매 예산과 월 유지비 조건을 충족한 대안입니다. 비교 선택은 전체 후보 중 최대 3대까지 가능하며, 다른 차량을 선택하려면 기존 선택을 해제해 주세요.</p>
      <div id="additional-candidates" className="candidate-additional-rows">{additionalRows.map(row => <RecommendationGrid key={row.start} candidates={row.candidates} rankOffset={row.start} preferences={diagnosis.vehicle} views={views} comparisonIds={comparisonIds} onToggleComparison={toggleComparison} />)}</div>
      {visibleCount < candidates.length && <button type="button" className="candidate-open-comparison" aria-controls="additional-candidates" aria-expanded={visibleCount > 3} onClick={() => setVisibleCount(count => Math.min(9, count + 3))}>다른 추천 후보 {Math.min(3, candidates.length - visibleCount)}대 더 보기 ({Math.min(visibleCount, candidates.length)}/{candidates.length})</button>}
      {visibleCount >= candidates.length && <p role="status">추천 후보 {candidates.length}대를 모두 표시했어요.{candidates.length === 9 ? ' 화면에는 최대 9대까지 제공합니다.' : ' 현재 재무 조건과 최소 인원을 충족하는 다른 모델은 없어요.'}</p>}
      {visibleCount > 3 && <button type="button" className="financial-recommendations-back" onClick={() => setVisibleCount(3)}>추가 후보 접기</button>}
    </section>}
    {result.conditionalRecommendations?.length > 0 && <section aria-label="사양 확인 필요 후보">
      <div className="financial-recommendations-list-heading"><h2>사양 확인 필요 후보</h2><span>총 {result.conditionalRecommendations.length}대</span></div>
      <p>재무 조건을 충족한 차량입니다. 승차 정원·전장이 미확인이거나 좌석 사양 선택이 필요해 일반 추천 목록에는 포함하지 않았습니다.</p>
      <RecommendationGrid candidates={result.conditionalRecommendations} preferences={diagnosis.vehicle} />
    </section>}
    {views.length > 1 && <section className="candidate-comparison-section" aria-labelledby="candidate-comparison-title">
      <div className="financial-recommendations-list-heading"><h2 id="candidate-comparison-title">무엇을 얻고, 무엇을 조정할까요?</h2><span>{comparisonIds.length}대 선택</span></div>
      <p>카드에서 2~3대를 선택해 같은 사양·비용·평가 근거로 비교하세요. 중요도가 높은 불일치부터 표시합니다.</p>
      {selectedViews ? <CandidateComparisonTable views={selectedViews} /> : <p className="candidate-condition-note">비교할 차량을 2대 이상 선택해 주세요.</p>}
      <button type="button" className="candidate-open-comparison" disabled={!selectedViews} onClick={openComparison}>선택한 차량 비교 화면 열기</button>
    </section>}

    <div className="financial-next-row">
      <button type="button" className="financial-previous-button" onClick={() => navigate('/financial/result', { state: { diagnosis, result, comparisonIds } })}><ArrowLeft size={theme.iconSize.sm} aria-hidden="true" />종합 분석 결과</button>
      <button type="button" className="financial-next-button" onClick={() => navigate('/financial/vehicle', { state: diagnosis })}>차량 취향 수정</button>
    </div>
  </div>;
}
