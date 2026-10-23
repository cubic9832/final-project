import { Navigate, useLocation, useNavigate } from 'react-router-dom';
import { ArrowLeft } from 'lucide-react';
import theme from '../../../../styles/theme.js';
import { calculateFinancialSummary } from '../../calculateFinancialSummary.js';
import { candidateMoney } from './candidatePresentation.js';
import RecommendationCard from './RecommendationCard.jsx';
import './FinancialRecommendationsPage.css';

const exclusionLabels = { 'purchase-price-ceiling': '구매가격 상한 초과', 'insufficient-cash-for-outright-purchase': '일시불 자금 부족', 'insufficient-monthly-buffer': '월 여유자금 부족' };

export default function FinancialRecommendationsPage() {
  const { state } = useLocation();
  const navigate = useNavigate();
  const diagnosis = state?.diagnosis;
  const result = state?.result;
  if (!diagnosis?.values || result?.modelVersion !== 'candidate-v2' || !Array.isArray(result?.recommendations)) return <Navigate to="/financial" replace />;
  const totals = calculateFinancialSummary(diagnosis.values, diagnosis.loans ?? []);
  const assumptions = result.assumptions;

  return <div className="financial-recommendations-page">
    <button type="button" className="financial-recommendations-back" onClick={() => navigate('/financial/result', { state: diagnosis })}>
      <ArrowLeft size={theme.iconSize.sm} aria-hidden="true" />분석 결과로 돌아가기
    </button>
    <header className="financial-recommendations-heading">
      <span>재무 진단 기반 추천</span><h1>내 예산에 맞는 추천 차량</h1>
      <p>구매 자금과 월 유지비를 확인하고, 입력한 취향에 맞춰 골랐어요.</p>
    </header>
    <section className="financial-recommendations-summary" aria-label="진단 결과 요약">
      <dl>
        <div><dt>차량 구매 가능 자금</dt><dd>{candidateMoney(result.budgetPolicy?.financialUpper ?? Math.max(0, Number(diagnosis.assets?.deposit || 0) * 10000))}</dd></div>
        <div><dt>월 유지비 가용액</dt><dd>{candidateMoney(totals.available * 10000)}</dd></div>
        <div><dt>내 차량 취향</dt><dd>{diagnosis.vehicle?.fuel || '상관없음'} · {diagnosis.vehicle?.purpose || '미입력'}</dd></div>
      </dl>
    </section>

    <section aria-label="추천 차량 목록">
      <div className="financial-recommendations-list-heading"><h2>추천 차량</h2><span>총 {result.recommendations.length}대</span></div>
      {result.recommendations.length ? <ol className="financial-recommendations-grid">{result.recommendations.map((vehicle, index) =>
        <RecommendationCard key={vehicle.vehicle.id} candidate={vehicle} rank={index + 1} preferences={diagnosis.vehicle} />)}
      </ol> : <div className="financial-recommendations-empty"><h2>추천 가능한 차량이 없습니다.</h2><p>현재 예금으로 구매할 수 있고 월 유지비를 감당할 수 있는 차량이 없습니다. 구매자금과 월 유지비 여력을 확인해 주세요.</p></div>}
    </section>
    {result.conditionalRecommendations?.length > 0 && <section aria-label="사양 확인 필요 후보">
      <div className="financial-recommendations-list-heading"><h2>사양 확인 필요 후보</h2><span>총 {result.conditionalRecommendations.length}대</span></div>
      <p>재무 조건을 충족한 차량입니다. 승차 정원·전장이 미확인이거나 좌석 사양 선택이 필요해 적격 차량 수에는 포함하지 않았습니다.</p>
      <ol className="financial-recommendations-grid">{result.conditionalRecommendations.map((candidate, index) => <RecommendationCard key={candidate.vehicle.id} candidate={candidate} rank={index + 1} preferences={diagnosis.vehicle} />)}</ol>
    </section>}
    <details className="financial-recommendations-note"><summary>추천 기준과 비용 계산 안내</summary><div>
      <p>총 {result.catalogCount}개 사양 중 {result.eligibleCount}개가 재무 조건을 충족했습니다.</p>
      {result.budgetPolicy && <p>우선 추천 가격대는 {candidateMoney(result.budgetPolicy.lower)} ~ {candidateMoney(result.budgetPolicy.upper)}입니다. 구간에 후보가 부족하면 낮은 가격대로 확대합니다. 구매 자금에 대출·할부는 포함하지 않습니다.</p>}
      <p>재무 조건을 충족한 서로 다른 모델을 최대 3개 제시합니다. 선호 인원이 부족하거나 제원이 미확인인 후보는 카드에 표시합니다. 크기 비교는 전장 기준이며 실제 정원과 판매 사양은 확인이 필요합니다.</p>
      {assumptions && <p>월 보험 {candidateMoney(assumptions.monthly_insurance)}, 정비 {candidateMoney(assumptions.monthly_maintenance)}, 세금 {candidateMoney(assumptions.monthly_tax)}에 주행거리 기반 에너지비를 더합니다. 실제 세금·보험 견적이 아닙니다.</p>}
      <p>차량 이미지는 예시이며 실제 연식·트림·색상과 다를 수 있습니다.</p>
      {Object.keys(result.excludedReasons ?? {}).length > 0 && <p>후보 제외 사유: {Object.entries(result.excludedReasons).map(([key, count]) => `${exclusionLabels[key] || key} ${count}건`).join(' · ')}. 한 사양에 여러 사유가 있을 수 있습니다.</p>}
    </div></details>
    <div className="financial-recommendations-actions">
      <button type="button" className="financial-recommendations-secondary" onClick={() => navigate('/financial/result', { state: diagnosis })}>재무 분석 다시 보기</button>
      <button type="button" className="financial-recommendations-primary" onClick={() => navigate('/financial', { state: { ...diagnosis, reviewReturn: false } })}>진단 조건 수정하기</button>
    </div>
  </div>;
}
