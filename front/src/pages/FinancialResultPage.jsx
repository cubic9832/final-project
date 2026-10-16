import { useLocation, useNavigate } from 'react-router-dom';
import { calculateVehicleBudget } from '../features/financial/calculateVehicleBudget';
import './FinancialPage.css';
import './FinancialResultPage.css';

const amount = (value) => Number(value).toLocaleString('ko-KR', { maximumFractionDigits: 1 });
const money = (value) => `${amount(value)}만 원`;

export default function FinancialResultPage() {
  const { state } = useLocation();
  const navigate = useNavigate();
  const { values = {}, credit = {}, vehicle = {} } = state ?? {};
  const result = calculateVehicleBudget(state ?? {});
  const expenses = result.expenses - Number(values.loan || 0);
  const distribution = [
    { label: '생활·주거·고정지출', value: expenses, color: '#203960' },
    { label: '기존 대출 상환', value: Number(values.loan || 0), color: '#3f8ae2' },
    { label: '목표 저축', value: result.savings, color: '#e9b653' },
    { label: '월 가용자금', value: result.available, color: '#54b19d' },
  ];
  const higher = [];
  const lower = [];
  if (credit.overdue && credit.overdue !== '연체 없음') higher.push(credit.overdue === '잘 모르겠어요' ? '현재 연체 여부 확인이 필요합니다.' : `현재 ${credit.overdue} 연체가 있습니다.`);
  if (credit.overdue === '연체 없음') lower.push('현재 연체 중인 금액이 없습니다.');
  if (Number(credit.newLoans) > 0 || credit.newLoans === '5 이상') higher.push('최근 6개월 이내 신규 대출이 있습니다.');
  if (Number(credit.overdueCount) > 0 || credit.overdueCount === '5 이상') higher.push('최근 1년 이내 연체 이력이 있습니다.');
  if (credit.firstCredit) lower.push(`최초 신용거래 시점은 ${credit.firstCredit.replace('-', '년 ')}월입니다.`);
  if (result.available <= 0 && state?.values) higher.push('월 가용자금이 없어 지출·상환 계획 확인이 필요합니다.');
  const status = !state?.credit ? '입력 필요' : higher.length ? '확인 필요' : '특이사항 없음';
  const purchaseAvailable = result.available - result.monthlyPayment - result.operatingCost;
  const beforeAfter = [
    { label: '가용자금', before: result.available, after: purchaseAvailable },
    { label: '월 상환액', before: Number(values.loan || 0), after: Number(values.loan || 0) + result.monthlyPayment },
    { label: '목표 저축', before: result.savings, after: result.savings },
  ];
  const maxBar = Math.max(1, ...beforeAfter.flatMap((item) => [Math.abs(item.before), Math.abs(item.after)]));

  return <div className="financial-page result-page">
    <div className="financial-page-heading"><div><h1>종합 분석 결과</h1><p>입력한 재무정보와 차량 조건을 바탕으로 계산한 결과입니다.</p></div><span className="financial-stage-badge">참고 시뮬레이션 · {vehicle.purpose || '목적 미입력'}</span></div>
    {!result.valid && <p className="result-missing" role="status">예산 계산에 필요한 입력이 부족합니다. 조건 다시 입력하기에서 소득·자산·할부 기간을 확인해 주세요.</p>}
    <div className="result-metrics">
      <section className="result-card"><h2>월 가용자금</h2><strong>{state?.values ? money(result.available) : '—'}</strong><p>차량 비용 지출 전 기준</p></section>
      <section className="result-card"><h2>신용거래 확인</h2><strong className="result-caution">{status}</strong><p>입력 이력 기준 · 심사 등급 아님</p></section>
      <section className="result-card"><h2>예상 차량 예산</h2><strong className="result-budget">{result.valid ? `${amount(Math.floor(result.low))}~${amount(Math.floor(result.high))}만 원` : '—'}</strong><p>선수금 {money(result.downPayment)} · {vehicle.installment || '할부 기간 미입력'}</p></section>
    </div>
    <div className="result-chart-grid">
      <section className="result-card"><h2>월소득 사용처</h2><p>월 실수령액과 기타 소득 기준</p>
        <div className="result-stacked-bar" aria-hidden="true">{distribution.map((item) => <span key={item.label} style={{ flexGrow: Math.max(0, item.value), background: item.color }} />)}</div>
        <dl className="result-distribution">{distribution.map((item) => <div key={item.label}><dt><i style={{ background: item.color }} />{item.label}</dt><dd>{state?.values ? money(item.value) : '—'}</dd></div>)}</dl>
      </section>
      <section className="result-card"><h2>구매 전후 월 재무상태</h2><p>단위: 만 원 · 예산 상한 구매 가정</p><div className="result-chart-legend"><span>구매 전</span><span>구매 후</span></div>
        <div className="result-bars" aria-label="구매 전후 비교 그래프">{beforeAfter.map((item) => <div className="result-bar-group" key={item.label}><div className="result-bar-pair">
          <span title={`구매 전 ${money(item.before)}`} style={{ height: `${Math.max(2, Math.max(0, item.before) / maxBar * 100)}%` }} />
          <span title={result.valid ? `구매 후 ${money(item.after)}` : '입력 필요'} style={{ height: `${result.valid ? Math.max(2, Math.max(0, item.after) / maxBar * 100) : 2}%` }} />
        </div><span>{item.label}</span></div>)}</div>
      </section>
    </div>
    <div className="result-factor-grid">
      <section className="result-factors result-higher"><h2>확인이 필요한 요인</h2><ul>{(higher.length ? higher : [state?.credit ? '입력된 정보에서 추가 확인 요인이 없습니다.' : '신용정보 입력이 필요합니다.']).map((item) => <li key={item}>{item}</li>)}</ul></section>
      <section className="result-factors result-lower"><h2>긍정적인 참고 요인</h2><ul>{(lower.length ? lower : ['신용정보를 입력하면 참고 요인을 확인할 수 있습니다.']).map((item) => <li key={item}>{item}</li>)}</ul></section>
    </div>
    <section className="result-card result-estimate"><div className="result-estimate-heading"><div><h2>구매 가능 예상</h2><p>입력한 조건과 화면의 계산 가정 기준</p></div><strong>{result.valid ? `차량 예산 ${amount(Math.floor(result.low))}~${amount(Math.floor(result.high))}만 원` : '입력 필요'}</strong></div>
      <div className="result-table-wrap"><table><caption className="result-sr-only">구매 전후 월 재무 상태</caption><thead><tr><th scope="col">항목</th><th scope="col">구매 전</th><th scope="col">구매 후</th></tr></thead><tbody>{beforeAfter.map((item) => <tr key={item.label}><th scope="row">{item.label}</th><td>{state?.values ? money(item.before) : '—'}</td><td>{result.valid ? money(item.after) : '—'}</td></tr>)}</tbody></table></div>
      <p className="result-assumptions">계산 가정: 연 금리 6%, 월 유지비 20만 원, 가용자금의 25%를 여유자금으로 유지합니다. 선수금은 예금에서 비상자금을 제외한 범위로 제한합니다. 예산 하한은 할부 가능액의 80% 기준이며, 취득세·이전비는 포함하지 않습니다.</p>
    </section>
    <aside className="result-warning"><h2>결과·사용 전 확인</h2><p>위 예산은 화면용 추정치이며 실제 대출 가능액이나 금융기관 심사 결과가 아닙니다. 실제 금리와 보험료·유지비에 따라 달라집니다.</p></aside>
    <div className="financial-next-row result-navigation"><button type="button" className="result-previous" onClick={() => navigate('/financial', { state: { ...state, reviewReturn: false } })}>조건 다시 입력하기</button><button type="button" className="financial-next-button" onClick={() => navigate('/financial/recommendation-status', { state })}>추천 차량 확인하기</button></div>
  </div>;
}
