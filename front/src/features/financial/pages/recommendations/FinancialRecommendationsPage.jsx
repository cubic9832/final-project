import { useState } from 'react';
import { Navigate, useLocation, useNavigate } from 'react-router-dom';
import { ArrowLeft } from 'lucide-react';
import theme from '../../../../styles/theme.js';
import { calculateFinancialSummary } from '../../calculateFinancialSummary.js';
import { candidateMoney } from './candidatePresentation.js';
import FinancialFlowHeader from '../../components/FinancialFlowHeader.jsx';
import CandidateComparisonTable from './CandidateComparisonTable.jsx';
import { buildRecommendationView, conditionSummary, selectComparisonViews, evaluationLabels } from './buildRecommendationView.js';
import RecommendationGrid from './RecommendationGrid.jsx';
import './FinancialRecommendationsPage.css';

const exclusionLabels = { 'purchase-price-ceiling': '구매가격 상한 초과', 'insufficient-cash-for-outright-purchase': '일시불 자금 부족', 'insufficient-monthly-buffer': '월 여유자금 부족' };

export default function FinancialRecommendationsPage() {
  const { state } = useLocation();
  const navigate = useNavigate();
  const diagnosis = state?.diagnosis;
  const result = state?.result;
  const [comparisonIds, setComparisonIds] = useState(() => (state?.comparisonIds ?? []).slice(0, 3));
  const [visibleCount, setVisibleCount] = useState(3);
  if (!diagnosis?.values || result?.modelVersion !== 'candidate-v2' || !Array.isArray(result?.recommendations)) return <Navigate to="/financial" replace />;
  const totals = calculateFinancialSummary(diagnosis.values, diagnosis.loans ?? []);
  const assumptions = result.assumptions;
  const candidates = result.recommendations.slice(0, 9);
  const views = buildRecommendationView({ ...result, recommendations: candidates });
  const additionalRows = [];
  for (let start = 3; start < Math.min(visibleCount, candidates.length); start += 3) additionalRows.push({ start, candidates: candidates.slice(start, Math.min(start + 3, visibleCount)) });
  const selectedViews = selectComparisonViews(views, comparisonIds);
  const conditionMessage = conditionSummary(result.evaluationSummary);
  const applied = result.recommendations[0]?.integratedScore?.components ?? [];
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
        <div><dt>내 차량 취향</dt><dd>{diagnosis.vehicle?.fuel || '상관없음'}</dd></div>
      </dl>
    </section>
    {views.length > 1 && <aside className="candidate-comparison-tray" aria-label="선택 차량 비교">
      <div className="candidate-comparison-tray-content"><strong aria-live="polite">비교 차량 {comparisonIds.length} / 3대</strong>
      <p>{comparisonIds.length === 3 ? '최대 3대를 선택했어요. 다른 차량을 넣으려면 선택을 해제해 주세요.' : '카드에서 2~3대를 선택하면 가격·유지비·조건을 나란히 비교할 수 있어요.'}</p>
      <div className="candidate-comparison-chips">{views.filter(view => comparisonIds.includes(view.id)).map(view => <button type="button" key={view.id} onClick={() => toggleComparison(view.id)} aria-label={`${view.candidate.vehicle.model} 비교 선택 해제`}>{view.candidate.vehicle.model} · 선택 해제</button>)}</div></div>
      <button type="button" className="financial-next-button" disabled={!selectedViews} onClick={openComparison}>선택한 {comparisonIds.length}대 비교하기</button>
    </aside>}

    <section className="candidate-decision-summary" aria-labelledby="decision-summary-title">
      <h2 id="decision-summary-title">이렇게 비교했어요</h2>
      <p>구매 자금과 유지비 충당 가능 여부를 확인하며, 연료·크기·정원는 적용한 중요도로 비교합니다.</p>
      <div className="candidate-applied-priorities">{applied.filter(item => ['cost', 'fuel', 'space', 'seating'].includes(item.key)).map(item => <span key={item.key}>{evaluationLabels[item.key]} · {item.weight >= 4 ? '높음' : item.weight >= 3 ? '보통' : '낮음'}</span>)}</div>
      {conditionMessage && <p className="candidate-condition-summary">{conditionMessage}</p>}
      {!result.evaluationSummary?.complete && <p>전체 후보의 선호 충족 집계가 없어, 현재 표시된 차량의 평가만 설명합니다.</p>}
      <p className="candidate-cost-definition">입력한 예금으로 차량 가격을 지불하는 기준이에요. 월 유지비에 할부금은 포함되지 않으며, 구매 가격에 취득·등록비와 보조금은 반영하지 않았어요.</p>
    </section>
    <section id="recommended-vehicles" aria-label="추천 차량 목록">
      <div className="financial-recommendations-list-heading"><h2>상위 추천 차량</h2><span>추천 후보 총 {candidates.length}대 · 최대 9대</span></div>
      {candidates.length ? <RecommendationGrid candidates={candidates.slice(0, 3)} preferences={diagnosis.vehicle} views={views} comparisonIds={comparisonIds} onToggleComparison={toggleComparison} /> : <div className="financial-recommendations-empty"><h2>추천 가능한 차량이 없습니다.</h2><p>구매 후 남는 예금으로 부족한 월 자금을 12개월 충당하는 조건까지 확인했지만 추천 가능한 차량이 없습니다. 구매자금과 월 유지비 여력을 확인해 주세요.</p></div>}
    </section>
    {candidates.length > 3 && <section aria-labelledby="additional-candidates-title">
      <div className="financial-recommendations-list-heading"><h2 id="additional-candidates-title">다른 추천 후보</h2><span>4위부터 최대 9위까지</span></div>
      <p>구매 예산과 월 유지비 조건을 충족한 대안입니다. 비교 선택은 전체 후보 중 최대 3대까지 가능하며, 다른 차량을 선택하려면 기존 선택을 해제해 주세요.</p>
      <div id="additional-candidates" className="candidate-additional-rows">{additionalRows.map(row => <RecommendationGrid key={row.start} candidates={row.candidates} rankOffset={row.start} preferences={diagnosis.vehicle} views={views} comparisonIds={comparisonIds} onToggleComparison={toggleComparison} />)}</div>
      {visibleCount < candidates.length && <button type="button" className="candidate-open-comparison" aria-controls="additional-candidates" aria-expanded={visibleCount > 3} onClick={() => setVisibleCount(count => Math.min(9, count + 3))}>다른 추천 후보 {Math.min(3, candidates.length - visibleCount)}대 더 보기 ({Math.min(visibleCount, candidates.length)}/{candidates.length})</button>}
      {visibleCount >= candidates.length && <p role="status">추천 후보 {candidates.length}대를 모두 표시했어요.{candidates.length === 9 ? ' 화면에는 최대 9대까지 제공합니다.' : ' 현재 재무 조건을 충족하는 다른 모델은 없어요.'}</p>}
      {visibleCount > 3 && <button type="button" className="financial-recommendations-back" onClick={() => setVisibleCount(3)}>추가 후보 접기</button>}
    </section>}
    {result.conditionalRecommendations?.length > 0 && <section aria-label="사양 확인 필요 후보">
      <div className="financial-recommendations-list-heading"><h2>사양 확인 필요 후보</h2><span>총 {result.conditionalRecommendations.length}대</span></div>
      <p>재무 조건을 충족한 차량입니다. 승차 정원·전장이 미확인이거나 좌석 사양 선택이 필요해 적격 차량 수에는 포함하지 않았습니다.</p>
      <RecommendationGrid candidates={result.conditionalRecommendations} preferences={diagnosis.vehicle} />
    </section>}
    {views.length > 1 && <section className="candidate-comparison-section" aria-labelledby="candidate-comparison-title">
      <div className="financial-recommendations-list-heading"><h2 id="candidate-comparison-title">무엇을 얻고, 무엇을 조정할까요?</h2><span>{comparisonIds.length}대 선택</span></div>
      <p>카드에서 2~3대를 선택해 같은 사양·비용·평가 근거로 비교하세요. 중요도가 높은 불일치부터 표시합니다.</p>
      {selectedViews ? <CandidateComparisonTable views={selectedViews} /> : <p className="candidate-condition-note">비교할 차량을 2대 이상 선택해 주세요.</p>}
      <button type="button" className="candidate-open-comparison" disabled={!selectedViews} onClick={openComparison}>선택한 차량 비교 화면 열기</button>
    </section>}
    <details className="financial-recommendations-note"><summary>추천 기준과 비용 계산 안내</summary><div>
      <p>총 {result.catalogCount}개 사양 중 {result.eligibleCount}개가 재무 조건을 충족했습니다.</p>
      {result.budgetPolicy && <p>구매 가격 상한은 {candidateMoney(result.budgetPolicy.financialUpper)}입니다. 예산 상단의 차량에 별도 가점을 주지 않습니다. 구매 자금에 대출·할부는 포함하지 않습니다.</p>}
      <p>재무 조건을 충족한 서로 다른 모델을 최대 9개 제시합니다. 상위 3대 아래에서 나머지 후보를 펼쳐 볼 수 있습니다. 선호 인원이 부족하거나 제원이 미확인인 후보는 카드에 표시합니다. 크기 비교는 전장 기준이며 실제 정원과 판매 사양은 확인이 필요합니다.</p>
      {assumptions && <p>월 보험 {candidateMoney(assumptions.monthly_insurance)}, 정비 {candidateMoney(assumptions.monthly_maintenance)}, 세금 {candidateMoney(assumptions.monthly_tax)}에 주행거리 기반 에너지비를 더합니다. 실제 세금·보험 견적이 아닙니다.</p>}
      <p>차량 이미지는 예시이며 실제 연식·트림·색상과 다를 수 있습니다.</p>
      {Object.keys(result.excludedReasons ?? {}).length > 0 && <p>후보 제외 사유: {Object.entries(result.excludedReasons).map(([key, count]) => `${exclusionLabels[key] || key} ${count}건`).join(' · ')}. 한 사양에 여러 사유가 있을 수 있습니다.</p>}
    </div></details>
    <div className="financial-next-row">
      <button type="button" className="financial-previous-button" onClick={() => navigate('/financial/result', { state: { diagnosis, result, comparisonIds } })}><ArrowLeft size={theme.iconSize.sm} aria-hidden="true" />종합 분석 결과</button>
      <button type="button" className="financial-next-button" onClick={() => navigate('/financial/vehicle', { state: diagnosis })}>차량 취향 수정</button>
    </div>
  </div>;
}
