import { useEffect, useRef, useState } from 'react';
import { Link } from 'react-router-dom';
import { Car, Wallet, ShieldCheck, Bookmark, TrendingUp, RotateCcw, CircleHelp } from 'lucide-react';
import catalog from '../../../vehicle/planningVehicleCatalog.json';
import DreamCarPreview from '../../components/DreamCarPreview';
import { calculatePurchasePlan, defaultPlan } from '../../purchasePlan';
import { getVehicleCostDefaults, updatePlanInput } from '../../vehicleCostDefaults';
import theme from '../../../../styles/theme';
import './DreamCarPlannerPage.css';
import DreamCarTabs from '../../components/DreamCarTabs';
import DreamCarPageHeader from '../../components/DreamCarPageHeader';
import PurchaseFundingSummary from '../../components/PurchaseFundingSummary';
import PurchasePlanInsight from '../../components/PurchasePlanInsight';
import { purchasePlanUpdatedEvent, savePurchasePlanWithProgress } from '../../purchasePlanSync';
import { currentDate } from '../../savingsProgress';

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
    const savedVehicle = catalog.find(car => car.id === saved?.vehicleId);
    if (savedVehicle && saved.inputs && (!Number.isFinite(saved.inputs.efficiency) || saved.inputs.efficiency <= 0)) saved.inputs.efficiency = getVehicleCostDefaults(savedVehicle).inputs.efficiency;
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
  useEffect(() => {
    function sync(event) { if (!event.key || event.key === storageKey) setPlan(readPlan()); }
    window.addEventListener('storage', sync);
    window.addEventListener(purchasePlanUpdatedEvent, sync);
    return () => { window.removeEventListener('storage', sync); window.removeEventListener(purchasePlanUpdatedEvent, sync); };
  }, []);
  const [startedAt] = useState(() => Date.now());
  const [query, setQuery] = useState('');
  const [notice, setNotice] = useState('');
  const { vehicleId, inputs } = plan;
  const vehicle = catalog.find(car => car.id === vehicleId) || catalog[0];
  const costDefaults = getVehicleCostDefaults(vehicle, inputs.annualDistance);
  const selectedModel = `${vehicle.brand} ${vehicle.model}`;
  const filteredModels = models.filter(model => model.toLowerCase().includes(query.trim().toLowerCase()));
  const trims = catalog.filter(car => `${car.brand} ${car.model}` === selectedModel);
  const result = calculatePurchasePlan(vehicle.price / 10000, inputs);
  const valid = result && Object.values(inputs).every(value => value !== '' && value <= 100000000) && inputs.targetMonths >= 1 && inputs.efficiency >= 0.1;
  function change(name, value) { setPlan(current => ({ ...current, inputs: updatePlanInput(vehicle, current.inputs, name, value) })); setNotice(''); }
  function selectVehicle(id) {
    const next = catalog.find(car => car.id === id);
    setPlan(current => ({ vehicleId: id, inputs: { ...current.inputs, ...getVehicleCostDefaults(next, current.inputs.annualDistance).inputs } }));
    setNotice('');
  }
  function save() {
    try {
      savePurchasePlanWithProgress(plan, result.target, currentDate(), vehicle);
      setNotice('현재 설정을 저장하고 저축 실행 현황에도 반영했습니다.');
    } catch (error) { setNotice(error.message || '브라우저 저장 공간을 사용할 수 없습니다.'); }
  }
  function field(name, label, unit, min) {
    return <PlanField key={name} {...{ name, label, unit, min, inputs }} onChange={change} />;
  }
  return <div className="dream-page">
    <DreamCarPageHeader eyebrow="DREAM CAR PLAN" title="드림카, 꿈에서 내 차로." description="갖고 싶은 차를 고르면, 준비해야 할 돈과 시간이 보입니다." />
    <DreamCarTabs />
    <div className="dream-layout"><div className="dream-inputs">
      <section className="dream-card"><div className="dream-section-title"><span>01</span><h2>나의 드림카</h2><Car size={theme.iconSize.lg} aria-hidden /></div>
        <label className="dream-field"><span>모델 검색</span><input type="search" placeholder="브랜드 또는 모델명으로 검색" value={query} onChange={event => setQuery(event.target.value)} /></label>
        {filteredModels.length ? <label className="dream-field"><span>모델 선택 · 검색 결과 {filteredModels.length}개</span><select value={filteredModels.includes(selectedModel) ? selectedModel : ''} onChange={event => selectVehicle(catalog.find(car => `${car.brand} ${car.model}` === event.target.value).id)}><option value="" disabled>모델을 선택해 주세요</option>{filteredModels.map(model => <option key={model}>{model}</option>)}</select></label> : <p role="status">검색 결과가 없습니다. 다른 모델명을 입력해 주세요.</p>}
        <label className="dream-field"><span>트림 선택</span><select value={vehicleId} onChange={event => selectVehicle(event.target.value)}>{trims.map(car => <option key={car.id} value={car.id}>{car.trim} · {fuels[car.fuel] || car.fuel} · {money(car.price / 10000)}</option>)}</select></label>
        <DreamCarPreview vehicle={vehicle} />
        <p className="dream-note">등록 카탈로그 기준 · {vehicle.checked_on || '기준일 미등록'}{vehicle.source_url && <> · <a href={vehicle.source_url} target="_blank" rel="noreferrer">차량 정보 출처</a></>}</p>
      </section>
      <section className="dream-card"><div className="dream-section-title"><span>02</span><h2>나의 저축 계획</h2><Wallet size={theme.iconSize.lg} aria-hidden /></div><div className="dream-fields">{field('savings', '차 구매용으로 모은 돈', '만 원')}{field('monthlySaving', '매월 저축할 금액', '만 원')}{field('targetMonths', '목표까지 남은 기간', '개월', 1)}{field('reserveMonths', '구매 후 유지비 예비자금', '개월')}</div><div className="dream-savings-actions"><button type="button" className="dream-save dream-savings-reset" disabled={!valid} onClick={save}>현재 설정 저장</button><button type="button" className="dream-reset dream-savings-reset" onClick={() => { setPlan(current => ({ ...current, inputs: { ...current.inputs, savings: defaultPlan.savings, monthlySaving: defaultPlan.monthlySaving, targetMonths: defaultPlan.targetMonths, reserveMonths: defaultPlan.reserveMonths } })); setNotice('저축 계획을 기본값으로 초기화했습니다.'); }}>초기화</button></div></section>
      <section className="dream-card"><div className="dream-section-title"><span>03</span><h2>구매·유지비 가정</h2><Link className="dream-help" to={`/dream-car/calculation-guide?vehicle=${encodeURIComponent(vehicleId)}&distance=${encodeURIComponent(inputs.annualDistance)}`} target="_blank" rel="noreferrer" aria-label="구매·유지비 계산 기준 안내 (새 탭)" title="계산 기준 보기"><CircleHelp size={theme.iconSize.md} aria-hidden /></Link></div><p className="dream-estimate-note">* 자동 입력된 금액과 수치는 구매 계획을 위한 예상치로, 실제 비용과 다를 수 있습니다.</p><div className="dream-fields">{field('annualDistance', '연간 주행거리', 'km')}{field('efficiency', (vehicle.fuel === 'ELECTRIC' ? '전비' : '연비') + (costDefaults.efficiencyEstimated ? ' (추정)' : ''), vehicle.fuel === 'ELECTRIC' ? 'km/kWh' : 'km/L', 0.1)}{field('energyPrice', vehicle.fuel === 'ELECTRIC' ? '충전 단가' : '연료 단가', vehicle.fuel === 'ELECTRIC' ? '원/kWh' : '원/L')}{field('insurance', '연간 보험료', '만 원')}{field('annualTax', '연간 자동차세', '만 원')}{field('maintenance', '연간 정비·소모품', '만 원')}{field('parking', '월 주차·기타 비용', '만 원')}{field('registrationRate', '취득·등록 비용 가정', '%')}{field('extras', '옵션·기타 초기비용', '만 원')}</div><div className="dream-savings-actions"><button type="button" className="dream-save dream-savings-reset" disabled={!valid} onClick={save}>현재 설정 저장</button><button className="dream-reset dream-restore-defaults" onClick={() => { setPlan(current => ({ ...current, inputs: { ...current.inputs, ...costDefaults.inputs } })); setNotice('선택 차량의 자동 계산값을 다시 적용했습니다.'); }}>차량 기준값 다시 적용</button></div></section>
    </div><aside className="dream-results" aria-label="구매 계획 결과">
    {valid ? <><PurchaseFundingSummary result={result} inputs={inputs} baseDate={startedAt} />
      <PurchasePlanInsight result={result} inputs={inputs} />
      <section className="dream-card"><h2>내 차가 된 뒤, 한 달에</h2><strong className="dream-monthly">{money(result.monthlyTotal)}</strong><p className="dream-note">현금 구매 기준 · 할부금 제외 · 연 {inputs.annualDistance.toLocaleString('ko-KR')}km 반영</p><dl className="dream-breakdown">{Object.entries(result.monthlyCosts).map(([key, amount]) => <div key={key}><dt>{{ energy: vehicle.fuel === 'ELECTRIC' ? '충전비' : '연료비', insurance: '보험료', tax: '자동차세', maintenance: '정비·소모품', parking: '주차·기타' }[key]}</dt><dd>{money(amount)}</dd></div>)}</dl><div className="dream-reserve"><ShieldCheck size={theme.iconSize.md} aria-hidden /><span>{inputs.reserveMonths}개월 예비자금 <strong>{money(result.reserve)}</strong></span></div></section>
      <section className="dream-card"><h2>준비 자금 자세히 보기</h2><dl className="dream-breakdown">{[['차량 가격', vehicle.price / 10000], ['취득·등록 비용 가정', result.registration], ['옵션·기타 초기비용', inputs.extras], ['유지비 예비자금', result.reserve], ['구매 + 첫 1년 유지비', result.firstYear]].map(([label, value]) => <div key={label}><dt>{label}</dt><dd>{money(value)}</dd></div>)}</dl></section></> : <section className="dream-card" role="status"><h2>입력값을 확인해 주세요</h2><p>모든 항목에 유효한 숫자를 입력하면 계획을 계산합니다.</p></section>}
      <button className="dream-save" onClick={save} disabled={!valid}><Bookmark size={theme.iconSize.sm} aria-hidden />내 구매 계획 저장</button><Link className="dream-progress-link" to="/dream-car/progress"><TrendingUp size={theme.iconSize.sm} aria-hidden />저축 기록하고 계획과 비교하기</Link><button className="dream-reset" onClick={() => { setPlan({ vehicleId: catalog[0].id, inputs: { ...defaultPlan, ...getVehicleCostDefaults(catalog[0]).inputs } }); setQuery(''); setNotice('입력값을 초기화했습니다. 저장된 계획은 저장 버튼을 눌러 갱신할 수 있습니다.'); }}><RotateCcw size={theme.iconSize.sm} aria-hidden />입력값 초기화</button><p className="dream-note" role="status">{notice}</p>
    </aside></div>
  </div>;
}
