import { useState } from 'react';
import { Check, Plus } from 'lucide-react';
import { recordDailySaving } from '../../savingsProgress';
import theme from '../../../../styles/theme';
import SavingDatePicker from './SavingDatePicker';

export default function DailySavingForm({ plan, asOfDate, record, onSave, onCancel }) {
  const [date, setDate] = useState(record?.date || asOfDate);
  const [amount, setAmount] = useState(record?.amount?.toString() ?? '');
  const [memo, setMemo] = useState(record?.memo ?? '');
  const [error, setError] = useState('');
  function submit(event) {
    event.preventDefault();
    if (amount.trim() === '' || !/^\d+(\.\d{1,2})?$/.test(amount)) { setError('저축액을 소수점 둘째 자리까지 숫자로 입력해 주세요.'); return; }
    try {
      const next = recordDailySaving(plan, date, Number(amount), memo, asOfDate, crypto.randomUUID(), record?.id);
      if (onSave(next)) { setAmount(''); setMemo(''); setError(''); onCancel(); }
    } catch (failure) { setError(failure.message); }
  }
  return <section className="savings-card savings-entry"><div className="savings-section-heading"><div className="savings-icon"><Plus size={theme.iconSize.md} aria-hidden /></div><div><h2>{record ? '저축 기록 수정' : '나의 저축 기록'}</h2><p>매일 조금씩, 한 번에 모아도 괜찮아요.</p></div></div><form onSubmit={submit}>
    <SavingDatePicker value={date} min={plan.startDate || `${plan.startMonth}-01`} max={asOfDate} onChange={value => { setDate(value); setError(''); }} />
    {record?.legacyMonth && <p className="savings-caption">{record.legacyMonth}의 기존 월별 기록입니다. 실제 저축 날짜를 지정해 날짜별 기록으로 옮깁니다.</p>}
    <label>실제 저축한 금액<div className="savings-amount-input"><input type="text" inputMode="decimal" value={amount} placeholder="예: 5 또는 0.5" required aria-invalid={Boolean(error)} aria-describedby={error ? 'savings-entry-error' : undefined} onChange={event => { setAmount(event.target.value); setError(''); }} /><span>만 원</span></div></label>
    
    <label>한 줄 메모 <span className="savings-optional">선택</span><textarea value={memo} maxLength={200} placeholder="예: 오늘 커피값 아껴서 5천 원 저축" onChange={event => setMemo(event.target.value)} /></label>
    {error && <p id="savings-entry-error" className="savings-error" role="alert">{error}</p>}
    <button className="savings-button mint" type="submit"><Check size={theme.iconSize.sm} aria-hidden />{record ? '기록 수정 완료' : '저축 기록 추가'}</button>
    {record && <button className="savings-example-button" type="button" onClick={onCancel}>수정 취소</button>}
  </form></section>;
}
