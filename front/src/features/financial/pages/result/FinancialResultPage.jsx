import { normalizeCharging } from '../../chargingPreferences.js';
import { useEffect, useRef, useState } from 'react';
import { Navigate, useLocation, useNavigate } from 'react-router-dom';
import { importanceLabel, sizeLabel } from '../../vehiclePreferences.js';
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
    setNotice('차량별 가격·유지비를 계산하고 있습니다.');
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
    <div className="financial-page-heading"><div><span className="financial-eyebrow">추천을 위한 예산 확인</span><h1>내 차량 예산을 확인해 보세요</h1><p>구매할 때 쓸 돈과 매달 유지할 여력을 함께 살펴봤어요.</p></div></div>
    <div className="result-metrics">
      <section className="result-card"><h2>월 유지비에 쓸 수 있는 금액</h2><strong>{money(totals.available)}</strong><p>생활비·상환·저축 차감 후</p></section>
      <section className="result-card"><h2>차량 구매 가능 자금</h2><strong>{money(Number(assets.deposit || 0))}</strong><p>입력한 사용 가능 예금</p></section>
    </div>
    <details className="financial-disclosure result-detail-panel"><summary>내역과 추천 조건 자세히 보기</summary>
    <div className="result-chart-grid">
      <section className="result-card"><h2>월 재무 내역</h2><dl className="result-distribution">
        {[['월 소득', totals.income], ['주거·생활·고정 지출', totals.expenses - totals.loanPayment], ['기존 대출 월 상환', totals.loanPayment], ['목표 저축', totals.savings], ['월 가용자금', totals.available]].map(([label, value]) => <div key={label}><dt>{label}</dt><dd>{money(value)}</dd></div>)}
      </dl></section>
      <section className="result-card"><h2>자산·구매 자금</h2><dl className="result-distribution">
        {[['사용 가능 예금', assets.deposit], ['구매 활용 가능 예금', Number(assets.deposit || 0)]].map(([label, value]) => <div key={label}><dt>{label}</dt><dd>{money(value)}</dd></div>)}
      </dl></section>
      <section className="result-card"><h2>추천에 적용할 이용 조건</h2><dl className="result-distribution">
        {[['이용 목적', vehicle.purpose], ['선호 연료', vehicle.fuel], ...(vehicle.fuel === '전기' ? [['충전 환경', normalizeCharging(vehicle.charging)]] : []), ['희망 탑승 인원 · 선호', Number(vehicle.minimumSeats) > 0 ? `${vehicle.minimumSeats}명 이상` : '미지정']].map(([label, value]) => <div key={label}><dt>{label}</dt><dd>{value ?? '미입력'}</dd></div>)}
      </dl>
        {Number(vehicle.minimumSeats) > 0 && <p className="result-condition-note">운전자를 포함한 승차 정원으로 비교합니다. 등록된 기본 정원으로 비교합니다. 기본 정원보다 많은 인원에 좌석 옵션이 필요한 차량은 별도 확인 후보로 안내합니다.</p>}
      </section>
      <section className="result-card"><h2>중요도·점수 산정 조건</h2><dl className="result-distribution">
        {[
          ['가성비 중요도', `${importanceLabel(vehicle.costImportance)} · 가중치 ${vehicle.costImportance ?? 3}`],
          ['공간 중요도', !vehicle.preferredSize || vehicle.preferredSize === 'any' ? `${importanceLabel(vehicle.spaceImportance)} · 크기 미지정으로 평가 제외` : `${importanceLabel(vehicle.spaceImportance)} · 가중치 ${vehicle.spaceImportance ?? 3}`],
          ['선호 크기', sizeLabel(vehicle.preferredSize)],
          ['가성비 비용 비교 기간', '5년 · 차량 가격 + 유지비'],
          ['기존 ML 참고 점수', '가중치 1'],
        ].map(([label, value]) => <div key={label}><dt>{label}</dt><dd>{value}</dd></div>)}
      </dl></section>
    </div>
    </details>
    <aside className="result-warning"><h2>차량별 비용을 확인하세요</h2><p>추천 단계에서는 차량 가격과 예상 월 유지비를 비교합니다. 적격 후보 중 비용·연료 선호를 기준으로 순위를 정하며 조건을 만족하는 차량이 없을 수도 있습니다. 가격과 유지비는 비교를 위한 예상 금액입니다.</p></aside>
    <div className="financial-next-row result-navigation"><button type="button" className="result-previous" onClick={() => navigate('/financial', { state: { ...state, reviewReturn: false } })}>조건 다시 입력하기</button><button type="button" className="financial-next-button" onClick={showRecommendations} disabled={recommending} aria-busy={recommending}>{recommending ? '차량 분석 중…' : '추천 차량 확인하기'}</button></div>
    <p className="result-status" role="status">{notice}</p>
  </div>;
}
