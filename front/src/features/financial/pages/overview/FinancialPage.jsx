import { useState } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { calculateFinancialSummary } from '../../calculateFinancialSummary';
import FinancialProfileFields from './FinancialProfileFields';
import '../../styles/FinancialPages.css';

const fields = [
  { name: 'income', label: '월 실수령액', required: true },
  { name: 'housing', label: '월 주거비', required: true },
  { name: 'fixed', label: '월 고정 지출', required: true },
  { name: 'living', label: '월 생활비', required: true },
  { name: 'loan', label: '현재 대출 월 상환액', required: false },
  { name: 'savings', label: '월 목표 저축액', required: false },
];

const extraFields = [
  { name: 'extraIncome', label: '기타 정기 소득', required: false },
  { name: 'transport', label: '교통비', required: false },
  { name: 'phone', label: '통신비', required: false },
];

const steps = ['소득·지출', '자산·부채', '신용정보', '차량 조건', '확인'];

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

export default function FinancialPage() {
  const navigate = useNavigate();
  const location = useLocation();
  const [values, setValues] = useState(location.state?.values ?? {});
  const [expanded, setExpanded] = useState(
    extraFields.some(({ name }) => location.state?.values?.[name] !== undefined)
  );

  const { income, expenses, savings, available } = calculateFinancialSummary(values);
  const format = (value) => value.toLocaleString('ko-KR', { maximumFractionDigits: 2 });
  const started = Object.values(values).some((value) => value !== '');

  function handleSubmit(event) {
    event.preventDefault();
    if (!event.currentTarget.reportValidity()) return;
    navigate(location.state?.reviewReturn ? '/financial/review' : '/financial/assets', { state: { ...location.state, values, reviewReturn: false } });
  }

  function renderField({ name, label, required }) {
    return (
      <div className="financial-field" key={name}>
        <label htmlFor={`financial-${name}`}>
          {label}{!required && ' (선택)'}
          {required && <span className="financial-required" aria-hidden="true"> *</span>}
        </label>
        <div className="financial-input-wrap">
          <input
            id={`financial-${name}`}
            name={name}
            type="number"
            min="0"
            step="0.01"
            inputMode="decimal"
            placeholder="0"
            required={required}
            value={values[name] ?? ''}
            onChange={(event) => setValues((previous) => ({ ...previous, [name]: event.target.value }))}
            aria-describedby="financial-unit"
          />
          <span aria-hidden="true">만 원</span>
        </div>
      </div>
    );
  }

  return (
    <div className="financial-page">
      <div className="financial-page-heading">
        <div>
          <h1>재무·신용정보 입력</h1>
          <p>월 소득과 지출을 입력하고, 내 재무에 맞는 구매 여력을 확인하세요.</p>
        </div>
        <span className="financial-stage-badge">1 / 5 · 소득·지출</span>
      </div>
      <FinancialProgress />

      <form onSubmit={handleSubmit}>
        <div className="financial-entry-grid">
          <section className="financial-entry-card" aria-labelledby="income-title">
            <h2 id="income-title">1. 소득·지출</h2>
            <p id="financial-unit">월 소득과 정기 지출을 입력해 주세요. 모든 금액은 만 원 단위입니다.</p>
            <p className="financial-required-note">* 표시는 필수 입력 항목입니다. 지출이 없으면 0을 입력해 주세요.</p>
            <div className="financial-fields">{fields.map(renderField)}</div>
            <FinancialProfileFields values={values} onChange={(name, value) => setValues((previous) => ({ ...previous, [name]: value }))} />

            <div className="financial-extra">
              <div className="financial-extra-heading">
                <div>
                  <h3>기타 정기 소득·교통비·통신비 (선택)</h3>
                  <p>선택 항목은 더 정확한 월 가용자금 계산에 활용됩니다.</p>
                  <p>이미 월 고정 지출이나 생활비에 포함했다면 중복 입력하지 마세요.</p>
                </div>
                <button
                  type="button"
                  className="financial-blue-button"
                  aria-expanded={expanded}
                  aria-controls="financial-extra-fields"
                  onClick={() => setExpanded((previous) => !previous)}
                >
                  {expanded ? '접기' : '입력하기'}
                </button>
              </div>
              <div
                id="financial-extra-fields"
                className={`financial-extra-slide${expanded ? ' expanded' : ''}`}
                inert={!expanded}
                aria-hidden={!expanded}
              >
                <div className="financial-extra-content">
                  <div className="financial-fields">{extraFields.map(renderField)}</div>
                </div>
              </div>
            </div>
          </section>

          <aside className="financial-live-card" aria-labelledby="live-title">
            <h2 id="live-title">실시간 계산</h2>
            <p>현재 예상 월 가용자금</p>
            <strong className="financial-available" aria-live="polite">
              {started ? `${format(available)}만 원` : '—'}
            </strong>
            <dl>
              <div><dt>월 실수령액 + 기타 소득</dt><dd>{format(income)}만 원</dd></div>
              <div><dt>총 지출·상환</dt><dd>{format(expenses)}만 원</dd></div>
              <div><dt>목표 저축액</dt><dd>{format(savings)}만 원</dd></div>
            </dl>
            <div className="financial-calculation-note">
              <h3>계산 기준</h3>
              <p>총 소득 − 주거비 − 고정 지출 − 생활비 − 대출 상환 − 교통비 − 통신비 − 목표 저축</p>
            </div>
            <p className="financial-live-hint">선택 항목을 비워두면 0원으로 계산합니다.</p>
          </aside>
        </div>
        <div className="financial-next-row">
          <button className="financial-next-button" type="submit">{location.state?.reviewReturn ? '수정 완료' : '다음 단계'}</button>
        </div>
      </form>
    </div>
  );
}
