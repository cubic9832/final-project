import { Navigate, useLocation, useNavigate } from 'react-router-dom';
import FinancialAnalysis from '../recommendations/FinancialAnalysis.jsx';
import FinancialFlowHeader from '../../components/FinancialFlowHeader.jsx';
import { calculateFinancialSummary } from '../../calculateFinancialSummary.js';
import '../recommendations/FinancialRecommendationsPage.css';

export default function FinancialResultPage() {
  const { state } = useLocation();
  const navigate = useNavigate();
  if (!state?.diagnosis?.values || state?.result?.modelVersion !== 'candidate-v2') return <Navigate to={state?.values ? '/financial/vehicle' : '/financial'} state={state} replace />;
  const { diagnosis, result } = state;
  return <div className="financial-recommendations-page">
    <FinancialFlowHeader current={3} title="종합 분석 결과" description="입력한 재무 정보로 구매 전후의 자금 변화를 확인하세요." />
    <FinancialAnalysis totals={calculateFinancialSummary(diagnosis.values, diagnosis.loans ?? [])} result={result} onShowRecommendations={() => navigate('/financial/recommendations', { state })} />
    <div className="financial-next-row"><button type="button" className="financial-previous-button" onClick={() => navigate('/financial/vehicle', { state: diagnosis })}>차량 취향 수정</button><button type="button" className="financial-next-button" onClick={() => navigate('/financial/recommendations', { state })}>추천 차량 보기</button></div>
  </div>;
}
