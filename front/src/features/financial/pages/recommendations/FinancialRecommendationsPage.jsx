import { Navigate, useLocation, useNavigate } from 'react-router-dom';
import { ArrowLeft } from 'lucide-react';
import theme from '../../../../styles/theme.js';
import { calculateVehicleBudget } from '../../calculateVehicleBudget.js';
import RecommendationCard from './RecommendationCard.jsx';
import './FinancialRecommendationsPage.css';

const money = (amount) => `${Math.floor(amount).toLocaleString('ko-KR')}만 원`;

export default function FinancialRecommendationsPage() {
  const { state } = useLocation();
  const navigate = useNavigate();
  const diagnosis = state?.diagnosis;
  const result = state?.result;
  if (!diagnosis?.values || !Array.isArray(result?.recommendations)) return <Navigate to="/financial" replace />;
  const budget = calculateVehicleBudget(diagnosis);

  return <div className="financial-recommendations-page">
    <button type="button" className="financial-recommendations-back" onClick={() => navigate('/financial/result', { state: diagnosis })}>
      <ArrowLeft size={theme.iconSize.sm} aria-hidden="true" />분석 결과로 돌아가기
    </button>
    <header className="financial-recommendations-heading">
      <span>재무 진단 기반 추천</span><h1>내 조건으로 찾은 차량 후보</h1>
      <p>진단에서 입력하신 정보를 바탕으로 추천한 차량입니다. 후보별 특징을 살펴보세요.</p>
    </header>
    <section className="financial-recommendations-summary" aria-label="추천에 사용한 진단 요약">
      <dl>
        <div><dt>주 이용목적</dt><dd>{diagnosis.vehicle?.purpose || '미입력'}</dd></div>
        <div><dt>월 가용자금</dt><dd>{money(budget.available)}</dd></div>
        <div><dt>예상 차량 예산</dt><dd>{budget.valid ? `${money(budget.low)} ~ ${money(budget.high)}` : '입력 정보 확인 필요'}</dd></div>
      </dl>
    </section>
    <section aria-label="추천 차량 목록">
      <div className="financial-recommendations-list-heading"><h2>추천 차량</h2><span>총 {result.recommendations.length}대</span></div>
      {result.recommendations.length ? <ol className="financial-recommendations-grid">{result.recommendations.map((vehicle, index) =>
        <RecommendationCard key={vehicle.labelCode} vehicle={vehicle} rank={index + 1} diagnosis={diagnosis} />)}
      </ol> : <div className="financial-recommendations-empty"><h2>추천 가능한 차량이 없습니다.</h2><p>진단 조건을 확인하고 다시 추천받아 보세요.</p></div>}
    </section>
    <aside className="financial-recommendations-note"><h2>추천 결과를 확인할 때</h2>
      <p>합성 데이터로 학습한 참고 추천입니다. 모델 예측 확률은 구매 적합도나 구매 가능 확률이 아닙니다. 진단 예산과 후보 차량의 실제 가격·구매 가능 여부는 별도로 확인해 주세요.</p>
      <p>차량 이미지는 예시이며 실제 연식·트림·색상과 다를 수 있습니다.</p>
    </aside>
    <div className="financial-recommendations-actions">
      <button type="button" className="financial-recommendations-secondary" onClick={() => navigate('/financial/result', { state: diagnosis })}>재무 분석 다시 보기</button>
      <button type="button" className="financial-recommendations-primary" onClick={() => navigate('/financial', { state: { ...diagnosis, reviewReturn: false } })}>진단 조건 수정하기</button>
    </div>
  </div>;
}
