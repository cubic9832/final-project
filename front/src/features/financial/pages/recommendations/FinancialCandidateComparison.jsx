import { Link } from 'react-router-dom';
import { isFinancialRecommendationResult } from '../../isFinancialRecommendationResult.js';
import CandidateComparisonTable from './CandidateComparisonTable.jsx';
import FinancialFlowHeader from '../../components/FinancialFlowHeader.jsx';
import { buildRecommendationView, selectComparisonViews } from './buildRecommendationView.js';
import './FinancialRecommendationsPage.css';

export default function FinancialCandidateComparison({ result, diagnosis, selectedIds }) {
  const views = isFinancialRecommendationResult(result) ? buildRecommendationView(result) : [];
  const selected = selectComparisonViews(views, selectedIds);
  if (!selected || !diagnosis?.values) return <section className="financial-recommendations-empty">
    <h1>추천 비교 정보를 확인할 수 없습니다.</h1><p>선택한 차량 정보를 찾을 수 없어요. 추천 결과에서 차량을 다시 선택해 주세요.</p>
    <Link to="/financial">재무 정보 입력하기</Link>
  </section>;
  return <div className="financial-recommendations-page">
    <FinancialFlowHeader current={5} title="내 조건에서 선택지를 비교해 보세요" description="추천 결과와 동일한 차량 사양과 예상 비용으로 비교합니다. 일시불 구매 기준이에요." />
    <CandidateComparisonTable views={selected} />
    <div className="financial-recommendations-actions">
      <Link className="candidate-open-comparison" to="/financial/recommendations" state={{ diagnosis, result, comparisonIds: selectedIds }}>추천 결과로 돌아가기</Link>
      <Link className="candidate-open-comparison" to="/financial/vehicle" state={diagnosis}>차량 취향 수정하기</Link>
    </div>
  </div>;
}
