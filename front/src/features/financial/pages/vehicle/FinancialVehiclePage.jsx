import { useState } from 'react';
import { Navigate, useLocation, useNavigate } from 'react-router-dom';
import VehiclePriorities from './VehiclePriorities';
import { FinancialProgress } from '../overview/FinancialPage';
import '../../styles/FinancialPages.css';
import './FinancialVehiclePage.css';

const purposes = ['출퇴근', '주말 여가', '가족 이동', '업무'];
const vehicleFields = [
  { name: 'segment', label: '추천 차량 범위', options: ['domestic-car', 'imported-car'] },
  { name: 'purchase', label: '구매 구분', options: ['신차 우선 · 중고차 포함', '신차만', '중고차만'] },
  { name: 'body', label: '차종', options: ['경차 · 소형 · 준중형', '중형 · 대형', 'SUV', '승합차'] },
  { name: 'fuel', label: '연료', options: ['가솔린 · 하이브리드', '가솔린', '디젤', '하이브리드', '전기', 'LPG', '상관없음'] },
  { name: 'passengers', label: '탑승 인원', options: ['주로 1~2명', '주로 3~4명', '5명 이상'] },
  { name: 'annualDistance', label: '연간 주행거리', options: ['5,000km', '10,000km', '15,000km', '20,000km', '30,000km'] },
  { name: 'road', label: '도로 환경', options: ['도심 70% · 고속 30%', '도심 50% · 고속 50%', '도심 30% · 고속 70%'] },
  { name: 'charging', label: '충전 가능 여부', options: ['충전 불가', '집에서 충전 가능', '직장에서 충전 가능', '집 · 직장 충전 가능'] },
  { name: 'installment', label: '할부 기간', options: ['일시불', '24개월', '36개월', '48개월', '60개월'] },
];
const initialVehicle = {
  purpose: '출퇴근', ...Object.fromEntries(vehicleFields.map(({ name, options }) => [name, options[0]])),
  annualDistance: '15,000km', installment: '48개월',
};
const profiles = {
  출퇴근: { title: '도심 출퇴근형 첫차', description: '정기적 출퇴근이 있어 연비가 좋고 월 부담이 안정적인 차량을 우선합니다.' },
  '주말 여가': { title: '주말 여가형 차량', description: '주말 여행과 여가 활동에 맞춰 주행 편의와 적재 공간을 함께 고려합니다.' },
  '가족 이동': { title: '가족 이동형 차량', description: '함께 타는 가족을 위해 탑승 공간과 안전·편의를 함께 고려합니다.' },
  업무: { title: '업무 이동형 차량', description: '업무 이동에 맞춰 주행거리와 유지비, 필요한 공간을 함께 고려합니다.' },
};

export default function FinancialVehiclePage() {
  const { state } = useLocation();
  const navigate = useNavigate();
  const [vehicle, setVehicle] = useState(() => ({ ...initialVehicle, ...state?.vehicle }));
  const [priorities, setPriorities] = useState(() => state?.priorities ?? ['월 총비용', '연비', '차량가격', '안전·편의', '실내공간']);
  const [notice, setNotice] = useState('');
  const profile = profiles[vehicle.purpose];
  const recommendedFuel = vehicle.fuel === '가솔린 · 하이브리드' ? '하이브리드' : vehicle.fuel === '상관없음' ? '선호 없음' : vehicle.fuel;

  if (!state?.values) return <Navigate to="/financial" replace />;

  function handleSubmit(event) {
    event.preventDefault();
    navigate('/financial/review', { state: { ...state, vehicle, priorities, reviewReturn: false } });
  }

  return (
    <div className="financial-page vehicle-page">
      <div className="financial-page-heading">
        <div><h1>차량 이용조건 입력</h1><p>실제 이용 방식에 맞춰 유지비와 추천 우선순위를 계산합니다.</p></div>
        <span className="financial-stage-badge">4 / 5 · 차량 조건</span>
      </div>
      <FinancialProgress current={4} />
      <form onSubmit={handleSubmit}>
        <div className="financial-entry-grid">
          <section className="financial-entry-card vehicle-entry-card" aria-labelledby="vehicle-title">
            <h2 id="vehicle-title">4. 차량 조건</h2>
            <p>선택한 조건은 추천 차량과 월 유지비 계산에 반영됩니다.</p>
            <fieldset className="vehicle-purpose">
              <legend>주 이용 목적</legend>
              <div className="vehicle-purpose-options">
                {purposes.map((purpose) => <label key={purpose}>
                  <input type="radio" name="purpose" value={purpose} checked={vehicle.purpose === purpose} onChange={() => { setVehicle((previous) => ({ ...previous, purpose })); setNotice(''); }} />
                  <span>{purpose}</span>
                </label>)}
              </div>
            </fieldset>
            <div className="vehicle-fields">
              {vehicleFields.map(({ name, label, options }) => <div className="financial-field" key={name}>
                <label htmlFor={`vehicle-${name}`}>{label}</label>
                <select id={`vehicle-${name}`} name={name} value={vehicle[name]} onChange={(event) => { setVehicle((previous) => ({ ...previous, [name]: event.target.value })); setNotice(''); }}>
                  {options.map((option) => <option key={option} value={option}>{name === 'segment' ? (option === 'domestic-car' ? '국내차' : '수입차') : option}</option>)}
                </select>
              </div>)}
            </div>
            <VehiclePriorities priorities={priorities} onChange={(next) => { setPriorities(next); setNotice(''); }} />
          </section>
          <aside className="vehicle-profile" aria-labelledby="vehicle-profile-title">
            <h2 id="vehicle-profile-title">예상 이용 프로필</h2>
            <svg className="vehicle-profile-icon" width="40" height="32" viewBox="0 0 40 32" fill="none" aria-hidden="true">
              <path d="M6 23H4V13L7 6H20L26 11L35 13V23H32M12 23H26" stroke="currentColor" strokeWidth="1.5" strokeLinejoin="round" />
              <circle cx="9" cy="23" r="3" stroke="currentColor" strokeWidth="1.5" /><circle cx="29" cy="23" r="3" stroke="currentColor" strokeWidth="1.5" />
            </svg>
            <div aria-live="polite">
              <h3>{profile.title}</h3><p>{profile.description}</p>
              <dl>
                <div><dt>연간 예상 주행</dt><dd>{vehicle.annualDistance}</dd></div>
                <div><dt>월 환산 주행</dt><dd>{Math.round(Number(vehicle.annualDistance.replace(/[^0-9]/g, '')) / 12).toLocaleString('ko-KR')}km</dd></div>
                <div><dt>선호 할부</dt><dd>{vehicle.installment}</dd></div>
                <div><dt>추천 연료</dt><dd>{recommendedFuel}</dd></div>
              </dl>
            </div>
          </aside>
        </div>
        <div className="financial-next-row vehicle-navigation">
          <button type="button" className="vehicle-previous-button" onClick={() => navigate('/financial/credit', { state: { ...state, vehicle, priorities } })}>이전</button>
          <button type="submit" className="financial-next-button">{state?.reviewReturn ? '수정 완료' : '다음 단계'}</button>
        </div>
        <p className="vehicle-notice" role="status">{notice}</p>
      </form>
    </div>
  );
}
