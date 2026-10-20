import { Navigate, useLocation, useNavigate } from 'react-router-dom';
import { ArrowLeft } from 'lucide-react';
import theme from '../../../../styles/theme.js';
import { calculateFinancialSummary } from '../../calculateFinancialSummary.js';
import { candidateMoney } from './candidatePresentation.js';
import RecommendationCard from './RecommendationCard.jsx';
import './FinancialRecommendationsPage.css';

const exclusionLabels = { 'charging-unavailable': '충전 조건 미충족', 'insufficient-cash-for-outright-purchase': '일시불 자금 부족', 'insufficient-monthly-buffer-under-stress': '비용 상승 시 월 여유자금 부족' };

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
      <span>재무 진단 기반 추천</span><h1>내 조건으로 찾은 차량 후보</h1>
      <p>목표 저축과 비상 자금을 유지하고 비용 상승 조건에서도 월 여유자금이 남는 차량 후보입니다. 비용·선호 순위는 실험 모델의 참고 결과입니다.</p>
    </header>
    <section className="financial-recommendations-summary" aria-label="진단 결과 요약">
      <dl>
        <div><dt>주 이용목적</dt><dd>{diagnosis.vehicle?.purpose || '미입력'}</dd></div>
        <div><dt>월 가용자금</dt><dd>{candidateMoney(totals.available * 10000)}</dd></div>
        <div><dt>검토한 가격 사양</dt><dd>{result.catalogCount}개 중 {result.eligibleCount}개 적격</dd></div>
      </dl>
    </section>
    <section aria-label="추천 차량 목록">
      <div className="financial-recommendations-list-heading"><h2>추천 차량</h2><span>총 {result.recommendations.length}대</span></div>
      {result.recommendations.length ? <ol className="financial-recommendations-grid">{result.recommendations.map((vehicle, index) =>
        <RecommendationCard key={vehicle.vehicle.id} candidate={vehicle} rank={index + 1} />)}
      </ol> : <div className="financial-recommendations-empty"><h2>추천 가능한 차량이 없습니다.</h2><p>입력한 자금과 비용 상승 조건을 만족하는 후보가 없습니다. 선수금·저축·할부 기간·충전 조건을 확인하고 다시 추천받아 보세요.</p></div>}
    </section>
    <aside className="financial-recommendations-note"><h2>추천 결과를 확인할 때</h2>
      <p>합성 효용으로 학습한 실험 추천이며 실제 만족도·구매 확률을 뜻하지 않습니다. 자동 추출한 가격 스냅샷이므로 최신 가격·판매 여부·좌석·안전 사양을 별도로 확인하세요.</p>
      {assumptions && <p>기본 금리 연 6%, 취득부대비 {Number((assumptions.acquisition_ratio * 100).toFixed(2))}% 가정. 월 보험 {candidateMoney(assumptions.monthly_insurance)}, 정비 {candidateMoney(assumptions.monthly_maintenance)}, 세금 {candidateMoney(assumptions.monthly_tax)}에 주행거리 기반 에너지비를 더합니다. 비용 상승 시 금리 +{assumptions.stress_rate_addition * 100}%p, 유지비 {assumptions.stress_running_multiplier}배를 적용합니다. 실제 세금·보험 견적이 아닙니다.</p>}
      <p>차량 이미지는 예시이며 실제 연식·트림·색상과 다를 수 있습니다.</p>
      {Object.keys(result.excludedReasons ?? {}).length > 0 && <p>후보 제외 사유: {Object.entries(result.excludedReasons).map(([key, count]) => `${exclusionLabels[key] || key} ${count}건`).join(' · ')}. 한 사양에 여러 사유가 있을 수 있습니다.</p>}
    </aside>
    <div className="financial-recommendations-actions">
      <button type="button" className="financial-recommendations-secondary" onClick={() => navigate('/financial/result', { state: diagnosis })}>재무 분석 다시 보기</button>
      <button type="button" className="financial-recommendations-primary" onClick={() => navigate('/financial', { state: { ...diagnosis, reviewReturn: false } })}>진단 조건 수정하기</button>
    </div>
  </div>;
}
