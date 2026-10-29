import { Link } from 'react-router-dom';
import { Car } from 'lucide-react';
import DreamCarPreview from '../../components/DreamCarPreview';
import PurchaseFundingSummary from '../../components/PurchaseFundingSummary';
import PurchasePlanInsight from '../../components/PurchasePlanInsight';
import { calculatePurchasePlan, defaultPlan } from '../../purchasePlan';
import { calculateSavingsProgress, monthIndex } from '../../savingsProgress';
import { getVehicleCostDefaults } from '../../vehicleCostDefaults';
import catalog from '../../../vehicle/planningVehicleCatalog.json';
import SavingsStartSettings from './SavingsStartSettings';
import theme from '../../../../styles/theme';

export default function SavedPurchasePlanSection({ savedPlan, activePlan, asOfDate, onStart, onUpdate, onSavingsChange }) {
  const vehicle = activePlan ? catalog.find(car => car.id === activePlan.vehicleId) : savedPlan?.vehicle;
  if (!vehicle) return <section className="savings-card"><h2>차량 구매 계획</h2><p className="savings-caption">계산기에서 구매 계획을 저장하면 실제 저축 기록을 시작할 수 있어요.</p><Link className="savings-button navy" to="/dream-car">구매 계획 만들기</Link></section>;
  const baseline = activePlan?.purchaseInputs || (savedPlan?.vehicle.id === vehicle.id ? savedPlan.saved.inputs : { ...defaultPlan, ...getVehicleCostDefaults(vehicle).inputs });
  const inputs = activePlan ? { ...baseline, savings: calculateSavingsProgress(activePlan, asOfDate.slice(0, 7)).total, monthlySaving: activePlan.monthlySaving, targetMonths: Math.max(1, activePlan.targetMonths - Math.max(0, monthIndex(asOfDate.slice(0, 7)) - monthIndex(activePlan.startMonth))) } : baseline;
  const result = calculatePurchasePlan(vehicle.price / 10000, inputs);
  if (activePlan) {
    result.target = activePlan.target;
    result.remaining = Math.max(0, result.target - inputs.savings);
    result.progress = Math.min(100, inputs.savings / result.target * 100);
    result.months = result.remaining === 0 ? 0 : inputs.monthlySaving > 0 ? Math.ceil(result.remaining / inputs.monthlySaving) : null;
    result.fasterMonths = Math.ceil(result.remaining / (inputs.monthlySaving + 30));
    result.requiredMonthly = result.remaining / inputs.targetMonths;
  }
  const settingsPlan = activePlan || { startMonth: asOfDate.slice(0, 7), startDate: asOfDate, initialSavings: inputs.savings, monthlySaving: inputs.monthlySaving, targetMonths: inputs.targetMonths, entries: {} };
  const vehiclePreview = <><DreamCarPreview vehicle={vehicle} /><p className="savings-caption">등록 카탈로그 기준 · {vehicle.checked_on || '확인일 미등록'}{vehicle.source_url && <> · <a href={vehicle.source_url} target="_blank" rel="noreferrer">차량 정보 출처</a></>}</p></>;
  return <div className="savings-purchase-layout"><section className="savings-card"><div className="savings-purchase-heading"><span>01</span><h2>차량 구매 계획</h2><Car size={theme.iconSize.lg} aria-hidden /></div><div className="savings-purchase-settings"><SavingsStartSettings key={JSON.stringify([activePlan?.id, activePlan?.startDate, activePlan?.initialSavings, activePlan?.monthlySaving, activePlan?.targetMonths])} asOfDate={asOfDate} plan={settingsPlan} onApply={activePlan ? onUpdate : onStart} onDraftChange={onSavingsChange} buttonLabel={activePlan ? '계획 변경 저장' : '새 실행 계획 시작'} vehiclePreview={vehiclePreview} /></div></section><div className="savings-purchase-results"><PurchaseFundingSummary result={result} inputs={inputs} baseDate={activePlan?.startDate > asOfDate ? activePlan.startDate : asOfDate} /><PurchasePlanInsight result={result} inputs={inputs} /></div></div>;
}
