import { calculateFinancialSummary } from '../calculateFinancialSummary.js';

const money = value => `${Number(value).toLocaleString('ko-KR', { maximumFractionDigits: 2 })}만 원`;

export default function FinancialBudgetSummary({ values = {}, assets, loans = [] }) {
  const totals = calculateFinancialSummary(values, loans);
  const hasIncome = values.income !== undefined && values.income !== '';
  const hasAssets = assets?.deposit !== undefined && assets.deposit !== '';
  const monthly = totals.available;
  return <aside className="financial-budget-summary" aria-labelledby="budget-summary-title">
    <span className="financial-eyebrow">MY BUDGET</span>
    <h2 id="budget-summary-title">내 차량 예산</h2>
    <p>입력한 금액이 바로 반영됩니다.</p>
    <dl aria-live="polite" aria-atomic="true">
      <div className="financial-budget-purchase"><dt>차량 구매 가능 자금</dt><dd>{hasAssets ? money(Math.max(0, Number(assets.deposit))) : '—'}</dd><small>{hasAssets ? '입력한 사용 가능 예금' : '예금을 입력하면 계산해 드려요'}</small></div>
      <div><dt>월 유지비에 쓸 수 있는 금액</dt><dd>{hasIncome ? money(monthly) : '—'}</dd><small>생활비·상환·저축 차감 후</small></div>
    </dl>
    {hasIncome && monthly <= 0 && <p className="financial-budget-warning">월 유지비 여력이 부족합니다. 지출과 저축 계획을 확인해 주세요.</p>}
    <p className="financial-budget-footnote">구매 자금과 월 유지비 여력을 각각 확인합니다. 대출·할부 금액은 더하지 않습니다.</p>
  </aside>;
}
