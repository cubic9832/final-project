// 생년월일 입력 (회원가입 · 구글 추가 정보 공용)
// 숫자로 직접 입력(하이픈 자동)하거나, 아래 년 · 월 · 일 목록에서 골라도 된다.
// 부모에게는 다른 입력칸과 같은 모양의 onChange({ target: { name, value } }) 로 'YYYY-MM-DD' 를 넘긴다.
import { useState } from 'react';
import { MIN_SIGNUP_AGE } from './profileRules';

const EMPTY = { year: '', month: '', day: '' };
const pad = (number) => String(number).padStart(2, '0');

// 숫자만 남겨 1998-05-14 모양으로 하이픈을 넣는다 (전화번호 formatPhone 과 같은 방식)
function formatBirth(value) {
  const digits = value.replace(/\D/g, '').slice(0, 8);
  if (digits.length <= 4) return digits;
  if (digits.length <= 6) return `${digits.slice(0, 4)}-${digits.slice(4)}`;
  return `${digits.slice(0, 4)}-${digits.slice(4, 6)}-${digits.slice(6)}`;
}

// 'YYYY-MM-DD' 를 끝까지 입력했을 때만 년 · 월 · 일로 나눈다
function splitBirth(value) {
  const match = /^(\d{4})-(\d{2})-(\d{2})$/.exec(value ?? '');
  return match ? { year: match[1], month: match[2], day: match[3] } : null;
}

const daysInMonth = (year, month) => new Date(Number(year || 2000), Number(month), 0).getDate();

export default function BirthDateInput({ id, name, value, onChange, className, ...ariaProps }) {
  // 목록에서 년 · 월만 고르고 일은 아직 안 고른 상태처럼, 날짜가 다 정해지기 전 선택값
  const [draft, setDraft] = useState(EMPTY);
  const selected = splitBirth(value) ?? draft;

  // 목록 맨 위는 가입할 수 있는 가장 늦은 해(올해 - 18), 아래로 1900년까지
  const latestYear = new Date().getFullYear() - MIN_SIGNUP_AGE;
  const years = Array.from({ length: latestYear - 1899 }, (_, index) => String(latestYear - index));
  if (selected.year && !years.includes(selected.year)) years.unshift(selected.year); // 직접 입력한 해가 범위 밖이어도 보이게
  const days = Array.from({ length: daysInMonth(selected.year, selected.month || 1) }, (_, index) => pad(index + 1));

  const emit = (next) => onChange({ target: { name, value: next } });

  function handleType(event) {
    setDraft(EMPTY); // 직접 입력하면 목록 선택 중이던 값은 버린다
    emit(formatBirth(event.target.value));
  }

  function handlePick(key, picked) {
    const next = { ...selected, [key]: picked };
    // 2월 30일처럼 그 달에 없는 날이 되면 일을 비운다
    if (next.day && next.month && Number(next.day) > daysInMonth(next.year, next.month)) next.day = '';
    setDraft(next);
    // 셋 다 골라야 날짜가 된다. 아직이면 입력칸은 비워 둔다
    emit(next.year && next.month && next.day ? `${next.year}-${next.month}-${next.day}` : '');
  }

  return (
    <div className="signup-birth">
      <input
        id={id}
        name={name}
        type="text"
        inputMode="numeric"
        placeholder="예: 1998-05-14 (숫자만 입력)"
        autoComplete="bday"
        maxLength={10}
        value={value}
        onChange={handleType}
        className={className}
        {...ariaProps}
      />
      <div className="signup-birth-selects" aria-label="생년월일 목록에서 고르기">
        <select aria-label="태어난 해" value={selected.year} onChange={(event) => handlePick('year', event.target.value)} className={className}>
          <option value="">년</option>
          {years.map((year) => <option key={year} value={year}>{year}년</option>)}
        </select>
        <select aria-label="태어난 달" value={selected.month} onChange={(event) => handlePick('month', event.target.value)} className={className}>
          <option value="">월</option>
          {Array.from({ length: 12 }, (_, index) => pad(index + 1)).map((month) => <option key={month} value={month}>{Number(month)}월</option>)}
        </select>
        <select aria-label="태어난 날" value={selected.day} onChange={(event) => handlePick('day', event.target.value)} className={className}>
          <option value="">일</option>
          {days.map((day) => <option key={day} value={day}>{Number(day)}일</option>)}
        </select>
      </div>
    </div>
  );
}
