import { useState } from 'react';
import { Navigate, useLocation, useNavigate } from 'react-router-dom';
import { sizeOptions, fuelOptions, bodyTypeOptions, bodyTypeLabel } from '../../vehiclePreferences.js';
import useCandidateRecommendations from './useCandidateRecommendations.js';
import BodyTypePreview from './BodyTypePreview.jsx';
import FinancialBudgetSummary from '../../components/FinancialBudgetSummary.jsx';
import FinancialFlowHeader from '../../components/FinancialFlowHeader.jsx';
import '../../styles/FinancialPages.css';
import './FinancialVehiclePage.css';

const priorities = [['costImportance', '가성비'], ['bodyImportance', '차체 형태'], ['spaceImportance', '크기 일치'], ['fuelImportance', '선호 연료'], ['seatingImportance', '탑승 인원']];
const priorityPresets = [{ value: '1', label: '우선도 낮음' }, { value: '3', label: '우선도 중간' }, { value: '5', label: '우선도 높음' }];
const availableBodyTypeOptions = bodyTypeOptions.filter(item => item.value !== 'PICKUP');
const initialVehicle = {
  purpose: '출퇴근', fuel: '상관없음',
  preferredBodyType: 'any', bodyImportance: '3',
  costImportance: '3', spaceImportance: '3', minimumSeats: '0', preferredSize: 'any',
  fuelImportance: '3', seatingImportance: '3', purposeImportance: '1',
};
export default function FinancialVehiclePage() {
  const { state } = useLocation();
  const navigate = useNavigate();
  const [vehicle, setVehicle] = useState(() => ({ ...initialVehicle, ...state?.vehicle,
    preferredBodyType: state?.vehicle?.preferredBodyType === 'PICKUP' ? 'any' : (state?.vehicle?.preferredBodyType ?? initialVehicle.preferredBodyType),
    ...Object.fromEntries(priorities.map(([name]) => { const value = Number(state?.vehicle?.[name] ?? initialVehicle[name]); return [name, String(value <= 2 ? 1 : value >= 4 ? 5 : 3)]; })) }));

  const diagnosis = { ...state, vehicle };
  const { notice, recommending, showRecommendations } = useCandidateRecommendations(diagnosis);
  const inactive = name => (name === 'bodyImportance' && vehicle.preferredBodyType === 'any') || (name === 'fuelImportance' && vehicle.fuel === '상관없음') || (name === 'spaceImportance' && vehicle.preferredSize === 'any') || (name === 'seatingImportance' && Number(vehicle.minimumSeats) === 0);

  if (!state?.values) return <Navigate to="/financial" replace />;

  function handleSubmit(event) {
    event.preventDefault();
    showRecommendations();
  }

  return (
    <div className="financial-page vehicle-page">
      <FinancialFlowHeader current={2} title="어떤 차를 타고 싶으세요?" description="원하는 차체 형태와 연료, 크기를 골라 주세요. 다음 화면에서 종합 분석 결과를 확인할 수 있어요." />
      <form onSubmit={handleSubmit}>
        <div className="financial-entry-grid">
          <section className="financial-entry-card vehicle-entry-card" aria-labelledby="vehicle-title">
            <h2 id="vehicle-title">내 차량 취향</h2>
            <p>선택한 취향은 추천 순위에 반영됩니다.</p>
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
            <fieldset className="vehicle-purpose">
              <legend>선호 차체 형태</legend>
              <div className="vehicle-purpose-options">
                {availableBodyTypeOptions.map(item => <label key={item.value}><input type="radio" name="preferredBodyType" value={item.value} checked={vehicle.preferredBodyType === item.value} onChange={() => setVehicle(previous => ({ ...previous, preferredBodyType: item.value }))} /><span>{item.label}</span></label>)}
              </div>
              <BodyTypePreview value={vehicle.preferredBodyType} label={bodyTypeLabel(vehicle.preferredBodyType)} />
              <p className="vehicle-field-help">차체 형태와 크기는 별도 조건이에요. 쿠페형 SUV는 SUV에 포함해요.</p>
            </fieldset>
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
            <div className="vehicle-fields">
              <div className="financial-field"><label htmlFor="vehicle-minimumSeats">최소 탑승 인원 · 운전자 포함</label><select id="vehicle-minimumSeats" value={vehicle.minimumSeats} onChange={event => setVehicle(previous => ({ ...previous, minimumSeats: event.target.value }))}><option value="0">상관없음</option>{[2, 3, 4, 5, 6, 7, 8, 9].map(value => <option key={value} value={value}>{value}명 이상</option>)}</select><p>최소 인원은 중요도와 관계없이 필수로 적용해요. 정원이 부족한 차량은 추천에서 제외해요.</p></div>
            </div>
            <fieldset className="vehicle-preferences">
              <legend>어떤 점이 중요한가요?</legend>
              <p>중요할수록 추천 순위에 더 크게 반영합니다.</p>
              <div className="vehicle-priority-list">
                {priorities.map(([name, label]) => <fieldset className="vehicle-priority-row" key={name} disabled={inactive(name)}>
                  <legend>{label}{inactive(name) && <small>조건을 선택하면 설정할 수 있어요</small>}</legend>
                  <div className="vehicle-purpose-options">
                    {priorityPresets.map(item => <label key={item.value}><input type="radio" name={name} value={item.value} checked={vehicle[name] === item.value} onChange={() => setVehicle(previous => ({ ...previous, [name]: item.value }))} /><span>{item.label}</span></label>)}
                  </div>
                </fieldset>)}
              </div>

            </fieldset>

            <p className="vehicle-field-help">가성비를 높게 선택하면 구매비·유지비 절약을 더 중요하게 반영해요. 낮게 선택하면 비용 차이의 영향이 줄고 다른 선호가 상대적으로 더 반영됩니다. 비싼 차량에 별도 가점은 주지 않아요.</p>

          </section>
          <FinancialBudgetSummary values={state.values} assets={state.assets} loans={state.loans} />
        </div>
        <section className="vehicle-final-check" aria-labelledby="final-check-title">
          <div><h2 id="final-check-title">선택한 조건으로 차량을 찾아볼까요?</h2><p>{vehicle.fuel} · {bodyTypeLabel(vehicle.preferredBodyType)} · {Number(vehicle.minimumSeats) > 0 ? `${vehicle.minimumSeats}명 이상` : '탑승 인원 상관없음'}</p><p>구매 후 예금으로 부족한 월 자금을 최소 12개월 충당할 수 있는 차량도 비교합니다. 유지비는 공통 기준인 연 15,000km로 계산합니다.</p></div>
        </section>
          <div className="financial-next-row">
            <button type="button" className="financial-previous-button" disabled={recommending} onClick={() => navigate('/financial', { state: diagnosis })}>재무 정보 수정</button>
            <button type="submit" className="financial-next-button" disabled={recommending} aria-busy={recommending}>{recommending ? '분석하고 있어요…' : '종합 분석 결과 보기'}</button>
          </div>
          {notice && <p className="vehicle-request-notice" role={recommending ? 'status' : 'alert'}>{notice}</p>}

      </form>
    </div>
  );
}
