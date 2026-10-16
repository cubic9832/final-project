import { useEffect } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { CircleAlert, LoaderCircle, SearchX } from 'lucide-react';
import { useVehicle } from '../features/vehicle/useVehicle';
import { getFinancialRecommendations } from './FinancialVehicleRecommendationsPage';
import './FinancialRecommendationStatusPage.css';

export default function FinancialRecommendationStatusPage() {
  const { state } = useLocation();
  const navigate = useNavigate();
  const { vehicles, catalogStatus, catalogError, retryCatalog } = useVehicle();
  const analysis = getFinancialRecommendations(state, vehicles);
  const failed = !analysis.valid || catalogStatus === 'error';
  const empty = !failed && catalogStatus === 'ready' && !analysis.vehicles.length;

  useEffect(() => {
    if (analysis.valid && catalogStatus === 'ready' && analysis.vehicles.length) {
      navigate('/financial/recommendations', { state, replace: true });
    }
  }, [analysis.valid, analysis.vehicles.length, catalogStatus, navigate, state]);

  const edit = () => navigate('/financial', { state: { ...state, reviewReturn: false } });
  const Icon = failed ? CircleAlert : empty ? SearchX : LoaderCircle;
  return <div className="financial-recommendation-status">
    <header><h1>분석·추천 상태 화면</h1><p>입력 확인 · 분석 진행 · 결과 확인 · 조건 수정</p></header>
    <p className="frs-banner">입력한 재무 조건과 기존 차량 데이터로 구매 여력을 확인합니다.</p>
    <section className={`frs-card ${failed ? 'frs-failed' : empty ? 'frs-empty' : 'frs-loading'}`} aria-live="polite" aria-busy={!failed && !empty}>
      <small>{failed ? 'STATE 02 · 분석 실패' : empty ? 'STATE 03 · 추천 결과 없음' : 'STATE 01 · 분석 진행 중'}</small>
      <span className="frs-icon"><Icon size={24} aria-hidden="true" /></span>
      <h2>{failed ? '분석을 완료하지 못했어요' : empty ? '맞는 차량을 찾지 못했어요' : '구매 여력을 분석하고 있어요'}</h2>
      <p>{!analysis.valid ? '재무 입력값과 할부 기간을 확인해 주세요.' : failed ? catalogError : empty ? '현재 구매 예산 안에 맞는 차량 후보가 없어요. 조건을 다시 확인해 주세요.' : '입력한 예산과 차량 정보를 확인하고 있습니다. 완료되면 추천 차량 화면으로 이동합니다.'}</p>
      <div className="frs-checklist"><strong>{failed ? '입력 정보 확인' : empty ? '확인할 조건' : '입력정보 확인'}</strong><p>소득·지출 · 선수금 · 할부 기간 · 차량 구매 예산</p></div>
      <p className="frs-hint">입력한 조건은 유지됩니다.</p>
      <div className="frs-actions">
        {failed ? <><button onClick={edit}>입력 확인</button>{analysis.valid && <button className="frs-primary" onClick={retryCatalog}>다시 분석</button>}</> : empty ? <button className="frs-primary" onClick={edit}>차량 조건 수정</button> : <button disabled>분석 진행 중</button>}
      </div>
    </section>
    <aside className="frs-banner"><strong>재분석 시 데이터 흐름</strong><p>입력값 유지 · 조건 수정 후 재확인 · 추천 결과 갱신</p></aside>
  </div>;
}
