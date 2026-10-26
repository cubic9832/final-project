import { calculateFinancialSummary } from '../calculateFinancialSummary.js';
import { formatFinancialMoney } from '../formatFinancialMoney.js';

const money = value => formatFinancialMoney(Number(value) * 10000);

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
      <div className="financial-budget-purchase"><dt>차량 구매·유지에 사용할 예금</dt><dd>{hasAssets ? money(Math.max(0, Number(assets.deposit))) : '—'}</dd><small>{hasAssets ? '차량값과 구매 후 부족한 월 자금에 함께 사용할 총액' : '예금을 입력하면 계산해 드려요'}</small></div>
      <div><dt>월 유지비에 쓸 수 있는 금액</dt><dd>{hasIncome ? money(monthly) : '—'}</dd><small>생활비·상환 차감 후</small></div>
    </dl>
    {hasIncome && monthly <= 0 && <p className="financial-budget-warning">월 유지비 여력이 부족합니다. 지출과 구매 후 남는 예금을 확인해 주세요.</p>}
    <p className="financial-budget-footnote">이 예금에서 차량값을 먼저 지불합니다. 월소득으로 부족한 생활비·유지비는 남은 예금으로 충당하며, 같은 돈을 두 번 계산하지 않습니다.</p>
  </aside>;
}
