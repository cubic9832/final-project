import { TrendingUp } from 'lucide-react';
import theme from '../../../styles/theme';
import './PurchasePlanInsight.css';

const money = value => `${Math.round(value).toLocaleString('ko-KR')}만 원`;
export default function PurchasePlanInsight({ result, inputs }) {
  return <section className="purchase-plan-insight"><TrendingUp size={theme.iconSize.lg} aria-hidden /><h2>꿈에 조금 더 가까이</h2><p>{inputs.targetMonths}개월 안에 구매하려면 월 <strong>{money(result.requiredMonthly)}</strong>을 모으면 돼요.</p><p>매월 30만 원 더 저축하면 <strong>{result.months === null ? `${result.fasterMonths}개월 후 도달` : `${Math.max(0, result.months - result.fasterMonths)}개월 단축`}</strong>할 수 있어요.</p><p>구매 후에도 월 <strong>{money(result.monthlyTotal)}</strong>의 여유자금이 있는지 확인하세요.</p></section>;
}
