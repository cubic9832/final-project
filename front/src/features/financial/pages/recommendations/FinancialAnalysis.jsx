import { candidateMoney } from './candidatePresentation.js';
import './FinancialAnalysis.css';

export default function FinancialAnalysis({ totals, result, onShowRecommendations }) {
  const candidates = result.recommendations;
  const first = candidates[0];
  const financial = first?.decisionEvidence?.financial;
  const budget = result.budgetPolicy;
  const money = value => candidateMoney(value * 10000);
  const spending = [
    { label: '생활지출', value: totals.expenses - totals.loanPayment, tone: 'living' },
    { label: '기존 대출 상환', value: totals.loanPayment, tone: 'debt' },
    { label: '월 유지비 가용액', value: Math.max(0, totals.available), tone: 'available' },
  ];
  const total = spending.reduce((sum, item) => sum + Math.max(0, item.value), 0);
  const checks = [
    totals.available <= 0 ? '생활지출·상환을 제외하면 월 유지비에 쓸 여력이 없어요.' : null,
    !first ? '현재 구매 자금과 월 유지비 여력을 모두 충족하는 추천 차량이 없어요.' : null,
    financial && financial.cashAfterPurchase < financial.monthlyRunningCost * 3 ? '첫 번째 추천 차량을 구매하면 남는 예금이 예상 월 유지비 3개월분보다 적어요.' : null,
  ].filter(Boolean);
  const comparison = financial ? [
    { label: '구매·유지용 예금', before: financial.purchaseFunds, after: financial.cashAfterPurchase },
    { label: '월 여유금', before: financial.monthlyAvailable, after: financial.remainingMonthly },
  ] : [];
  const chartComparison = comparison.filter(item => item.before > 0 && item.after >= 0);
  return <section className="financial-analysis" aria-labelledby="financial-analysis-title">
    <div className="analysis-section-heading"><div><span>FINANCIAL OVERVIEW</span><h2 id="financial-analysis-title">내 차량 구매 여력</h2></div><button type="button" className="financial-recommendations-back" onClick={onShowRecommendations}>추천 차량 살펴보기</button></div>
    <div className="analysis-metrics">
      <article><h3>차량 구매 전 월 여유금</h3><strong>{money(totals.available)}</strong><p>부족한 유지비는 구매 후 예금으로 최소 12개월 충당 가능한지도 확인해요.</p></article>
      <article><h3>재무 조건 충족 후보</h3><strong>{result.eligibleCount ?? result.evaluationSummary?.financiallyEligibleConfigurations ?? 0}개 사양</strong><p>구매 후 예금으로 부족한 월 자금 12개월분을 충당할 수 있는 후보도 포함해요.</p></article>
      <article><h3>구매 가격 상한</h3><strong>{budget ? candidateMoney(budget.financialUpper) : '산정 정보 없음'}</strong><p>입력한 예금 기준의 상한이며, 높은 가격을 우대하지 않아요. 유지비 충당 조건은 별도로 확인해요.</p></article>
    </div>
    <div className="analysis-panels">
      <article className="analysis-panel"><h3>월소득 사용처</h3><p>월 실수령액 {money(totals.income)} 기준</p>
        <div className="analysis-stacked-bar" aria-hidden="true">{spending.map(item => <span key={item.tone} className={`analysis-tone-${item.tone}`} style={{ width: `${total ? Math.max(0, item.value) / total * 100 : 0}%` }} />)}</div>
        <dl className="analysis-legend">{spending.map(item => <div key={item.tone}><dt><i className={`analysis-tone-${item.tone}`} aria-hidden="true" />{item.label}</dt><dd>{money(item.value)}</dd></div>)}</dl>
        {totals.available < 0 && <p>매달 지출·상환 합계가 소득보다 {money(-totals.available)} 많아요.</p>}
      </article>
      <article className="analysis-panel"><h3>구매 전후 자금 비교</h3><p>{first ? `${first.vehicle.model} · ${first.vehicle.trim} 구매 기준` : '추천 가능한 차량이 생기면 구매 전후를 비교해 드려요.'}</p>
        {financial && <p>입력한 예금 {candidateMoney(financial.purchaseFunds)}에서 차량값 {candidateMoney(financial.purchaseCost)}을 지불하면 {candidateMoney(financial.cashAfterPurchase)}이 남아요. 부족한 월 자금은 이 잔액에서 사용합니다.</p>}
        {financial?.fundingSource === 'assets' && <p>예금 사용형: 월 {candidateMoney(financial.monthlyAssetDrawdown)} 소진 · 약 {financial.assetRunwayMonths}개월 유지 가능. 구매 후 예금으로 최소 {financial.requiredAssetCoverageMonths}개월분 충당 기준이며, 수입·지출·유지비가 일정하다고 가정해요.</p>}
        {financial && <><div className="analysis-chart-key"><span>구매 전</span><span>구매 후</span></div><div className="analysis-bars" aria-hidden="true">{chartComparison.map(item => <div key={item.label}><div className="analysis-bar-pair"><span style={{ height: '100%' }} /><span style={{ height: `${item.before > 0 ? Math.max(0, item.after) / item.before * 100 : 0}%` }} /></div><span>{item.label}</span></div>)}</div><p>각 항목의 구매 전 금액을 100%로 비교했어요. 정확한 금액은 아래 표에서 확인하세요.</p></>}
      </article>
    </div>
    <div className="analysis-panels">
      <article className="analysis-notice analysis-caution"><h3>확인하면 좋은 점</h3><ul>{(checks.length ? checks : ['입력한 조건에서 추가적인 자금 부족 신호는 확인되지 않았어요.']).map(text => <li key={text}>{text}</li>)}<li>차량 가격에 취득·등록비는 포함되지 않아 별도로 준비해야 해요.</li></ul></article>
      <article className="analysis-notice analysis-positive"><h3>현재 확보한 여력</h3><ul>{first && <li>추천 차량은 구매 가능 여부와 소득·예금을 통한 유지비 충당 가능 여부를 확인했어요.</li>}<li>미래 소득이나 추가 대출을 구매 자금에 더하지 않았어요.</li></ul></article>
    </div>
    {financial && <article className="analysis-panel analysis-purchase"><h3>첫 번째 추천 차량 구매 시</h3><p>{first.vehicle.model} 기준 · 다른 차량의 비용은 아래에서 비교할 수 있어요.</p><table><caption className="analysis-sr-only">첫 번째 추천 차량 구매 전후 자금</caption><thead><tr><th scope="col">항목</th><th scope="col">구매 전</th><th scope="col">구매 후</th></tr></thead><tbody>{comparison.map(item => <tr key={item.label}><th scope="row">{item.label}</th><td>{candidateMoney(item.before)}</td><td>{candidateMoney(item.after)}</td></tr>)}<tr><th scope="row">차량 월 유지비</th><td>미반영</td><td>{candidateMoney(financial.monthlyRunningCost)}</td></tr></tbody></table><p>일시불 구매 기준이며, 신용평가나 실제 보험·세금 견적은 아닙니다.</p></article>}
  </section>;
}
