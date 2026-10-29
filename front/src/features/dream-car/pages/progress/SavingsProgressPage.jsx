import { useEffect, useState } from 'react';
import { CalendarDays, ChartNoAxesCombined, Flag, Target, Trophy, Wallet } from 'lucide-react';
import catalog from '../../../vehicle/planningVehicleCatalog.json';
import { calculatePurchasePlan } from '../../purchasePlan';
import SavedPurchasePlanSection from './SavedPurchasePlanSection';
import { calculateSavingsProgress, createProgressPlan, currentDate, deleteSavingRecord, formatMoney, getSavingRecords, isProgressPlan, monthIndex, planStorageKey, progressStorageKey, shiftMonth } from '../../savingsProgress';
import theme from '../../../../styles/theme';
import SavingsProgressChart from './SavingsProgressChart';
import DailySavingForm from './DailySavingForm';
import RecurringSavingsSettings from './RecurringSavingsSettings';
import { applyRecurringSavings, isRecurringRule } from '../../recurringSavings';
import { purchasePlanUpdatedEvent, syncSavedSavings } from '../../purchasePlanSync';
import SavingsRecordHistory from './SavingsRecordHistory';
import DreamCarTabs from '../../components/DreamCarTabs';
import DreamCarPageHeader from '../../components/DreamCarPageHeader';
import './SavingsProgressPage.css';

function readProgress() {
  try {
    const raw = localStorage.getItem(progressStorageKey);
    if (!raw) return { plans: [], error: '' };
    const plans = JSON.parse(raw);
    if (!Array.isArray(plans) || !plans.every(plan => isProgressPlan(plan) && (plan.recurringRules === undefined || Array.isArray(plan.recurringRules) && plan.recurringRules.every(isRecurringRule)))) throw new Error();
    const updated = plans.map(plan => applyRecurringSavings(plan, currentDate()));
    if (updated.some((plan, index) => plan !== plans[index])) localStorage.setItem(progressStorageKey, JSON.stringify(updated));
    return { plans: updated, error: '' };
  } catch { return { plans: [], error: '저장된 실행 기록을 읽을 수 없습니다. 브라우저 저장 공간 또는 데이터 상태를 확인해 주세요. 기존 데이터를 덮어쓰지 않았습니다.' }; }
}
function readSavedPlan() {
  try {
    const saved = JSON.parse(localStorage.getItem(planStorageKey));
    const vehicle = catalog.find(car => car.id === saved?.vehicleId);
    const result = vehicle && saved?.inputs && calculatePurchasePlan(vehicle.price / 10000, saved.inputs);
    if (result && Number.isInteger(saved.inputs.targetMonths) && saved.inputs.targetMonths > 0) return { saved, vehicle, target: result.target };
  } catch { /* 구매 계획이 없거나 올바르지 않으면 새 계획 저장을 안내한다. */ }
  return null;
}
export default function SavingsProgressPage() {
  const [asOfDate, setAsOfDate] = useState(currentDate);
  const asOfMonth = asOfDate.slice(0, 7);
  const [editingId, setEditingId] = useState(null);
  const [state, setState] = useState(readProgress);
  useEffect(() => {
    function refresh() { setAsOfDate(currentDate()); setState(readProgress()); }
    const timer = window.setInterval(refresh, 60000);
    window.addEventListener('focus', refresh);
    return () => { window.clearInterval(timer); window.removeEventListener('focus', refresh); };
  }, []);
  const [savedPlan, setSavedPlan] = useState(readSavedPlan);
  useEffect(() => {
    function refreshSaved() { setSavedPlan(readSavedPlan()); setState(readProgress()); }
    window.addEventListener('storage', refreshSaved);
    window.addEventListener(purchasePlanUpdatedEvent, refreshSaved);
    return () => { window.removeEventListener('storage', refreshSaved); window.removeEventListener(purchasePlanUpdatedEvent, refreshSaved); };
  }, []);
  const [notice, setNotice] = useState('');
  const plan = state.plans.at(-1);
  const summary = plan ? calculateSavingsProgress(plan, asOfMonth) : null;
  const editingRecord = plan ? getSavingRecords(plan).find(record => record.id === editingId) : null;
  function persist(plans, message) {
    if (state.error) { setNotice('저장된 데이터 오류를 먼저 확인해 주세요. 기존 기록을 덮어쓰지 않았습니다.'); return false; }
    try { localStorage.setItem(progressStorageKey, JSON.stringify(plans)); setState({ plans, error: '' }); setNotice(message); return true; } catch { setNotice('저장 공간을 사용할 수 없어 저장하지 못했습니다. 입력값을 유지했으니 다시 시도해 주세요.'); return false; }
  }
  function start(settings) {
    if (!savedPlan) return false;
    try {
      const next = createProgressPlan(savedPlan.vehicle, { ...savedPlan.saved.inputs, savings: settings.initialSavings, monthlySaving: settings.monthlySaving, targetMonths: settings.targetMonths }, savedPlan.target, settings.startDate, crypto.randomUUID());
      next.purchaseInputs = { ...savedPlan.saved.inputs };
      syncSavedSavings({ savings: settings.initialSavings, monthlySaving: settings.monthlySaving, targetMonths: settings.targetMonths - Math.max(0, monthIndex(asOfMonth) - monthIndex(settings.startMonth)) });
      if (persist([...state.plans, next], '새 실행 계획을 만들었습니다. 시작 자금은 다시 저축 기록에 더하지 마세요.')) { setEditingId(null); return true; }
    } catch (failure) { setNotice(failure.message); }
    return false;
  }
  function update(settings) {
    if (!plan || settings.id !== plan.id) return false;
    try {
      syncSavedSavings({ savings: settings.initialSavings, monthlySaving: settings.monthlySaving, targetMonths: settings.targetMonths - Math.max(0, monthIndex(asOfMonth) - monthIndex(settings.startMonth)) });
      return persist(state.plans.map(item => item.id === plan.id ? settings : item), '기존 계획을 수정했습니다. 저축 기록을 유지하고 월 목표와 차트를 갱신했어요.');
    } catch { setNotice('구매 계획에 수치를 반영하지 못했습니다. 브라우저 저장 공간을 확인해 주세요.'); return false; }
  }
  function syncSavings(patch) {
    try { syncSavedSavings(patch); } catch { setNotice('구매 계획에 수치를 반영하지 못했습니다. 브라우저 저장 공간을 확인해 주세요.'); }
  }
  const rows = plan ? Array.from({ length: Math.min(summary.elapsed, 600) }, (_, index) => {
    const month = shiftMonth(asOfMonth, -index);
    const result = calculateSavingsProgress(plan, month);
    return { month, ...result };
  }) : [];
  return <div className="savings-page">
    <DreamCarPageHeader eyebrow="MY DREAM JOURNEY" title="계획을 넘어, 내 차에 가까이." description="매달의 작은 실행을 모아 드림카까지의 여정을 확인하세요." />
    <DreamCarTabs />
    {state.error && <p className="savings-error" role="alert">{state.error}</p>}
    <SavedPurchasePlanSection savedPlan={savedPlan} activePlan={plan} asOfDate={asOfDate} onStart={start} onUpdate={update} onSavingsChange={syncSavings} />
    {notice && <p className="savings-notice" role="status">{notice}</p>}
    {!plan ? <section className="savings-card savings-empty"><ChartNoAxesCombined size={theme.iconSize.lg} aria-hidden /><h2>저축의 첫 기록을 기다리고 있어요</h2><p>계획을 시작하고 매달 저축액을 기록해 보세요.<br />목표와 실제 누적액, 이번 달 부족액을 한눈에 확인할 수 있습니다.</p></section> : <>
      <section className="savings-plan-heading"><div><span className="savings-eyebrow">MY SAVINGS PLAN</span><h2>{plan.name}</h2><p>{plan.trim} · {plan.startDate || plan.startMonth} 시작 · 목표 {summary.targetMonth}</p></div><span className="savings-plan-badge"><Flag size={theme.iconSize.sm} aria-hidden />{summary.remaining === 0 ? '목표 달성' : (plan.startDate || `${plan.startMonth}-01`) > asOfDate ? '저축 시작 예정' : '차근차근 모으는 중'}</span></section>
      {summary.remaining === 0 && <section className="savings-achievement" role="status"><Trophy size={theme.iconSize.lg} aria-hidden /><div><h2>드림카 자금 준비 완료!</h2><p>목표 {formatMoney(plan.target)}을 달성했어요. 지금까지 {formatMoney(summary.total)}을 모았습니다.{summary.total > plan.target && ` 목표보다 ${formatMoney(summary.total - plan.target)} 더 모았어요.`}</p></div><strong>100% 달성</strong></section>}
      <div className="savings-metrics"><section className="savings-card"><Wallet size={theme.iconSize.md} aria-hidden /><span>지금까지 모은 자금</span><strong>{formatMoney(summary.total)}</strong><small>시작 자금 {formatMoney(plan.initialSavings)} 포함 · 기록 기준</small></section><section className="savings-card"><Target size={theme.iconSize.md} aria-hidden /><span>최종 목표까지</span><strong>{formatMoney(summary.remaining)}</strong><small>최종 목표 {formatMoney(plan.target)}</small></section><section className="savings-card"><CalendarDays size={theme.iconSize.md} aria-hidden /><span>이번 달 목표 대비</span><strong>{summary.monthlyGap === null ? '아직 미기록' : summary.monthlyGap < 0 ? `${formatMoney(-summary.monthlyGap)} 부족` : summary.monthlyGap > 0 ? `${formatMoney(summary.monthlyGap)} 초과` : '목표 달성'}</strong><small>{asOfMonth} 월말 목표 {formatMoney(summary.monthlyGoal)}</small></section></div>
      <div className="savings-main-grid"><div><section className="savings-card"><div className="savings-section-heading"><div><h2>자금이 쌓이는 여정</h2><p>계획한 속도와 실제 저축을 비교해 보세요.</p></div><span className="savings-chart-unit">월말 누적 기준</span></div><SavingsProgressChart key={plan.id} {...{ plan, asOfMonth }} /></section>
        <SavingsRecordHistory plan={plan} onEdit={setEditingId} onDelete={id => { try { const next = deleteSavingRecord(plan, id); const saved = persist(state.plans.map(item => item.id === plan.id ? next : item), '저축 기록을 삭제하고 월 합계와 차트를 갱신했습니다.'); if (saved && editingId === id) setEditingId(null); return saved; } catch (failure) { setNotice(failure.message); return false; } }} />
        <section className="savings-card savings-history"><div className="savings-section-heading"><h2>월별 실행 기록</h2><span className="savings-caption">최근 월부터 표시</span></div><div className="savings-table-scroll"><table><caption className="savings-sr-only">월별 목표 저축액과 실제 저축액, 누적액 비교</caption><thead><tr><th scope="col">월</th><th scope="col">목표 저축</th><th scope="col">실제 저축</th><th scope="col">목표 대비</th><th scope="col">기록 누적액</th><th scope="col">메모</th></tr></thead><tbody>{rows.map(row => <tr key={row.month}><th scope="row">{row.month}</th><td>{formatMoney(row.monthlyGoal)}</td><td>{row.currentEntry ? formatMoney(row.currentEntry.amount) : <span className="savings-unrecorded">미기록</span>}</td><td>{row.monthlyGap === null ? '미기록' : row.monthlyGap < 0 ? `${formatMoney(-row.monthlyGap)} 부족` : row.monthlyGap > 0 ? `${formatMoney(row.monthlyGap)} 초과` : '달성'}</td><td>{formatMoney(row.total)}</td><td>{row.currentEntry?.memo || '—'}</td></tr>)}</tbody></table></div></section></div>
        <aside className="savings-sidebar">{(plan.startDate || `${plan.startMonth}-01`) > asOfDate ? <section className="savings-card"><h2>저축 시작 예정</h2><p className="savings-caption">{plan.startDate || `${plan.startMonth}-01`}부터 저축 내역을 기록할 수 있어요.</p></section> : <DailySavingForm key={`${plan.id}-${editingRecord?.id || 'new'}`} {...{ plan, asOfDate }} record={editingRecord} onCancel={() => setEditingId(null)} onSave={next => { return persist(state.plans.map(item => item.id === plan.id ? next : item), '날짜별 저축 기록을 저장했습니다. 월 합계와 차트에 반영했어요.'); }} />}
          <RecurringSavingsSettings key={plan.id} plan={plan} asOfDate={asOfDate} onSave={(next, message) => persist(state.plans.map(item => item.id === plan.id ? next : item), message)} />
          <section className="savings-card savings-progress-card"><div className="savings-section-heading"><Flag size={theme.iconSize.md} aria-hidden /><h2>드림카까지의 거리</h2></div><strong>{summary.progress.toFixed(1)}<small>%</small></strong><progress value={summary.progress} max="100" aria-label="최종 목표 달성률" /><p>{summary.remaining === 0 ? '목표 자금을 모두 모았어요. 구매 조건과 실제 견적을 확인해 보세요.' : `최종 목표까지 ${formatMoney(summary.remaining)} 남았어요.`}</p><div className="savings-progress-pair"><span>현재 누적 목표</span><b>{formatMoney(summary.planned)}</b></div><div className="savings-progress-pair"><span>계획 대비 누적 차이</span><b>{summary.cumulativeGap < 0 ? `${formatMoney(-summary.cumulativeGap)} 부족` : `${formatMoney(summary.cumulativeGap)} 앞섬`}</b></div>{summary.missingMonths > 0 && <p className="savings-caption">미기록 {summary.missingMonths}개월이 있습니다. 해당 월을 기록하면 비교가 더 정확해져요.</p>}</section>

        </aside></div>
    </>}
  </div>;
}
