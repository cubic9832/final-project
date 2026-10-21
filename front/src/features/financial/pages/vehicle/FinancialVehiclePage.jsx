import { useState } from 'react';
import { Navigate, useLocation, useNavigate } from 'react-router-dom';
import { Car } from 'lucide-react';
import theme from '../../../../styles/theme.js';
import { importanceLevels, sizeOptions, importanceLabel, sizeLabel } from '../../vehiclePreferences.js';
import { FinancialProgress } from '../overview/FinancialPage';
import '../../styles/FinancialPages.css';
import './FinancialVehiclePage.css';

const purposes = ['출퇴근', '주말 여가', '가족 이동', '업무'];
const vehicleFields = [
  { name: 'annualDistance', label: '연간 주행거리', options: ['5,000km', '10,000km', '15,000km', '20,000km', '30,000km'] },
  { name: 'fuel', label: '선호 연료 · 순위에 반영', options: ['상관없음', '가솔린', '하이브리드', '디젤', '전기', 'LPG'] },
  { name: 'charging', label: '충전 가능 여부 · 전기차 후보 조건', options: ['충전 불가', '집에서 충전 가능', '직장에서 충전 가능', '집 · 직장 충전 가능'] },
  { name: 'installment', label: '할부 기간', options: ['일시불', '24개월', '36개월', '48개월', '60개월'] },
];
const initialVehicle = {
  purpose: '출퇴근', ...Object.fromEntries(vehicleFields.map(({ name, options }) => [name, options[0]])),
  annualDistance: '15,000km', installment: '48개월', minimumBuffer: '0',
  costImportance: '3', spaceImportance: '3', minimumSeats: '0', preferredSize: 'any',
};
export default function FinancialVehiclePage() {
  const { state } = useLocation();
  const navigate = useNavigate();
  const [bufferError, setBufferError] = useState('');
  const [vehicle, setVehicle] = useState(() => ({ ...initialVehicle, ...state?.vehicle }));

  if (!state?.values) return <Navigate to="/financial" replace />;

  function handleSubmit(event) {
    event.preventDefault();
    navigate('/financial/review', { state: { ...state, vehicle, reviewReturn: false } });
  }

  return (
    <div className="financial-page vehicle-page">
      <div className="financial-page-heading">
        <div><h1>차량 이용조건 입력</h1><p>이용 정보와 자금 계획으로 차량별 비용을 계산하고 예산 안의 후보를 추천합니다.</p></div>
        <span className="financial-stage-badge">3 / 4 · 차량 이용</span>
      </div>
      <FinancialProgress current={3} />
      <form onSubmit={handleSubmit}>
        <div className="financial-entry-grid">
          <section className="financial-entry-card vehicle-entry-card" aria-labelledby="vehicle-title">
            <h2 id="vehicle-title">3. 차량 이용</h2>
            <p>재무 조건을 통과한 후보에 가성비·크기 중요도를 반영합니다. 크기는 실내 공간이 아닌 전장 기준입니다.</p>
            <fieldset className="vehicle-preferences">
              <legend>중요하게 생각하는 요소</legend>
              <p>중요도는 1~5 가중치로 반영합니다. 중요하지 않아도 비싼 차나 큰 차를 선호한다는 뜻은 아닙니다.</p>
              <div className="vehicle-fields">
                {[['costImportance', '가성비 중요도 · 구매비 + 유지비'], ['spaceImportance', '공간 중요도 · 선호 크기 일치']].map(([name, label]) => <div className="financial-field" key={name}>
                  <label htmlFor={`vehicle-${name}`}>{label}</label><select id={`vehicle-${name}`} value={vehicle[name]} onChange={event => setVehicle(previous => ({ ...previous, [name]: event.target.value }))}>
                    {importanceLevels.map(item => <option value={item.value} key={item.value}>{item.label}</option>)}
                  </select>
                </div>)}
                <div className="financial-field"><label htmlFor="vehicle-preferredSize">선호 크기</label><select id="vehicle-preferredSize" value={vehicle.preferredSize} onChange={event => setVehicle(previous => ({ ...previous, preferredSize: event.target.value }))}>{sizeOptions.map(item => <option key={item.value} value={item.value}>{item.label}</option>)}</select></div>
                <div className="financial-field"><label htmlFor="vehicle-minimumSeats">최소 탑승 인원 · 필수 조건</label><select id="vehicle-minimumSeats" value={vehicle.minimumSeats} onChange={event => setVehicle(previous => ({ ...previous, minimumSeats: event.target.value }))}><option value="0">미지정</option>{[2, 3, 4, 5, 6, 7, 8, 9].map(value => <option key={value} value={value}>{value}명 이상</option>)}</select></div>
              </div>
              <p>최소 인원을 지정하면 좌석 수 미확인 차량은 제외합니다. 현재 좌석 자료가 부족해 결과가 없을 수 있습니다. 크기 미지정 시 공간 중요도는 점수에 반영하지 않습니다.</p>
            </fieldset>
            <fieldset className="vehicle-purpose">
              <legend>주 이용 목적</legend>
              <div className="vehicle-purpose-options">
                {purposes.map((purpose) => <label key={purpose}>
                  <input type="radio" name="purpose" value={purpose} checked={vehicle.purpose === purpose} onChange={() => { setVehicle((previous) => ({ ...previous, purpose })); }} />
                  <span>{purpose}</span>
                </label>)}
              </div>
            </fieldset>
            <div className="vehicle-fields">
              {vehicleFields.map(({ name, label, options }) => <div className="financial-field" key={name}>
                <label htmlFor={`vehicle-${name}`}>{label}</label>
                <select id={`vehicle-${name}`} name={name} value={vehicle[name]} onChange={(event) => { setVehicle((previous) => ({ ...previous, [name]: event.target.value })); }}>
                  {options.map((option) => <option key={option}>{option}</option>)}
                </select>
              </div>)}
              <div className="financial-field">
                <label htmlFor="vehicle-minimumBuffer">구매 후 최소 월 여유자금</label>
                <div className="financial-input-wrap"><input id="vehicle-minimumBuffer" type="number" min="0" step="0.01" required aria-invalid={Boolean(bufferError)} aria-describedby={bufferError ? 'vehicle-buffer-error' : undefined} onInvalid={(event) => { event.preventDefault(); setBufferError(event.currentTarget.validationMessage); }} value={vehicle.minimumBuffer} onChange={(event) => { setVehicle(previous => ({ ...previous, minimumBuffer: event.target.value })); setBufferError(''); }} /><span>만 원</span></div>
                {bufferError && <p id="vehicle-buffer-error" className="financial-field-error" role="alert">{bufferError}</p>}
                <p>목표 저축과 차량 비용을 제외하고 남길 금액입니다. 없으면 0을 입력하세요.</p>
              </div>
            </div>

          </section>
          <aside className="vehicle-profile" aria-labelledby="vehicle-profile-title">
            <h2 id="vehicle-profile-title">예상 이용 프로필</h2>
            <Car className="vehicle-profile-icon" size={theme.iconSize.lg} aria-hidden="true" />
            <div aria-live="polite">
              <h3>{vehicle.purpose}</h3><p>저축·비상 자금을 유지하고 비용 상승 조건에서도 월 여유자금이 남는 후보만 평가합니다.</p>
              <dl>
                <div><dt>연간 예상 주행</dt><dd>{vehicle.annualDistance}</dd></div>
                <div><dt>월 환산 주행</dt><dd>{Math.round(Number(vehicle.annualDistance.replace(/[^0-9]/g, '')) / 12).toLocaleString('ko-KR')}km</dd></div>
                <div><dt>선호 할부</dt><dd>{vehicle.installment}</dd></div>
                <div><dt>선호 연료</dt><dd>{vehicle.fuel}</dd></div><div><dt>최소 월 여유자금</dt><dd>{vehicle.minimumBuffer || 0}만 원</dd></div>
                <div><dt>가성비 중요도</dt><dd>{importanceLabel(vehicle.costImportance)}</dd></div>
                <div><dt>공간 중요도</dt><dd>{importanceLabel(vehicle.spaceImportance)}</dd></div>
                <div><dt>선호 크기</dt><dd>{sizeLabel(vehicle.preferredSize)}</dd></div>
              </dl>
            </div>
          </aside>
        </div>
        <div className="financial-next-row vehicle-navigation">
          <button type="button" className="vehicle-previous-button" onClick={() => navigate('/financial/assets', { state: { ...state, vehicle } })}>이전</button>
          <button type="submit" className="financial-next-button">{state?.reviewReturn ? '수정 완료' : '다음 단계'}</button>
        </div>

      </form>
    </div>
  );
}
