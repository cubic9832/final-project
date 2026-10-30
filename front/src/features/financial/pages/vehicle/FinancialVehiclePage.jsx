import { useState } from 'react';
import { Navigate, useLocation, useNavigate } from 'react-router-dom';
import { sizeOptions, fuelOptions } from '../../vehiclePreferences.js';
import useCandidateRecommendations from './useCandidateRecommendations.js';
import LifestylePreferences from './LifestylePreferences.jsx';
import useRecommendationOptions from '../../useRecommendationOptions.js';
import { createVehiclePreferences } from '../../createVehiclePreferences.js';
import FinancialBudgetSummary from '../../components/FinancialBudgetSummary.jsx';
import FinancialFlowHeader from '../../components/FinancialFlowHeader.jsx';
import '../../styles/FinancialPages.css';
import '../../styles/VehicleInputs.css';

export default function FinancialVehiclePage() {
  const { state } = useLocation();
  const navigate = useNavigate();
  const [vehicle, setVehicle] = useState(() => createVehiclePreferences(state?.vehicle));

  const { options, error: optionsError } = useRecommendationOptions();
  const scenarioMode = options?.scenarioSupported ?? false;
  const diagnosis = { ...state, vehicle: { ...vehicle, scenarioMode } };
  const { notice, recommending, showRecommendations } = useCandidateRecommendations(diagnosis);


  if (!state?.values) return <Navigate to="/financial" replace />;

  function handleSubmit(event) {
    event.preventDefault();
    if (!options) return;
    showRecommendations();
  }

  return (
    <div className="financial-page vehicle-input-page">
      <FinancialFlowHeader current={3} title="어떤 차를 타고 싶으세요?" description="마음에 드는 윤곽과 가속 성향, 연료와 크기를 골라 주세요. 다음 화면에서 종합 분석 결과를 확인할 수 있어요." />
      <form onSubmit={handleSubmit}>
        <div className="financial-entry-grid">
          <div className="vehicle-section-stack">
          <section className="financial-entry-card vehicle-entry-card">
            <LifestylePreferences value={vehicle} onChange={setVehicle} includePurpose={!scenarioMode} />
          </section>
          <section className="financial-entry-card vehicle-entry-card" aria-labelledby="vehicle-title">
            <h2 id="vehicle-title">연료와 크기</h2>
            <p>선택한 취향은 추천 순위에 반영됩니다.</p>
            {!options && !optionsError && <p role="status">추천 입력 항목을 불러오고 있어요…</p>}
            {optionsError && <p role="alert">{optionsError}</p>}
            <fieldset className="vehicle-purpose vehicle-fuel-preference" aria-describedby="vehicle-fuel-help">
              <legend>선호 연료</legend>
              <p id="vehicle-fuel-help">원하는 연료가 없다면 상관없음을 선택해 주세요.</p>
              <div className="vehicle-purpose-options">
                {fuelOptions.map(fuel => <label key={fuel}>
                  <input type="radio" name="fuel" value={fuel} checked={vehicle.fuel === fuel} onChange={() => setVehicle(previous => ({ ...previous, fuel }))} />
                  <span>{fuel === '가솔린' ? '휘발유(가솔린)' : fuel === '디젤' ? '경유(디젤)' : fuel}</span>
                </label>)}
              </div>
            </fieldset>
            {scenarioMode && vehicle.fuel === '전기' && <fieldset className="vehicle-purpose">
              <legend>집이나 직장에서 전기차를 충전할 수 있나요?</legend>
              <div className="vehicle-purpose-options">{[[false, '충전할 곳이 없어요'], [true, '충전할 수 있어요']].map(([available, label]) => <label key={String(available)}><input type="radio" name="chargingAvailable" checked={(vehicle.chargingAvailable ?? false) === available} onChange={() => setVehicle(previous => ({ ...previous, chargingAvailable: available }))} /><span>{label}</span></label>)}</div>
            </fieldset>}
            <fieldset className="vehicle-purpose vehicle-size-preference">
              <legend>선호 크기</legend>
              <div className="vehicle-purpose-options vehicle-size-options">
                {sizeOptions.map(item => <label key={item.value}>
                  <input type="radio" name="preferredSize" value={item.value} checked={vehicle.preferredSize === item.value} onChange={() => setVehicle(previous => ({ ...previous, preferredSize: item.value }))} />
                  <span>{({ any: '상관없음', small: '작게', medium: '보통', large: '크게' })[item.value]}<small>{({ any: '크기 평가 제외', small: '전장 4.2m 이하', medium: '전장 4.2~4.8m', large: '전장 4.8m 이상' })[item.value]}</small></span>
                </label>)}
              </div>
              <p className="vehicle-field-help">크기는 차량 전체 길이 기준이며, 실내 공간과는 다를 수 있습니다.</p>
            </fieldset>
            <p className="vehicle-field-help">{scenarioMode ? '구매비·유지비와 최소 탑승 인원을 먼저 확인하고, 비용 성향·연료·크기·주행거리·충전 여건을 바탕으로 어울리는 차량을 추천합니다.' : '구매비·유지비와 최소 탑승 인원은 먼저 확인합니다. 디자인·가속·목적은 비교군 학습 점수로, 연료와 크기 일치는 보조 기준으로 반영합니다. 취향 근거가 없으면 구매 후 남는 자금을 참고합니다.'}</p>

          </section>
          </div>
          <FinancialBudgetSummary values={state.values} assets={state.assets} loans={state.loans} />
        </div>
        <section className="vehicle-final-check" aria-labelledby="final-check-title">
          <div><h2 id="final-check-title">선택한 조건으로 차량을 찾아볼까요?</h2><p>{vehicle.fuel} · {Number(vehicle.minimumSeats) > 0 ? `${vehicle.minimumSeats}명 이상` : '탑승 인원 상관없음'}</p><p>구매 후 예금으로 부족한 월 자금을 최소 12개월 충당할 수 있는 차량도 비교합니다. 유지비는 공통 기준인 연 15,000km로 계산합니다.</p></div>
        </section>
          <div className="financial-next-row">
            <button type="button" className="financial-previous-button" disabled={recommending} onClick={() => navigate('/financial/environment', { state: diagnosis })}>이용 환경·중요도 수정</button>
            <button type="submit" className="financial-next-button" disabled={recommending || !options} aria-busy={recommending}>{recommending ? '분석하고 있어요…' : '종합 분석 결과 보기'}</button>
          </div>
          {notice && <p className="vehicle-request-notice" role={recommending ? 'status' : 'alert'}>{notice}</p>}

      </form>
    </div>
  );
}
