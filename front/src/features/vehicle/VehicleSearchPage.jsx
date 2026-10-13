import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import VehicleCard from './VehicleCard';
import VehicleArtwork from './VehicleArtwork';
import { useVehicle } from './useVehicle';
import { calculateCosts, formatAmount } from './vehicleData';
import './VehiclePages.css';

const fields = [['income', '월 실수령액'], ['expenses', '월 고정지출'], ['debt', '기존 월 상환액'], ['cash', '보유 현금·예금'], ['downPayment', '원하는 선수금'], ['limit', '월 차량비 한도']];
export function VehicleSearchPage() {
  const { vehicles, conditions, setConditions } = useVehicle();
  const [draft, setDraft] = useState(conditions);
  const [error, setError] = useState('');
  const navigate = useNavigate();
  const available = calculateCosts(vehicles[0], draft).available;
  function submit(event) {
    event.preventDefault();
    if (fields.some(([key]) => draft[key] === '' || !Number.isFinite(Number(draft[key])) || Number(draft[key]) < 0) || Number(draft.income) <= 0 || Number(draft.limit) <= 0) { setError('금액을 모두 입력하고 월 실수령액과 월 차량비 한도는 0보다 크게 입력해 주세요.'); return; }
    if (Number(draft.downPayment) > Number(draft.cash)) { setError('선수금은 보유 현금·예금 이하로 입력해 주세요.'); return; }
    setConditions(Object.fromEntries(Object.entries(draft).map(([key, value]) => [key, key === 'condition' ? value : Number(value)])));
    navigate('/vehicles');
  }
  return <div className="vehicle-page"><div className="vehicle-heading"><h1>차량 찾기</h1><p>사회초년생의 재무상태에 맞는 차량을 조건별로 찾아보세요.</p></div><form onSubmit={submit} className="vehicle-search-grid"><section className="panel"><h2>재무상태 조건</h2><p className="muted">입력값은 차량 구매 여력을 살펴보기 위한 예시 조건입니다.</p><div className="vehicle-fields">{fields.map(([key, label]) => <label key={key}>{label}<div className="vehicle-input"><input aria-describedby={error ? 'condition-error' : undefined} required type="number" min={key === 'income' || key === 'limit' ? 1 : 0} max="1000000" value={draft[key]} onChange={(event) => setDraft({ ...draft, [key]: event.target.value === '' ? '' : Number(event.target.value) })} /><span>만 원</span></div></label>)}</div><fieldset className="vehicle-choice"><legend>차량 구분</legend>{['상관없음', '신차', '중고차'].map((type) => <button key={type} type="button" aria-pressed={draft.condition === type} onClick={() => setDraft({ ...draft, condition: type })}>{type}</button>)}</fieldset><div className="vehicle-note mint"><small>예상 월 가용자금</small><strong>{formatAmount(available)}</strong><small>소득에서 고정지출·기존 상환액을 뺀 금액의 40%</small></div>{error && <p id="condition-error" role="alert" className="vehicle-error">{error}</p>}</section><aside className="vehicle-summary panel"><h2>검색 조건 요약</h2><p>현재 조건으로 부담 가능한 차량을<br />우선순위에 맞춰 추천합니다.</p>{[['구매 예산', `${formatAmount(Number(draft.downPayment) + Number(draft.limit) * 30)} 내외`], ['월 차량비', `${formatAmount(Number(draft.limit))} 이하`], ['선수금', formatAmount(Number(draft.downPayment))], ['대출 부담', '기존 상환액 반영']].map(([label, value]) => <div className="summary-item" key={label}><small>{label}</small><strong>{value}</strong></div>)}<button className="vehicle-button cta" type="submit">조건에 맞는 차량 찾기</button></aside></form><section className="vehicle-candidates"><h2>조건에 맞는 차량 후보</h2><p className="muted">예산과 월 부담을 함께 고려한 예시 차량입니다.</p><div className="vehicle-grid">{vehicles.slice(0, 3).map((vehicle) => <Link className="panel candidate" key={vehicle.id} to={`/vehicles/${vehicle.id}`}><VehicleArtwork vehicle={vehicle} /><h3>{vehicle.type}</h3><p className="vehicle-detail-link">상세 조건 확인</p></Link>)}</div></section><p className="vehicle-disclaimer">금액과 추천 결과는 서비스 흐름 확인을 위한 예시값입니다.</p></div>;
}
export function VehicleResultsPage() {
  const { vehicles, conditions, comparison } = useVehicle();
  const [onlyFavorites, setOnlyFavorites] = useState(false);
  const { favorites } = useVehicle();
  const results = vehicles.filter((vehicle) => (conditions.condition === '상관없음' || vehicle.condition === conditions.condition) && (!onlyFavorites || favorites.includes(vehicle.id))).sort((a, b) => calculateCosts(b, conditions).score - calculateCosts(a, conditions).score);
  return <div className="vehicle-page"><div className="vehicle-heading split"><div><h1>추천 차량</h1><p>재무상태와 차량 이용 목적을 바탕으로 고른 추천 차량입니다.</p></div><span className="vehicle-badge">총 {results.length}대 추천</span></div><div className="vehicle-toolbar"><Link className="vehicle-button" to="/search">검색 조건 변경</Link><label><input type="checkbox" checked={onlyFavorites} onChange={(event) => setOnlyFavorites(event.target.checked)} /> 관심차량만 보기</label><Link className="vehicle-button primary" to="/vehicles/compare">차량 비교 ({comparison.length}/3)</Link></div>{results.length ? <div className="vehicle-grid">{results.map((vehicle) => <VehicleCard key={vehicle.id} vehicle={vehicle} />)}</div> : <div className="panel vehicle-empty"><h2>조건에 맞는 차량이 없습니다.</h2><p>검색 조건이나 관심차량 필터를 변경해 주세요.</p><button className="vehicle-button" onClick={() => setOnlyFavorites(false)}>전체 차량 보기</button></div>}<div className="vehicle-note warning"><strong>안내</strong><p>차량 가격과 연비, 적합도는 화면 구성 검토를 위한 예시이며 실제 구매 전 확인이 필요합니다.</p></div></div>;
}
