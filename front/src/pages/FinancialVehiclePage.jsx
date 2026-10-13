import { useState } from 'react';
import { Navigate, useLocation, useNavigate } from 'react-router-dom';
import { FinancialProgress } from './FinancialPage';
import './FinancialPage.css';
import './FinancialAssetsPage.css';
import './FinancialCreditPage.css';
import './FinancialVehiclePage.css';

const purposes = ['출퇴근', '주말 여가', '가족 이용', '업무'];
const fields = [
  { name: 'purchase', label: '구매 구분', options: ['신차 우선 · 중고차 포함', '신차만', '중고차만'] },
  { name: 'type', label: '차종', options: ['경차 · 소형 · 준중형', '중형', '대형', 'SUV', '선호 없음'] },
  { name: 'fuel', label: '연료', options: ['가솔린 · 하이브리드', '가솔린', '하이브리드', '전기', '디젤', '선호 없음'] },
  { name: 'passengers', label: '탑승 인원', options: ['주로 1~2명', '주로 3~4명', '5명 이상'] },
  { name: 'mileage', label: '연간 주행거리', options: ['5,000km 이하', '10,000km', '15,000km', '20,000km', '25,000km 이상'] },
  { name: 'roads', label: '도로 환경', options: ['도심 70% · 고속 30%', '도심 50% · 고속 50%', '도심 30% · 고속 70%', '주로 도심', '주로 고속도로'] },
  { name: 'charging', label: '충전 가능 여부', options: ['충전 불가', '집에서 충전 가능', '직장에서 충전 가능', '공용 충전소 이용 가능'] },
  { name: 'term', label: '할부 기간', options: ['일시불', '24개월', '36개월', '48개월', '60개월'] },
];
const initial = {
  purpose: '출퇴근', purchase: fields[0].options[0], type: fields[1].options[0],
  fuel: fields[2].options[0], passengers: fields[3].options[0], mileage: '15,000km',
  roads: fields[5].options[0], charging: '충전 불가', term: '48개월',
};
const priorities = ['월 부담', '연비', '차량 가격', '공간·편의', '실내 공간'];

export default function FinancialVehiclePage() {
  const { state } = useLocation();
  const navigate = useNavigate();
  const [vehicle, setVehicle] = useState(state?.vehicle ?? initial);
  const [ranking, setRanking] = useState(state?.ranking ?? priorities);
  const [notice, setNotice] = useState('');
  const [selectedPriority, setSelectedPriority] = useState(null);

  if (!state?.values) return <Navigate to="/financial" replace />;

  function changePriority(index) {
    if (selectedPriority === null) {
      setSelectedPriority(index);
      return;
    }
    setRanking((previous) => {
      const next = [...previous];
      [next[selectedPriority], next[index]] = [next[index], next[selectedPriority]];
      return next;
    });
    setSelectedPriority(null);
  }

  function handleSubmit(event) {
    event.preventDefault();
    setNotice('차량 조건 입력을 완료했습니다. 마지막 확인 화면은 준비 중입니다.');
  }

  return (
    <div className="financial-page vehicle-page">
      <div className="financial-page-heading">
        <div>
          <h1>차량 이용조건 입력</h1>
          <p>실제 이용 방식에 맞춰 유지비와 추천 우선순위를 계산합니다.</p>
        </div>
        <span className="financial-stage-badge">4 / 5 · 차량 조건</span>
      </div>
      <FinancialProgress current={4} />

      <form onSubmit={handleSubmit}>
        <div className="financial-entry-grid">
          <section className="financial-entry-card" aria-labelledby="vehicle-title">
            <h2 id="vehicle-title">4. 차량 조건</h2>
            <p>선택한 조건은 추천 차량과 월 유지비 계산에 반영됩니다.</p>

            <fieldset className="credit-overdue">
              <legend>주 이용 목적</legend>
              <div className="credit-chip-group">
                {purposes.map((purpose) => (
                  <label className="credit-chip" key={purpose}>
                    <input
                      type="radio"
                      name="purpose"
                      value={purpose}
                      checked={vehicle.purpose === purpose}
                      onChange={() => setVehicle((previous) => ({ ...previous, purpose }))}
                    />
                    <span>{purpose}</span>
                  </label>
                ))}
              </div>
            </fieldset>

            <div className="financial-fields vehicle-fields">
              {fields.map(({ name, label, options }) => (
                <div className="financial-field" key={name}>
                  <label htmlFor={`vehicle-${name}`}>{label}</label>
                  <select
                    id={`vehicle-${name}`}
                    value={vehicle[name]}
                    onChange={(event) => setVehicle((previous) => ({ ...previous, [name]: event.target.value }))}
                  >
                    {options.map((option) => <option key={option} value={option}>{option}</option>)}
                  </select>
                </div>
              ))}
            </div>

            <section className="vehicle-priorities" aria-labelledby="priority-title">
              <h3 id="priority-title">중요조건 우선순위</h3>
              <p>두 항목을 차례로 눌러 순서를 바꿀 수 있습니다.</p>
              <ol>
                {ranking.map((priority, index) => (
                  <li key={priority}>
                    <button
                      type="button"
                      aria-pressed={selectedPriority === index}
                      onClick={() => changePriority(index)}
                    >
                      {index + 1} {priority}
                    </button>
                  </li>
                ))}
              </ol>
              <p className="vehicle-priority-status" role="status">
                {selectedPriority !== null ? `${ranking[selectedPriority]}와 순서를 바꿀 항목을 선택하세요.` : ''}
              </p>
            </section>
            <p className="credit-notice" role="status">{notice}</p>
          </section>

          <aside className="financial-live-card" aria-labelledby="profile-title">
            <h2 id="profile-title">예상 이용 프로필</h2>
            <svg className="vehicle-profile-icon" viewBox="0 0 48 32" fill="none" stroke="currentColor" strokeWidth="1.5" aria-hidden="true">
              <path d="m5 20 4-11h18l7 8 8 3v7h-5m-23 0h14M5 20v7h3" />
              <circle cx="11" cy="26" r="4" />
              <circle cx="32" cy="26" r="4" />
            </svg>
            <h3 className="vehicle-profile-title">
              {vehicle.roads.includes('고속 70%') || vehicle.roads === '주로 고속도로' ? '장거리 이동형' : '도심 이용형'} {vehicle.purpose}
            </h3>
            <p>선택한 이용 조건을 정리한 예시 프로필입니다. 실제 차량 추천과 유지비 계산은 추후 연결됩니다.</p>
            <dl className="vehicle-profile-details">
              <div><dt>연간 예상 주행</dt><dd>{vehicle.mileage}</dd></div>
              <div><dt>탑승 인원</dt><dd>{vehicle.passengers}</dd></div>
              <div><dt>선호 할부</dt><dd>{vehicle.term}</dd></div>
              <div><dt>선호 연료</dt><dd>{vehicle.fuel}</dd></div>
              <div><dt>가장 중요한 조건</dt><dd>{ranking[0]}</dd></div>
            </dl>
          </aside>
        </div>

        <div className="financial-next-row assets-navigation">
          <button
            type="button"
            className="assets-previous-button"
            onClick={() => navigate('/financial/credit', { state: { ...state, vehicle, ranking } })}
          >
            이전
          </button>
          <button className="financial-next-button" type="submit">다음 단계</button>
        </div>
      </form>
    </div>
  );
}
