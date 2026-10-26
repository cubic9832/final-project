import { useEffect, useRef, useState } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import FinancialBudgetSummary from '../../components/FinancialBudgetSummary.jsx';
import FinancialFlowHeader from '../../components/FinancialFlowHeader.jsx';
import LoanCalculator from './LoanCalculator.jsx';
import { formatFinancialMoney } from '../../formatFinancialMoney.js';
import '../../styles/FinancialPages.css';

const expenseFields = [
  ['housing', '주거비'], ['fixed', '기타 고정 지출'], ['living', '생활비'],
  ['transport', '교통비'], ['phone', '통신비'],
];
const totalExpenses = values => expenseFields.reduce((sum, [key]) => sum + Number(values[key] || 0), 0);

<<<<<<< HEAD
const extraFields = [
  { name: 'extraIncome', label: '기타 정기 소득', required: false },
  { name: 'transport', label: '교통비', required: false },
  { name: 'phone', label: '통신비', required: false },
];

const steps = ['소득·지출', '자산·부채', '신용정보', '차량 조건', '확인'];

// 화면 이동 확인용 초기값. 이전 단계에서 전달한 사용자 입력이 있으면 그 값을 우선한다.
const initialState = {
  values: { income: 500, housing: 50, fixed: 30, living: 70, loan: 0, savings: 50 },
  assets: { deposit: 1500, downPayment: 500, emergency: 500 },
  loans: [],
  credit: { overdue: '연체 없음', overdueCount: '0', newLoans: '0', cards: '2', firstCredit: '2021-03' },
  vehicle: { purchase: '신차만', body: '경차 · 소형 · 준중형', fuel: '가솔린 · 하이브리드', installment: '48개월', purpose: '출퇴근' },
};

export function FinancialProgress({ current = 1 }) {
  return (
    <div className="financial-progress">
      <ol aria-label="재무 진단 진행 단계">
        {steps.map((step, index) => (
          <li key={step} className={current === index + 1 ? 'current' : ''} aria-current={current === index + 1 ? 'step' : undefined}>
            {index + 1} {step}
          </li>
        ))}
      </ol>
      <div className="financial-progress-track" aria-hidden="true">
        <span style={{ width: `${current * 20}%` }} />
      </div>
    </div>
  );
}
=======
>>>>>>> ml/test

export default function FinancialPage() {
  const { state } = useLocation();
  const navigate = useNavigate();
<<<<<<< HEAD
  const location = useLocation();
  const formState = location.state ?? initialState;
  const [values, setValues] = useState(formState.values ?? initialState.values);
  const [expanded, setExpanded] = useState(
    extraFields.some(({ name }) => location.state?.values?.[name] !== undefined)
  );
=======
  const formRef = useRef(null);
  useEffect(() => {
    const form = formRef.current;
    const preventWheelChange = event => {
      if (event.target instanceof HTMLInputElement && event.target.type === 'number') event.preventDefault();
    };
    form.addEventListener('wheel', preventWheelChange, { passive: false });
    return () => form.removeEventListener('wheel', preventWheelChange);
  }, []);
  const [values, setValues] = useState(() => ({
    income: state?.values?.income === undefined ? '' : String(Number(state.values.income || 0) + Number(state.values.extraIncome || 0)),
    monthlyExpenses: state?.values?.monthlyExpenses ?? (state?.values ? String(totalExpenses(state.values)) : ''),
  }));
  const [deposit, setDeposit] = useState(state?.assets?.deposit ?? '');
  const [loanPayment, setLoanPayment] = useState(() => String((state?.loans ?? []).reduce((sum, loan) => sum + Number(loan.payment || 0), 0)));
  const [loanDetails, setLoanDetails] = useState(() => (state?.loans ?? []).filter(loan => loan.id).map(loan => ({ ...loan })));
  const [detailedLoans, setDetailedLoans] = useState(state?.detailedLoans ?? false);
  const [breakdown, setBreakdown] = useState(state?.expenseBreakdown ?? state?.values ?? {});
  const [detailed, setDetailed] = useState(false);
  const [errors, setErrors] = useState({});
  const loans = detailedLoans ? loanDetails : [{ payment: loanPayment || '0' }];
  const totalLoanPayment = loans.reduce((sum, loan) => sum + Number(loan.payment || 0), 0);
>>>>>>> ml/test

  function input(name, label, value, onChange, { required = false, help, readOnly = false } = {}) {
    return <div className="financial-field" key={name}>
      <label htmlFor={`financial-${name}`}>{label}{required ? <span className="financial-required"> *</span> : ' (선택)'}</label>
      <div className="financial-input-wrap"><input id={`financial-${name}`} type="number" min="0" max="9999999999.99" step="0.01" inputMode="decimal" placeholder="0" required={required} readOnly={readOnly} value={value} onKeyDown={event => { if (['e', 'E', '+', '-'].includes(event.key)) event.preventDefault(); }} onChange={event => { const next = event.target.value; if (!/^\d{0,10}(\.\d{0,2})?$/.test(next)) { event.currentTarget.value = String(value ?? ''); return; } onChange(next); setErrors(previous => ({ ...previous, [name]: '' })); }} aria-invalid={Boolean(errors[name])} aria-describedby={errors[name] ? `${name}-error` : help ? `${name}-help` : undefined} onInvalid={event => { event.preventDefault(); const message = event.currentTarget.validationMessage; setErrors(previous => ({ ...previous, [name]: message })); }} /><span aria-hidden="true">만 원</span></div>
      {help && <p className="financial-input-help" id={`${name}-help`}>{help}</p>}
      {Number(value) >= 10000 && <p className="financial-input-help">{formatFinancialMoney(Number(value) * 10000)}</p>}
      {errors[name] && <p className="financial-field-error" id={`${name}-error`} role="alert">{errors[name]}</p>}
    </div>;
  }

  function changeMode(next) {
    if (next && totalExpenses(breakdown) !== Number(values.monthlyExpenses || 0)) setBreakdown({ living: values.monthlyExpenses || '0' });
    if (next && values.monthlyExpenses === '') setValues(previous => ({ ...previous, monthlyExpenses: '0' }));
    setDetailed(next);
  }

  function submit(event) {
    event.preventDefault();
<<<<<<< HEAD
    if (!event.currentTarget.reportValidity()) return;
    navigate(location.state?.reviewReturn ? '/financial/review' : '/financial/assets', { state: { ...formState, values, reviewReturn: false } });
=======
    if (detailedLoans && loanDetails.some(loan => loan.payment === '')) { setErrors(previous => ({ ...previous, loanPayment: '등록한 대출의 월 상환액을 계산하거나 직접 입력해 주세요.' })); return; }
    navigate('/financial/vehicle', { state: { values, assets: { deposit }, loans, detailedLoans, vehicle: state?.vehicle, expenseBreakdown: breakdown } });
>>>>>>> ml/test
  }

  return <div className="financial-page">
    <FinancialFlowHeader current={1} title="내 차량 예산부터 알아볼까요?" description="매달 들어오고 나가는 돈과 차량 구매·유지에 사용할 예금을 알려주세요." />
    <form ref={formRef} onSubmit={submit}><div className="financial-entry-grid">
      <section className="financial-entry-card" aria-labelledby="income-title"><h2 id="income-title">소득과 지출</h2><p>모든 금액은 만 원 단위입니다. 지출이 없으면 0을 입력해 주세요.</p>
        <div className="financial-fields">
          {input('income', '월 총수령액', values.income, value => setValues(previous => ({ ...previous, income: value })), { required: true, help: '실수령 월급과 정기적으로 받는 기타 소득을 합쳐 주세요.' })}
          {input('monthlyExpenses', '월 생활지출 합계', values.monthlyExpenses, value => setValues(previous => ({ ...previous, monthlyExpenses: value })), { required: true, readOnly: detailed, help: '주거비·생활비·통신비 등을 포함해 주세요. 대출 상환은 아래에 따로 입력합니다.' })}
        </div>
        <fieldset className="financial-expense-mode"><legend>생활지출 입력 방식</legend><label><input type="radio" name="expenseMode" checked={!detailed} onChange={() => changeMode(false)} /> 합계 직접 입력</label><label><input type="radio" name="expenseMode" checked={detailed} onChange={() => changeMode(true)} /> 항목별로 계산</label></fieldset>
        {detailed && <div className="financial-expense-breakdown"><p className="financial-input-help">항목별 합계가 위 생활지출에 적용됩니다. 생활비에 포함된 금액을 다른 항목에 나눌 때는 그만큼 생활비에서 빼 주세요.</p><div className="financial-fields">{expenseFields.map(([key, label]) => input(key, label, breakdown[key] ?? '', value => { const next = { ...breakdown, [key]: value }; setBreakdown(next); setValues(previous => ({ ...previous, monthlyExpenses: String(totalExpenses(next)) })); }))}</div></div>}
        <h2 className="financial-subsection-heading">구매 자금과 대출 상환</h2>
        <div className="financial-fields">
          {input('deposit', '차량 구매·유지에 사용할 예금', deposit, setDeposit, { required: true, help: '차량값과 구매 후 부족한 생활비·유지비에 사용할 수 있는 총예금입니다. 다른 용도로 남겨 둘 돈은 제외해 주세요. 월소득이 부족하면 차량값을 뺀 예금으로 부족액을 최소 12개월 충당할 수 있는지 확인합니다.' })}
          {input('loanPayment', '기존 대출 월 상환액 합계', detailedLoans ? String(totalLoanPayment) : loanPayment, setLoanPayment, { readOnly: detailedLoans, help: '대출이 없다면 0으로 두세요. 생활지출에는 이 금액을 다시 포함하지 않습니다.' })}
        </div>
        <fieldset className="financial-expense-mode"><legend>대출 상환액 입력 방식</legend><label><input type="radio" name="loanMode" checked={!detailedLoans} onChange={() => { setLoanPayment(String(totalLoanPayment)); setDetailedLoans(false); }} />합계 직접 입력</label><label><input type="radio" name="loanMode" checked={detailedLoans} onChange={() => { if (!loanDetails.length && Number(loanPayment) > 0) setLoanDetails([{ id: crypto.randomUUID(), type: '기타 대출', balance: '', rate: '', months: '', payment: loanPayment }]); setDetailedLoans(true); }} />상품별 계산</label></fieldset>
        {detailedLoans && <LoanCalculator loans={loanDetails} onChange={next => { setLoanDetails(next); setErrors(previous => ({ ...previous, loanPayment: '' })); }} />}
      </section>
      <FinancialBudgetSummary values={values} assets={{ deposit }} loans={loans} />
    </div><div className="financial-next-row"><button type="submit" className="financial-next-button">차량 취향 선택하기</button></div></form>
  </div>;
}
