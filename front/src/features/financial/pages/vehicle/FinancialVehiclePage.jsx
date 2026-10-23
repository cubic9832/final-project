import { useState } from 'react';
import { Navigate, useLocation, useNavigate } from 'react-router-dom';
import { sizeOptions, fuelOptions } from '../../vehiclePreferences.js';
import { chargingOptions, normalizeCharging } from '../../chargingPreferences.js';
import FinancialBudgetSummary from '../../components/FinancialBudgetSummary.jsx';
import { FinancialProgress } from '../overview/FinancialPage';
import '../../styles/FinancialPages.css';
import './FinancialVehiclePage.css';

const priorities = [['costImportance', '가성비'], ['spaceImportance', '크기 일치'], ['fuelImportance', '선호 연료'], ['seatingImportance', '탑승 인원'], ['purposeImportance', '이용 목적']];
const priorityPresets = [{ value: '1', label: '낮음' }, { value: '3', label: '보통' }, { value: '5', label: '높음' }];
const purposes = ['출퇴근', '주말 여가', '가족 이동', '업무'];
const vehicleFields = [
  { name: 'charging', label: '전기차를 정기적으로 충전할 환경이 있나요?', options: chargingOptions },
];
const initialVehicle = {
  purpose: '출퇴근', fuel: '상관없음', ...Object.fromEntries(vehicleFields.map(({ name, options }) => [name, options[0]])),
  charging: '잘 모르겠음',
  costImportance: '3', spaceImportance: '3', minimumSeats: '0', preferredSize: 'any',
  fuelImportance: '3', seatingImportance: '3', purposeImportance: '1',
};
export default function FinancialVehiclePage() {
  const { state } = useLocation();
  const navigate = useNavigate();
  const [vehicle, setVehicle] = useState(() => ({ ...initialVehicle, ...state?.vehicle,
    charging: normalizeCharging(state?.vehicle?.charging) ?? initialVehicle.charging,
    ...Object.fromEntries(priorities.map(([name]) => { const value = Number(state?.vehicle?.[name] ?? initialVehicle[name]); return [name, String(value <= 2 ? 1 : value >= 4 ? 5 : 3)]; })) }));

  if (!state?.values) return <Navigate to="/financial" replace />;

  function handleSubmit(event) {
    event.preventDefault();
    navigate('/financial/review', { state: { ...state, vehicle, reviewReturn: false } });
  }

  return (
    <div className="financial-page vehicle-page">
      <div className="financial-page-heading">
        <div><span className="financial-eyebrow">나에게 맞는 첫차 찾기</span><h1>어떤 차를 타고 싶으세요?</h1><p>원하는 연료와 크기를 골라 주세요. 예산 안에서 취향을 반영합니다.</p></div>
        <span className="financial-stage-badge">2 / 3 · 차량 이용</span>
      </div>
      <FinancialProgress current={2} />
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
              <div className="financial-field"><label htmlFor="vehicle-minimumSeats">희망 탑승 인원 · 운전자 포함</label><select id="vehicle-minimumSeats" value={vehicle.minimumSeats} onChange={event => setVehicle(previous => ({ ...previous, minimumSeats: event.target.value }))}><option value="0">상관없음</option>{[2, 3, 4, 5, 6, 7, 8, 9].map(value => <option key={value} value={value}>{value}명 이상</option>)}</select></div>
            </div>
            <fieldset className="vehicle-purpose">
              <legend>주 이용 목적</legend>
              <div className="vehicle-purpose-options">
                {purposes.map((purpose) => <label key={purpose}>
                  <input type="radio" name="purpose" value={purpose} checked={vehicle.purpose === purpose} onChange={() => { setVehicle((previous) => ({ ...previous, purpose })); }} />
                  <span>{purpose}</span>
                </label>)}
              </div>
            </fieldset>
            <fieldset className="vehicle-preferences">
              <legend>어떤 점이 중요한가요?</legend>
              <p>중요할수록 추천 순위에 더 크게 반영합니다.</p>
              <div className="vehicle-priority-list">
                {priorities.map(([name, label]) => <fieldset className="vehicle-priority-row" key={name}>
                  <legend>{label}</legend>
                  <div className="vehicle-purpose-options">
                    {priorityPresets.map(item => <label key={item.value}><input type="radio" name={name} value={item.value} checked={vehicle[name] === item.value} onChange={() => setVehicle(previous => ({ ...previous, [name]: item.value }))} /><span>{item.label}</span></label>)}
                  </div>
                </fieldset>)}
              </div>

            </fieldset>

            <div className="vehicle-fields">
              {vehicleFields.filter(({ name }) => name !== 'charging' || vehicle.fuel === '전기').map(({ name, label, options }) => <div className="financial-field" key={name}>
                <label htmlFor={`vehicle-${name}`}>{label}</label>
                <select id={`vehicle-${name}`} name={name} value={vehicle[name]} onChange={(event) => { setVehicle((previous) => ({ ...previous, [name]: event.target.value })); }}>
                  {options.map((option) => <option key={option}>{option}</option>)}
                </select>
              </div>)}

            </div>

          </section>
          <FinancialBudgetSummary values={state.values} assets={state.assets} loans={state.loans} />
        </div>
        <div className="financial-next-row vehicle-navigation">
          <button type="button" className="vehicle-previous-button" onClick={() => navigate('/financial', { state: { ...state, vehicle } })}>이전</button>
          <button type="submit" className="financial-next-button">{state?.reviewReturn ? '수정 완료' : '다음 단계'}</button>
        </div>

      </form>
    </div>
  );
}
