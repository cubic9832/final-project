import { useEffect, useId, useRef, useState } from 'react';
import { CalendarDays, ChevronLeft, ChevronRight } from 'lucide-react';
import { shiftMonth } from '../../savingsProgress';
import theme from '../../../../styles/theme';

export default function SavingDatePicker({ value, min, max, onChange, label = '기록 날짜', today = max }) {
  const [open, setOpen] = useState(false);
  const [month, setMonth] = useState(value.slice(0, 7));
  const [view, setView] = useState('days');
  const [yearPage, setYearPage] = useState(2000);
  const wrapper = useRef(null);
  const trigger = useRef(null);
  const calendarId = useId();
  useEffect(() => {
    if (!open) return;
    function closeOutside(event) { if (!wrapper.current?.contains(event.target)) setOpen(false); }
    function closeOnEscape(event) { if (event.key === 'Escape') { setOpen(false); trigger.current?.focus(); } }
    document.addEventListener('pointerdown', closeOutside);
    document.addEventListener('keydown', closeOnEscape);
    return () => { document.removeEventListener('pointerdown', closeOutside); document.removeEventListener('keydown', closeOnEscape); };
  }, [open]);
  const [year, monthNumber] = month.split('-').map(Number);
  const firstDay = new Date(Date.UTC(year, monthNumber - 1, 1)).getUTCDay();
  const days = new Date(Date.UTC(year, monthNumber, 0)).getUTCDate();
  const cells = Array.from({ length: Math.ceil((firstDay + days) / 7) * 7 }, (_, index) => {
    const day = index - firstDay + 1;
    return day > 0 && day <= days ? `${month}-${String(day).padStart(2, '0')}` : null;
  });
  function choose(date) { onChange(date); setOpen(false); setView('days'); trigger.current?.focus(); }
  const maxYear = Number(max.slice(0, 4));
  function chooseYear(selectedYear) {
    const selectedMonth = Math.min(monthNumber, selectedYear === maxYear ? Number(max.slice(5, 7)) : 12);
    setMonth(`${selectedYear}-${String(selectedMonth).padStart(2, '0')}`);
    setView('days');
  }
  const selectedLabel = `${Number(value.slice(0, 4))}년 ${Number(value.slice(5, 7))}월 ${Number(value.slice(8, 10))}일`;
  return <div className="saving-date-picker" ref={wrapper}>
    <span className="saving-date-label" id={`${calendarId}-label`}>{label}</span>
    <button ref={trigger} className="saving-date-trigger" type="button" aria-labelledby={`${calendarId}-label ${calendarId}-value`} aria-expanded={open} aria-controls={calendarId} onClick={() => { if (!open) { setMonth(value.slice(0, 7)); setView('days'); } setOpen(current => !current); }}><span id={`${calendarId}-value`}>{value === today ? `오늘 · ${selectedLabel}` : selectedLabel}</span><CalendarDays size={theme.iconSize.md} aria-hidden /></button>
    {open && <div className="saving-calendar" id={calendarId} role="region" aria-label="저축 기록 날짜 선택">
      <div className="saving-calendar-heading">
        <button type="button" aria-label={view === 'years' ? '이전 연도 묶음' : '이전 달'} disabled={view === 'years' ? yearPage <= 2000 : year <= 2000 && monthNumber === 1} onClick={() => view === 'years' ? setYearPage(yearPage - 12) : setMonth(shiftMonth(month, -1))}><ChevronLeft size={theme.iconSize.md} aria-hidden /></button>
        <div className="saving-calendar-month-select"><button type="button" className="saving-calendar-period" aria-label="연도 선택" aria-expanded={view === 'years'} onClick={() => { setYearPage(2000 + Math.floor((year - 2000) / 12) * 12); setView(view === 'years' ? 'days' : 'years'); }}>{view === 'years' ? `${yearPage}–${Math.min(yearPage + 11, maxYear)}년` : `${year}년`}</button><button type="button" className="saving-calendar-period" aria-label="월 선택" aria-expanded={view === 'months'} onClick={() => setView(view === 'months' ? 'days' : 'months')}>{monthNumber}월</button></div>
        <button type="button" aria-label={view === 'years' ? '다음 연도 묶음' : '다음 달'} disabled={view === 'years' ? yearPage + 12 > maxYear : month >= max.slice(0, 7)} onClick={() => view === 'years' ? setYearPage(yearPage + 12) : setMonth(shiftMonth(month, 1))}><ChevronRight size={theme.iconSize.md} aria-hidden /></button>
      </div>
      {view === 'years' && <div className="saving-calendar-period-grid" aria-label="연도 목록">{Array.from({ length: Math.max(0, Math.min(12, maxYear - yearPage + 1)) }, (_, index) => yearPage + index).map(option => <button type="button" key={option} aria-pressed={option === year} onClick={() => chooseYear(option)}>{option}년</button>)}</div>}
      {view === 'months' && <div className="saving-calendar-period-grid" aria-label="월 목록">{Array.from({ length: 12 }, (_, index) => index + 1).map(option => <button type="button" key={option} disabled={year === maxYear && option > Number(max.slice(5, 7))} aria-pressed={option === monthNumber} onClick={() => { setMonth(`${year}-${String(option).padStart(2, '0')}`); setView('days'); }}>{option}월</button>)}</div>}
      <div className="saving-calendar-grid" hidden={view !== 'days'}>{['일', '월', '화', '수', '목', '금', '토'].map(day => <span className="saving-calendar-weekday" key={day}>{day}</span>)}{cells.map((date, index) => date ? <button type="button" key={date} aria-label={`${date} 선택`} aria-pressed={date === value} aria-current={date === today ? 'date' : undefined} disabled={date < min || date > max} onClick={() => choose(date)}>{Number(date.slice(8))}</button> : <span key={`blank-${index}`} />)}</div>
      <button type="button" className="saving-calendar-today" disabled={today < min || today > max} onClick={() => choose(today)}>오늘 선택</button>
      {month <= min.slice(0, 7) && <p className="savings-caption">{min} 이후 날짜를 선택할 수 있습니다. 계획의 시작일은 ‘저축 시작 날짜·시작 자금 변경’에서 수정할 수 있습니다.</p>}
    </div>}
  </div>;
}
