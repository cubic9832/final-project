import { useState } from 'react';
import { Navigate, useLocation, useNavigate } from 'react-router-dom';
import FinancialFlowHeader from '../../components/FinancialFlowHeader.jsx';
import FinancialBudgetSummary from '../../components/FinancialBudgetSummary.jsx';
import { createVehiclePreferences } from '../../createVehiclePreferences.js';
import useRecommendationOptions from '../../useRecommendationOptions.js';
import './FinancialEnvironmentPage.css';
import '../../styles/VehicleInputs.css';

const costPriorities = [
  ['costImportance', '구매비와 유지비를 얼마나 아끼고 싶나요?',
    ['취향을 더 고려', '비용·취향 균형', '비용 절약 우선'], '차량 가격과 매달 드는 유지비를 함께 비교해요.'],
  ['assetRetentionImportance', '차를 산 뒤 예금을 얼마나 남기고 싶나요?',
    ['마음에 들면 사용', '일부는 남기기', '예금 보존 우선'], '중요하게 볼수록 구매 후 예금이 많이 남는 차에 유리해요.'],
  ['runningCostImportance', '매달 드는 유지비를 얼마나 아끼고 싶나요?',
    ['취향을 더 고려', '유지비·취향 균형', '유지비 절약 우선'], '연료비·보험료·세금·정비비를 합친 월 유지비를 비교해요.'],
];
const tastePriorities = [
  ['designImportance', '원하는 차체 윤곽이 얼마나 중요한가요?',
    ['다른 조건 우선', '골고루 고려', '원하는 윤곽 우선'], '다음 단계에서 고를 둥근 윤곽·각진 윤곽 등의 취향을 얼마나 반영할지 정해요.'],
  ['performanceImportance', '원하는 가속 느낌이 얼마나 중요한가요?',
    ['다른 조건 우선', '골고루 고려', '원하는 가속 우선'], '빠른 차를 고르는 항목이 아니에요. 다음에 고를 완만한·중간·빠른 가속과의 일치를 비교해요.'],
  ['fuelImportance', '원하는 연료가 얼마나 중요한가요?',
    ['다른 조건 우선', '골고루 고려', '원하는 연료 우선'], '다음 단계에서 고를 휘발유·하이브리드·전기 등의 선호를 반영해요.'],
  ['spaceImportance', '원하는 차량 크기가 얼마나 중요한가요?',
    ['다른 조건 우선', '골고루 고려', '원하는 크기 우선'], '큰 차를 고르는 항목이 아니에요. 다음에 고를 작은·보통·큰 차와의 일치를 비교해요.'],
];

export default function FinancialEnvironmentPage() {
  const { state } = useLocation();
  const navigate = useNavigate();
  const [vehicle, setVehicle] = useState(() => createVehiclePreferences(state?.vehicle));
  const { options, error } = useRecommendationOptions();
  if (!state?.values) return <Navigate to="/financial" replace />;
  const update = (name, value) => setVehicle(previous => ({ ...previous, [name]: value }));
  const diagnosis = { ...state, vehicle: { ...vehicle, scenarioMode: options?.scenarioSupported ?? vehicle.scenarioMode } };
  const scenarioMode = options?.scenarioSupported ?? vehicle.scenarioMode ?? false;

  function priorities(fields) {
    return <div className="environment-priorities">{fields.map(([name, label, choices, help]) => <fieldset className="vehicle-priority-row" key={name} aria-describedby={`${name}-help`}>
      <legend>{label}</legend>
      <p className="vehicle-field-help" id={`${name}-help`}>{help}</p>
      <div className="vehicle-purpose-options">{choices.map((text, index) => { const value = String(index * 2 + 1); return <label key={value}>
        <input type="radio" name={name} value={value} checked={String(vehicle[name]) === value} onChange={() => update(name, value)} /><span>{text}</span>
      </label>; })}</div>
    </fieldset>)}</div>;
  }

  return <div className="financial-page vehicle-input-page environment-page">
    <FinancialFlowHeader current={2} title="어떻게 이용하고, 무엇을 중요하게 보세요?" description="이용 조건과 비교 기준을 먼저 정해 주세요. 다음 단계에서 마음에 드는 차량 취향을 고릅니다." />
    <form onSubmit={event => { event.preventDefault(); if (options) navigate('/financial/vehicle', { state: diagnosis }); }}>
      <div className="financial-entry-grid">
        <div className="environment-sections">
          <section className="financial-entry-card vehicle-entry-card" aria-labelledby="environment-title">
            <h2 id="environment-title">이용 조건</h2><p>함께 탈 인원을 알려주세요. 운전자도 포함해 주세요.</p>
            {!options && !error && <p role="status">추천 입력 항목을 불러오고 있어요…</p>}
            {error && <p role="alert">{error}</p>}
            <div className="vehicle-fields environment-fields">
              <div className="financial-field"><label htmlFor="environment-seats">최소 탑승 인원 · 운전자 포함</label><select id="environment-seats" value={vehicle.minimumSeats} onChange={event => update('minimumSeats', event.target.value)}><option value="0">상관없음</option>{[2, 3, 4, 5, 6, 7, 8, 9].map(seats => <option key={seats} value={seats}>{seats}명 이상</option>)}</select></div>
            </div>
            <p className="vehicle-field-help">최소 인원은 필수 조건으로 적용됩니다.</p>
          </section>
          <section className="financial-entry-card vehicle-entry-card" aria-labelledby="importance-title">
            <h2 id="importance-title">나의 비교 기준</h2><p>조건이 서로 다를 때 무엇을 더 우선할지 골라 주세요. ‘우선’은 반드시 일치해야 한다는 뜻은 아니에요. 다음 단계에서 ‘상관없음’을 선택한 취향은 비교에서 제외돼요.</p>
            <h3 className="environment-group-heading">비용과 자금</h3>
            {priorities(scenarioMode ? costPriorities : costPriorities.slice(0, 1))}
            <h3 className="environment-group-heading">차량 취향</h3>
            {priorities(scenarioMode ? tastePriorities : [...tastePriorities, ['lifestylePurposeImportance', '사용 목적에 맞는 차가 얼마나 중요한가요?', ['다른 조건 우선', '골고루 고려', '사용 목적 우선'], '다음 단계에서 고를 사용 목적과의 일치를 비교해요.']])}
          </section>
        </div>
        <FinancialBudgetSummary values={state.values} assets={state.assets} loans={state.loans} />
      </div>
      <div className="financial-next-row"><button type="button" className="financial-previous-button" onClick={() => navigate('/financial', { state: diagnosis })}>재무 정보 수정</button><button type="submit" className="financial-next-button" disabled={!options}>차량 취향 선택하기</button></div>
    </form>
  </div>;
}
