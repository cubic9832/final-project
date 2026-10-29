import { useEffect, useRef, useState } from 'react';
import { Link } from 'react-router-dom';
import { Car, Target, Wallet, CalendarDays, ShieldCheck, Bookmark, TrendingUp, RotateCcw, CircleHelp } from 'lucide-react';
import catalog from '../../../../../../data/households/synthetic/sports-official-v1-20261028/catalog.json';
import { resolveVehicleImage } from '../../../vehicle/resolveVehicleImage';
import { calculatePurchasePlan, defaultPlan } from '../../purchasePlan';
import { getVehicleCostDefaults, updatePlanInput } from '../../vehicleCostDefaults';
import theme from '../../../../styles/theme';
import './DreamCarPlannerPage.css';

const money = value => `${Math.round(value).toLocaleString('ko-KR')}만 원`;
const fuels = { GASOLINE: '가솔린', HYBRID: '하이브리드', ELECTRIC: '전기', DIESEL: '디젤', LPG: 'LPG' };
const storageKey = 'dream-car-plan-v3';
const models = [...new Set(catalog.map(car => `${car.brand} ${car.model}`))];
function readPlan() {
  try {
    const current = localStorage.getItem(storageKey);
    const saved = JSON.parse(current || localStorage.getItem('dream-car-plan-v2'));
    if (!current && saved?.inputs) {
      const vehicle = catalog.find(car => car.id === saved.vehicleId);
      if (vehicle) Object.assign(saved.inputs, getVehicleCostDefaults(vehicle, saved.inputs.annualDistance).inputs);
    }
    if (saved && catalog.some(car => car.id === saved.vehicleId) && Object.keys(defaultPlan).every(key => Number.isFinite(saved.inputs?.[key]) && saved.inputs[key] >= 0)) return saved;
  } catch { /* 저장된 계획이 없으면 기본 조건으로 시작한다. */ }
  return { vehicleId: catalog[0].id, inputs: { ...defaultPlan, ...getVehicleCostDefaults(catalog[0]).inputs } };
}
function PlanField({ name, label, unit, inputs, onChange, min = 0, max = 100000000 }) {
  const fieldRef = useRef(null);
  useEffect(() => {
    const field = fieldRef.current;
    function preventWheelChange(event) {
      if (document.activeElement === field) event.preventDefault();
    }
    field.addEventListener('wheel', preventWheelChange, { passive: false });
    return () => field.removeEventListener('wheel', preventWheelChange);
  }, []);
  const value = inputs[name];
  const invalid = value === '' || !Number.isFinite(value) || value < min || value > max;
  return <label className="dream-field"><span>{label}</span><div><input ref={fieldRef} type="number" min={min} max={max} step="any" value={value} aria-invalid={invalid} aria-describedby={invalid ? `error-${name}` : undefined} onChange={event => onChange(name, event.target.value === '' ? '' : Number(event.target.value))} /><span>{unit}</span></div>{invalid && <small id={`error-${name}`} role="alert">{min}~{max.toLocaleString()} 범위로 입력해 주세요.</small>}</label>;
}
export default function DreamCarPlannerPage() {
  const [plan, setPlan] = useState(readPlan);
  const [startedAt] = useState(() => Date.now());
  const [query, setQuery] = useState('');
  const [notice, setNotice] = useState('');
  const [failedImage, setFailedImage] = useState('');
  const { vehicleId, inputs } = plan;
  const vehicle = catalog.find(car => car.id === vehicleId) || catalog[0];
  const costDefaults = getVehicleCostDefaults(vehicle, inputs.annualDistance);
  const selectedModel = `${vehicle.brand} ${vehicle.model}`;
  const filteredModels = models.filter(model => model.toLowerCase().includes(query.trim().toLowerCase()));
  const trims = catalog.filter(car => `${car.brand} ${car.model}` === selectedModel);
  const result = calculatePurchasePlan(vehicle.price / 10000, inputs);
  const valid = result && Object.values(inputs).every(value => value !== '' && value <= 100000000) && inputs.targetMonths >= 1 && inputs.efficiency >= 0.1;
  const image = resolveVehicleImage(vehicle)?.src;
  function change(name, value) { setPlan(current => ({ ...current, inputs: updatePlanInput(vehicle, current.inputs, name, value) })); setNotice(''); }
  function selectVehicle(id) {
    const next = catalog.find(car => car.id === id);
    setPlan(current => ({ vehicleId: id, inputs: { ...current.inputs, ...getVehicleCostDefaults(next, current.inputs.annualDistance).inputs } }));
    const nextCosts = getVehicleCostDefaults(next, inputs.annualDistance).inputs;
    const sameModel = next.brand === vehicle.brand && next.model === vehicle.model;
    const taxMessage = nextCosts.annualTax === costDefaults.inputs.annualTax
      ? '자동차세 예산은 이전 선택과 같습니다.'
      : `자동차세 예산은 연 ${money(nextCosts.annualTax)}으로 변경했습니다.`;
    setNotice(`${sameModel ? '트림' : '차량'} 변경을 반영했습니다. ${taxMessage} 연비·보험료·정비비도 선택 사양 기준으로 다시 계산했습니다.`);
  }
  function save() { try { localStorage.setItem(storageKey, JSON.stringify(plan)); setNotice('이 브라우저에 계획을 저장했습니다. 다음 방문에 이어서 볼 수 있어요.'); } catch { setNotice('브라우저 저장 공간을 사용할 수 없습니다.'); } }
  function field(name, label, unit, min) {
    return <PlanField key={name} {...{ name, label, unit, min, inputs }} onChange={change} />;
  }
  let arrival = '저축액을 입력해 주세요';
  if (valid && result.months !== null) {
    const date = new Date(startedAt);
    date.setDate(1);
    date.setMonth(date.getMonth() + result.months);
    arrival = result.months === 0 ? '지금 목표를 달성했어요' : result.months > 1200 ? '100년 이상 · 저축액 조정 필요' : `${date.getFullYear()}년 ${date.getMonth() + 1}월 예상`;
  }
  return <div className="dream-page">
    <header className="dream-heading"><div><span className="dream-eyebrow"><Target size={theme.iconSize.sm} aria-hidden /> DREAM CAR PLAN</span><h1>드림카, 꿈에서 내 차로.</h1><p>갖고 싶은 차를 고르면, 준비해야 할 돈과 시간이 보입니다.</p></div><span className="dream-catalog-count">{models.length}개 모델 · {catalog.length}개 트림</span></header>
    <div className="dream-layout"><div className="dream-inputs">
      <section className="dream-card"><div className="dream-section-title"><span>01</span><h2>나의 드림카</h2><Car size={theme.iconSize.lg} aria-hidden /></div>
        <label className="dream-field"><span>모델 검색</span><input type="search" placeholder="브랜드 또는 모델명으로 검색" value={query} onChange={event => setQuery(event.target.value)} /></label>
        {filteredModels.length ? <label className="dream-field"><span>모델 선택 · 검색 결과 {filteredModels.length}개</span><select value={filteredModels.includes(selectedModel) ? selectedModel : ''} onChange={event => selectVehicle(catalog.find(car => `${car.brand} ${car.model}` === event.target.value).id)}><option value="" disabled>모델을 선택해 주세요</option>{filteredModels.map(model => <option key={model}>{model}</option>)}</select></label> : <p role="status">검색 결과가 없습니다. 다른 모델명을 입력해 주세요.</p>}
        <label className="dream-field"><span>트림 선택</span><select value={vehicleId} onChange={event => selectVehicle(event.target.value)}>{trims.map(car => <option key={car.id} value={car.id}>{car.trim} · {fuels[car.fuel] || car.fuel} · {money(car.price / 10000)}</option>)}</select></label>
        <p className="dream-note">트림 변경 시 연비·보험료·자동차세·정비비를 다시 계산합니다. 같은 배기량의 편의사양 트림은 자동차세가 같을 수 있습니다. 배기량 미확인 차량의 세금 예산은 트림 가격에 따른 추정값입니다.</p><div className="dream-vehicle">{image && failedImage !== image ? <img src={image} alt={`${vehicle.brand} ${vehicle.model}`} onError={() => setFailedImage(image)} /> : <Car size={theme.iconSize.lg} aria-hidden />}<div><small>{vehicle.brand} · {vehicle.year}년형</small><h3>{vehicle.model}</h3><p>{vehicle.trim} · {fuels[vehicle.fuel] || vehicle.fuel}</p><strong>{money(vehicle.price / 10000)}</strong></div></div>
        <p className="dream-note">등록 카탈로그 기준 · {vehicle.checked_on || '기준일 미등록'}{vehicle.source_url && <> · <a href={vehicle.source_url} target="_blank" rel="noreferrer">차량 정보 출처</a></>}</p>
      </section>
      <section className="dream-card"><div className="dream-section-title"><span>02</span><h2>나의 저축 계획</h2><Wallet size={theme.iconSize.lg} aria-hidden /></div><div className="dream-fields">{field('savings', '차 구매용으로 모은 돈', '만 원')}{field('monthlySaving', '매월 저축할 금액', '만 원')}{field('targetMonths', '목표까지 남은 기간', '개월', 1)}{field('reserveMonths', '구매 후 유지비 예비자금', '개월')}</div><p className="dream-note">생활비 비상금은 제외하고, 차량에 쓸 수 있는 자금만 입력하세요.</p><div className="dream-savings-actions"><button type="button" className="dream-reset dream-savings-reset" onClick={() => { setPlan(current => ({ ...current, inputs: { ...current.inputs, savings: defaultPlan.savings, monthlySaving: defaultPlan.monthlySaving, targetMonths: defaultPlan.targetMonths, reserveMonths: defaultPlan.reserveMonths } })); setNotice('저축 계획을 기본값으로 초기화했습니다.'); }}>초기화</button></div></section>
      <section className="dream-card"><div className="dream-section-title"><span>03</span><h2>구매·유지비 가정</h2><Link className="dream-help" to={`/dream-car/calculation-guide?vehicle=${encodeURIComponent(vehicleId)}&distance=${encodeURIComponent(inputs.annualDistance)}`} target="_blank" rel="noreferrer" aria-label="구매·유지비 계산 기준 안내 (새 탭)" title="계산 기준 보기"><CircleHelp size={theme.iconSize.md} aria-hidden /></Link></div><p className="dream-estimate-note">* 자동 입력된 금액과 수치는 구매 계획을 위한 예상치로, 실제 비용과 다를 수 있습니다.</p><div className="dream-fields">{field('annualDistance', '연간 주행거리', 'km')}{field('efficiency', vehicle.fuel === 'ELECTRIC' ? '전비' : '연비', vehicle.fuel === 'ELECTRIC' ? 'km/kWh' : 'km/L', 0.1)}{field('energyPrice', vehicle.fuel === 'ELECTRIC' ? '충전 단가' : '연료 단가', vehicle.fuel === 'ELECTRIC' ? '원/kWh' : '원/L')}{field('insurance', '연간 보험료', '만 원')}{field('annualTax', '연간 자동차세', '만 원')}{field('maintenance', '연간 정비·소모품', '만 원')}{field('parking', '월 주차·기타 비용', '만 원')}{field('registrationRate', '취득·등록 비용 가정', '%')}{field('extras', '옵션·기타 초기비용', '만 원')}</div><div className="dream-savings-actions"><button className="dream-reset dream-restore-defaults" onClick={() => { setPlan(current => ({ ...current, inputs: { ...current.inputs, ...costDefaults.inputs } })); setNotice('선택 차량의 자동 계산값을 다시 적용했습니다.'); }}>차량 기준값 다시 적용</button></div></section>
    </div><aside className="dream-results" aria-label="구매 계획 결과">
    {valid ? <><section className="dream-summary"><span className="dream-eyebrow"><CalendarDays size={theme.iconSize.sm} aria-hidden /> MY DREAM TIMELINE</span><p className="dream-summary-label">드림카를 위한 준비 자금</p><strong className="dream-big">{money(result.target)}</strong><p>차량 구매비 + {inputs.reserveMonths}개월 유지비 예비자금</p><div className="dream-progress-label"><span>목표 달성률</span><strong>{Math.floor(result.progress)}%</strong></div><progress value={result.progress} max="100" aria-label="구매 자금 달성률" /><div className="dream-summary-bottom"><div><small>앞으로 모을 돈</small><strong>{money(result.remaining)}</strong></div><div><small>현재 저축 속도로</small><strong>{result.months === null ? '기간 산출 불가' : `${result.months}개월`}</strong></div></div><div className="dream-arrival">{arrival}</div></section>
      <section className="dream-card"><h2>내 차가 된 뒤, 한 달에</h2><strong className="dream-monthly">{money(result.monthlyTotal)}</strong><p className="dream-note">현금 구매 기준 · 할부금 제외 · 연 {inputs.annualDistance.toLocaleString('ko-KR')}km 반영</p><dl className="dream-breakdown">{Object.entries(result.monthlyCosts).map(([key, amount]) => <div key={key}><dt>{{ energy: vehicle.fuel === 'ELECTRIC' ? '충전비' : '연료비', insurance: '보험료', tax: '자동차세', maintenance: '정비·소모품', parking: '주차·기타' }[key]}</dt><dd>{money(amount)}</dd></div>)}</dl><div className="dream-reserve"><ShieldCheck size={theme.iconSize.md} aria-hidden /><span>{inputs.reserveMonths}개월 예비자금 <strong>{money(result.reserve)}</strong></span></div></section>
      <section className="dream-card dream-insight"><TrendingUp size={theme.iconSize.lg} aria-hidden /><h2>꿈에 조금 더 가까이</h2><p>{inputs.targetMonths}개월 안에 구매하려면 월 <strong>{money(result.requiredMonthly)}</strong>을 모으면 돼요.</p><p>매월 30만 원 더 저축하면 <strong>{result.months === null ? `${result.fasterMonths}개월 후 도달` : `${Math.max(0, result.months - result.fasterMonths)}개월 단축`}</strong>할 수 있어요.</p><p>구매 후에도 월 <strong>{money(result.monthlyTotal)}</strong>의 여유자금이 있는지 확인하세요.</p></section>
      <section className="dream-card"><h2>준비 자금 자세히 보기</h2><dl className="dream-breakdown">{[['차량 가격', vehicle.price / 10000], ['취득·등록 비용 가정', result.registration], ['옵션·기타 초기비용', inputs.extras], ['유지비 예비자금', result.reserve], ['구매 + 첫 1년 유지비', result.firstYear]].map(([label, value]) => <div key={label}><dt>{label}</dt><dd>{money(value)}</dd></div>)}</dl><p className="dream-note">첫 1년 비용에는 예비자금을 중복 합산하지 않습니다. 저축 이자·차량 가격 변동·감가상각은 반영하지 않습니다.</p></section></> : <section className="dream-card" role="status"><h2>입력값을 확인해 주세요</h2><p>모든 항목에 유효한 숫자를 입력하면 계획을 계산합니다.</p></section>}
      <button className="dream-save" onClick={save} disabled={!valid}><Bookmark size={theme.iconSize.sm} aria-hidden />내 구매 계획 저장</button><button className="dream-reset" onClick={() => { setPlan({ vehicleId: catalog[0].id, inputs: { ...defaultPlan, ...getVehicleCostDefaults(catalog[0]).inputs } }); setQuery(''); setNotice('입력값을 초기화했습니다. 저장된 계획은 저장 버튼을 눌러 갱신할 수 있습니다.'); }}><RotateCcw size={theme.iconSize.sm} aria-hidden />입력값 초기화</button><p className="dream-note" role="status">{notice || '계획은 로그인 없이 이 브라우저에 저장할 수 있습니다.'}</p>
    </aside></div>
  </div>;
}
