import { useState } from 'react';
import SavingDatePicker from './SavingDatePicker';
import { monthIndex, updateProgressSettings } from '../../savingsProgress';

export default function SavingsStartSettings({ plan, asOfDate, onApply, buttonLabel, vehiclePreview, onDraftChange }) {
  const [date, setDate] = useState(plan.startDate || `${plan.startMonth}-01`);
  const [amount, setAmount] = useState(String(plan.initialSavings));
  const [remainingMonths, setRemainingMonths] = useState(String(Math.max(1, plan.targetMonths - Math.max(0, monthIndex(asOfDate.slice(0, 7)) - monthIndex(plan.startMonth)))));
  const [monthlySaving, setMonthlySaving] = useState(String(plan.monthlySaving));
  const [error, setError] = useState('');
  function changeValue(name, value) {
    const draft = { amount, remainingMonths, monthlySaving, [name]: value };
    if (name === 'amount') setAmount(value);
    if (name === 'remainingMonths') setRemainingMonths(value);
    if (name === 'monthlySaving') setMonthlySaving(value);
    setError('');
    if (/^\d+(\.\d{1,2})?$/.test(draft.amount) && /^\d+$/.test(draft.remainingMonths) && Number(draft.remainingMonths) >= 1 && Number(draft.remainingMonths) <= 1200 && /^\d+(\.\d{1,2})?$/.test(draft.monthlySaving)) {
      onDraftChange?.({ savings: Number(draft.amount), monthlySaving: Number(draft.monthlySaving), targetMonths: Number(draft.remainingMonths) });
    }
  }
  function submit(event) {
    event.preventDefault();
    if (amount.trim() === '' || !/^\d+(\.\d{1,2})?$/.test(amount)) { setError('시작 자금을 소수점 둘째 자리까지 숫자로 입력해 주세요.'); return; }
    if (!/^\d+$/.test(remainingMonths)) { setError('목표까지 남은 기간을 개월 단위의 정수로 입력해 주세요.'); return; }
    if (!/^\d+(\.\d{1,2})?$/.test(monthlySaving)) { setError('매월 저축할 금액을 소수점 둘째 자리까지 숫자로 입력해 주세요.'); return; }
    try { if (onApply(updateProgressSettings(plan, date, Number(amount), Number(remainingMonths), Number(monthlySaving), asOfDate))) setError(''); } catch (failure) { setError(failure.message); }
  }
  return <form className="savings-start-settings" onSubmit={submit}>
    <div className="savings-settings-columns"><div className="savings-settings-column"><SavingDatePicker label="저축 시작 날짜" value={date} min="2000-01-01" max="2100-12-31" today={asOfDate} onChange={value => { setDate(value); setError(''); }} />
    <label>시작 시점에 모아둔 돈<div className="savings-amount-input"><input type="text" inputMode="decimal" value={amount} required onChange={event => { changeValue('amount', event.target.value); }} /><span>만 원</span></div></label>
    </div><div className="savings-settings-column"><label>목표까지 남은 기간<div className="savings-amount-input"><input type="text" inputMode="numeric" value={remainingMonths} required onChange={event => { changeValue('remainingMonths', event.target.value); }} /><span>개월</span></div></label><label>매월 저축할 금액<div className="savings-amount-input"><input type="text" inputMode="decimal" value={monthlySaving} required onChange={event => { changeValue('monthlySaving', event.target.value); }} /><span>만 원</span></div></label></div></div>
    {vehiclePreview}
    {error && <p className="savings-error" role="alert">{error}</p>}<button type="submit" className="savings-button navy">{buttonLabel}</button>
  </form>;
}
