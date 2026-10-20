import { useEffect, useRef, useState } from 'react';
import { Navigate, useLocation, useNavigate } from 'react-router-dom';
import { calculateFinancialSummary } from '../../calculateFinancialSummary';
import { buildCandidateRecommendation } from '../../buildCandidateRecommendation';
import { getFinancialRecommendations } from '../../financialRecommendationApi';
import '../../styles/FinancialPages.css';
import './FinancialResultPage.css';

const money = value => `${Number(value || 0).toLocaleString('ko-KR', { maximumFractionDigits: 2 })}만 원`;

export default function FinancialResultPage() {
  const { state } = useLocation();
  const navigate = useNavigate();
  const [notice, setNotice] = useState('');
  const [recommending, setRecommending] = useState(false);
  const pendingRequest = useRef(null);
  useEffect(() => () => pendingRequest.current?.abort(), []);
  if (!state?.values) return <Navigate to="/financial" replace />;
  const { values, assets = {}, loans = [], vehicle = {} } = state;
  const totals = calculateFinancialSummary(values, loans);

  async function showRecommendations() {
    if (pendingRequest.current) return;
    const { request, errors } = buildCandidateRecommendation(state);
    if (!request) {
      setNotice(`입력 정보를 확인해 주세요: ${[...new Set(errors)].join(', ')}`);
      return;
    }
    const controller = new AbortController();
    pendingRequest.current = controller;
    setRecommending(true);
    setNotice('차량별 가격·할부금·유지비를 계산하고 있습니다.');
    try {
      const response = await getFinancialRecommendations(request, controller.signal);
      if (!controller.signal.aborted) navigate('/financial/recommendations', { state: { diagnosis: state, result: response } });
    } catch (error) {
      if (!controller.signal.aborted) setNotice(error.response?.data?.detail ?? '추천 서버에 연결하지 못했습니다. 입력은 유지됩니다. 추천 차량 확인하기를 눌러 다시 시도해 주세요.');
    } finally {
      pendingRequest.current = null;
      if (!controller.signal.aborted) setRecommending(false);
    }
  }

  return <div className="financial-page result-page">
    <div className="financial-page-heading"><div><h1>재무 진단 요약</h1><p>차량 비용을 제외하기 전의 월 가용자금입니다. 다음 단계에서 후보별 실제 가격으로 검증합니다.</p></div><span className="financial-stage-badge">새 추천 모델 · 실험</span></div>
    <div className="result-metrics">
      <section className="result-card"><h2>월 가용자금</h2><strong>{money(totals.available)}</strong><p>생활비·대출 상환·목표 저축 차감 후</p></section>
      <section className="result-card"><h2>차량 선수금</h2><strong>{money(assets.downPayment)}</strong><p>비상 자금 {money(assets.emergency)} 별도 유지</p></section>
      <section className="result-card"><h2>최소 월 여유자금</h2><strong>{money(vehicle.minimumBuffer)}</strong><p>차량 비용을 낸 뒤에도 유지할 금액</p></section>
    </div>
    <div className="result-chart-grid">
      <section className="result-card"><h2>월 재무 내역</h2><dl className="result-distribution">
        {[['월 소득', totals.income], ['주거·생활·고정 지출', totals.expenses - totals.loanPayment], ['기존 대출 월 상환', totals.loanPayment], ['목표 저축', totals.savings], ['월 가용자금', totals.available]].map(([label, value]) => <div key={label}><dt>{label}</dt><dd>{money(value)}</dd></div>)}
      </dl></section>
      <section className="result-card"><h2>추천에 적용할 조건</h2><dl className="result-distribution">
        {[['이용 목적', vehicle.purpose], ['연간 주행거리', vehicle.annualDistance], ['할부 기간', vehicle.installment], ['선호 연료', vehicle.fuel], ['충전 조건', vehicle.charging]].map(([label, value]) => <div key={label}><dt>{label}</dt><dd>{value}</dd></div>)}
      </dl></section>
    </div>
    <aside className="result-warning"><h2>차량별 비용을 확인하세요</h2><p>기본 금리 연 6%, 비용 상승 시 금리 +3%p와 유지비 증가를 적용합니다. 적격 후보 중 비용·연료 선호를 기준으로 순위를 정하며 조건을 만족하는 차량이 없을 수도 있습니다. 가격은 수집 시점 자료이고, 세금·보험·정비·에너지 단가는 실험 가정입니다. 금융 심사나 실제 만족도를 보장하지 않습니다.</p></aside>
    <div className="financial-next-row result-navigation"><button type="button" className="result-previous" onClick={() => navigate('/financial', { state: { ...state, reviewReturn: false } })}>조건 다시 입력하기</button><button type="button" className="financial-next-button" onClick={showRecommendations} disabled={recommending} aria-busy={recommending}>{recommending ? '차량 분석 중…' : '추천 차량 확인하기'}</button></div>
    <p className="result-status" role="status">{notice}</p>
  </div>;
}
