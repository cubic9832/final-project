import { Plus, Trash2 } from 'lucide-react';
import { calculateLoanPayment } from '../../calculateLoanPayment.js';
import { formatFinancialMoney } from '../../formatFinancialMoney.js';
import './LoanCalculator.css';

const loanTypes = ['신용대출', '주택담보대출', '전세자금대출', '학자금대출', '자동차대출', '카드론', '기타 대출'];
export default function LoanCalculator({ loans, onChange }) {
  function update(id, key, value) {
    onChange(loans.map(loan => {
      if (loan.id !== id) return loan;
      const next = { ...loan, [key]: value };
      if (['balance', 'rate', 'months'].includes(key)) {
        const payment = calculateLoanPayment(next.balance, next.rate, next.months);
        next.payment = payment === null ? '' : String(payment);
      }
      return next;
    }));
  }
  return <div className="loan-calculator">
    <div className="loan-calculator-heading"><div><h3>대출 상품별 계산</h3><p>기존 대출을 등록하면 월 상환액이 합산됩니다. 새 차량 구매 자금에 대출을 더하지 않습니다.</p></div><button type="button" className="financial-previous-button" onClick={() => onChange([...loans, { id: crypto.randomUUID(), type: '신용대출', balance: '', rate: '', months: '', payment: '' }])}><Plus size={16} aria-hidden="true" />대출 추가</button></div>
    {loans.map((loan, index) => <section className="loan-calculator-card" key={loan.id} aria-label={`${index + 1}번째 대출`}>
      <div className="loan-calculator-heading"><h4>대출 {index + 1}</h4><button type="button" className="financial-previous-button" aria-label={`${index + 1}번째 대출 삭제`} onClick={() => onChange(loans.filter(item => item.id !== loan.id))}><Trash2 size={16} aria-hidden="true" />삭제</button></div>
      <div className="financial-fields"><div className="financial-field"><label htmlFor={`loan-${loan.id}-type`}>대출 종류</label><select id={`loan-${loan.id}-type`} value={loan.type} onChange={event => update(loan.id, 'type', event.target.value)}>{loanTypes.map(type => <option key={type}>{type}</option>)}</select></div>
      {[['balance', '현재 대출 잔액', '백만 원', '9999999999.99'], ['rate', '연 금리', '%', '100'], ['months', '남은 기간', '개월', '1200'], ['payment', '월 상환액', '만 원', '9999999999.99']].map(([key, label, unit, max]) => <div className="financial-field" key={key}><label htmlFor={`loan-${loan.id}-${key}`}>{label}</label><div className="financial-input-wrap"><input id={`loan-${loan.id}-${key}`} type="number" min="0" max={max} step={key === 'months' ? '1' : key === 'payment' ? '0.0001' : '0.01'} inputMode={key === 'months' ? 'numeric' : 'decimal'} value={key === 'balance' && loan[key] !== '' ? Number(loan[key]) / 100 : loan[key]} onKeyDown={event => { if (['e', 'E', '+', '-'].includes(event.key)) event.preventDefault(); }} onChange={event => { const next = event.target.value; const pattern = key === 'months' ? /^\d{0,4}$/ : key === 'payment' ? /^\d{0,10}(\.\d{0,4})?$/ : /^\d{0,10}(\.\d{0,2})?$/; if (pattern.test(next)) update(loan.id, key, key === 'balance' && next !== '' ? String(Math.round(Number(next) * 10000) / 100) : next); else event.currentTarget.value = loan[key]; }} /><span aria-hidden="true">{key === 'balance' ? '백만원' : unit}</span></div>{['balance', 'payment'].includes(key) && loan[key] !== '' && <p className="financial-input-help">{formatFinancialMoney(Number(loan[key]) * 10000).replaceAll(' ', '')}</p>}</div>)}
      </div>
      <p>잔액·연 금리·남은 기간을 입력하면 월 상환액을 자동 계산합니다. 원리금균등·고정금리 가정이며 거치 기간·수수료는 제외해요. 실제 월 상환액을 직접 수정할 수 있으며, 대출 조건을 바꾸면 다시 계산됩니다.</p>
    </section>)}
    {!loans.length && <p>등록된 대출이 없습니다. 대출 추가를 눌러 입력해 주세요.</p>}
  </div>;
}
