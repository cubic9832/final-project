import { useState } from 'react';
import { Link, useLocation, useNavigate } from 'react-router-dom';
import { Search } from 'lucide-react';
import { useVehicle } from '../features/vehicle/useVehicle';
import { calculateVehicleBudget } from '../features/financial/calculateVehicleBudget';
import VehicleArtwork from '../features/vehicle/VehicleArtwork';
import { formatAmount } from '../features/vehicle/vehicleData';
import './FinancialVehicleRecommendationsPage.css';

export function getFinancialRecommendations(state, vehicles = []) {
  const budget = calculateVehicleBudget(state ?? {});
  const inputs = [...Object.values(state?.values ?? {}), ...Object.values(state?.assets ?? {})];
  const valid = budget.valid && inputs.every((value) => Number.isFinite(Number(value)) && Number(value) >= 0)
    && budget.income > 0 && Number.isFinite(budget.high) && budget.months >= 0;
  const monthlyRate = budget.annualRate / 12;
  const preferences = state?.vehicle ?? {};
  const candidates = valid ? vehicles.filter((vehicle) => vehicle.price <= budget.high
    && (preferences.purchase !== '신차만' || vehicle.condition === '신차')
    && (preferences.purchase !== '중고차만' || vehicle.condition === '중고차')
    && (!preferences.body || (preferences.body === '경차 · 소형 · 준중형' ? /경차|소형|준중형/.test(vehicle.type) : preferences.body === '중형 · 대형' ? /중형|대형/.test(vehicle.type) && !vehicle.type.includes('준중형') : preferences.body === '승합차' ? vehicle.type.includes('승합') : vehicle.type.includes(preferences.body)))
    && (!preferences.fuel || preferences.fuel === '상관없음' || preferences.fuel === '가솔린 · 하이브리드'
      || (preferences.fuel === '하이브리드' ? /하이브리드/.test(`${vehicle.name} ${vehicle.trim}`) : preferences.fuel === '가솔린' && !/하이브리드/.test(`${vehicle.name} ${vehicle.trim}`))))
    .map((vehicle) => {
    const principal = Math.max(0, vehicle.price - budget.downPayment);
    const installment = budget.months === 0 ? 0 : principal * monthlyRate / (1 - (1 + monthlyRate) ** -budget.months);
    return { ...vehicle, installment, monthlyCost: installment + budget.operatingCost,
      margin: budget.high > 0 ? Math.round((1 - vehicle.price / budget.high) * 100) : 0 };
  }).sort((a, b) => b.margin - a.margin || b.efficiency - a.efficiency) : [];
  return { valid, budget, vehicles: candidates };
}

const types = ['전체', '경차', '세단', 'SUV', '승합', '하이브리드'];

export default function FinancialVehicleRecommendationsPage() {
  const { state } = useLocation();
  const navigate = useNavigate();
  const { vehicles, catalogStatus, catalogError, retryCatalog } = useVehicle();
  const [query, setQuery] = useState('');
  const [type, setType] = useState('전체');
  const [sort, setSort] = useState('margin');
  const analysis = getFinancialRecommendations(state, vehicles);
  if (!analysis.valid) return <section className="financial-vehicle-recommendations fvr-message"><h1>재무 조건을 입력해 주세요</h1><p>종합 분석 결과에서 추천 차량 확인하기를 선택해 주세요.</p><Link to="/financial" state={state}>재무 정보 입력</Link></section>;
  if (catalogStatus !== 'ready') return <section className="financial-vehicle-recommendations fvr-message" role="status"><h1>{catalogStatus === 'error' ? '차량 정보를 불러오지 못했어요' : '차량 정보를 확인하고 있어요'}</h1><p>{catalogError}</p>{catalogStatus === 'error' && <button onClick={retryCatalog}>다시 시도</button>}</section>;
  const results = analysis.vehicles.filter((vehicle) => `${vehicle.name} ${vehicle.trim}`.toLowerCase().includes(query.toLowerCase())
    && (type === '전체' || (type === '하이브리드' ? vehicle.name.includes('하이브리드') || vehicle.trim.includes('하이브리드') : vehicle.type.includes(type))))
    .sort((a, b) => sort === 'price' ? a.price - b.price : sort === 'efficiency' ? b.efficiency - a.efficiency : sort === 'cost' ? a.monthlyCost - b.monthlyCost : b.margin - a.margin);
  return <div className="financial-vehicle-recommendations">
    <header><h1>추천 차량</h1><p>입력한 재무 조건의 구매 예산을 기준으로 차량을 확인하세요.</p><span className="fvr-summary">구매 예산 {formatAmount(analysis.budget.high)} · 선수금 {formatAmount(analysis.budget.downPayment)} · {analysis.budget.months ? `${analysis.budget.months}개월 할부` : '일시불'}</span></header>
    <div className="fvr-toolbar"><label className="fvr-search"><Search size={16} aria-hidden="true" /><input value={query} onChange={(event) => setQuery(event.target.value)} placeholder="차량 이름·브랜드·트림 검색" aria-label="추천 차량 검색" /></label><label className="fvr-sort"><span className="fvr-sr-only">정렬 기준</span><select value={sort} onChange={(event) => setSort(event.target.value)}><option value="margin">예산 여유순</option><option value="price">가격 낮은순</option><option value="cost">유지 부담 낮은순</option><option value="efficiency">연비 높은순</option></select></label></div>
    <div className="fvr-filters" aria-label="차량 유형 필터">{types.map((item) => <button key={item} aria-pressed={type === item} onClick={() => setType(item)}>{item}</button>)}</div>
    <div className="fvr-list-heading"><h2>조건에 맞는 차량 {results.length}대</h2><small>차량을 선택하면 상세 화면으로 이동합니다.</small></div>
    {results.length ? <div className="fvr-grid">{results.map((vehicle) => <Link className="fvr-card" key={vehicle.id} to={`/vehicles/${vehicle.id}`}>
      <div className="fvr-image"><VehicleArtwork vehicle={vehicle} photo /></div><span className="fvr-badge">예산 여유 {vehicle.margin}%</span><h3>{vehicle.name}</h3><p>{formatAmount(vehicle.price)} · {vehicle.condition}</p><p className="fvr-trim">{vehicle.trim}</p>
      <dl><div><dt>월 할부금</dt><dd>{formatAmount(vehicle.installment)}</dd></div><div><dt>월 유지비 가정</dt><dd>{formatAmount(analysis.budget.operatingCost)}</dd></div><div><dt>복합연비</dt><dd>{vehicle.efficiency}km/L</dd></div></dl>
      <div className="fvr-reason"><strong>추천 이유</strong><p>입력한 구매 예산 안에서 선택할 수 있고, 월 차량 비용은 약 {formatAmount(vehicle.monthlyCost)}입니다.</p></div>
    </Link>)}</div> : <section className="fvr-message" role="status"><h2>조건에 맞는 차량이 없습니다.</h2><p>{analysis.vehicles.length ? '검색어나 차량 유형을 변경해 주세요.' : '재무 조건과 구매 예산을 다시 확인해 주세요.'}</p><button onClick={() => { setQuery(''); setType('전체'); }}>검색 필터 초기화</button><button onClick={() => navigate('/financial', { state: { ...state, reviewReturn: false } })}>입력 조건 수정</button></section>}
    <p className="fvr-disclaimer">연 금리 6%·월 유지비 20만 원의 참고 계산입니다. 예산 여유는 구매 예산 대비 가격 차이이며 신용점수나 머신러닝 추천 확률이 아닙니다.</p>
    <footer><Link to="/financial/result" state={state}>종합 분석 결과</Link><Link to="/vehicles/compare">차량 비교하기</Link></footer>
  </div>;
}
