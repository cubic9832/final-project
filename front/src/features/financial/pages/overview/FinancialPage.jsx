import { useState } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import FinancialAssetsFields from '../../components/FinancialAssetsFields.jsx';
import FinancialBudgetSummary from '../../components/FinancialBudgetSummary.jsx';
import '../../styles/FinancialPages.css';

const fields = [
  { name: 'income', label: '월 실수령액', required: true },
  { name: 'housing', label: '월 주거비', required: true },
  { name: 'fixed', label: '월 고정 지출', required: true },
  { name: 'living', label: '월 생활비', required: true },
  { name: 'savings', label: '월 목표 저축액 · 예산 계산용', required: false },
];

const extraFields = [
  { name: 'extraIncome', label: '기타 정기 소득', required: false },
  { name: 'transport', label: '교통비', required: false },
  { name: 'phone', label: '통신비', required: false },
];

const steps = ['재무 정보', '차량 이용', '확인'];

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
        <span style={{ width: `${current / steps.length * 100}%` }} />
      </div>
    </div>
  );
}

export default function FinancialPage() {
  const navigate = useNavigate();
  const [fieldErrors, setFieldErrors] = useState({});
  const location = useLocation();
  const [values, setValues] = useState(location.state?.values ?? {});
  const [assets, setAssets] = useState({ deposit: location.state?.assets?.deposit ?? '' });
  const [loans, setLoans] = useState(() => (location.state?.loans ?? []).filter(loan => loan.balance !== '' || loan.payment !== '').map(loan => ({ ...loan, id: loan.id ?? crypto.randomUUID() })));
  const [expanded, setExpanded] = useState(
    extraFields.some(({ name }) => location.state?.values?.[name] !== undefined)
  );


  function handleSubmit(event) {
    event.preventDefault();
    if (!event.currentTarget.reportValidity()) return;
    navigate(location.state?.reviewReturn ? '/financial/review' : '/financial/vehicle', { state: { ...location.state, values, assets, loans, reviewReturn: false } });
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
            onChange={(event) => { setValues((previous) => ({ ...previous, [name]: event.target.value })); setFieldErrors((previous) => ({ ...previous, [name]: '' })); }}
            aria-invalid={Boolean(fieldErrors[name])}
            onInvalid={(event) => { event.preventDefault(); if (extraFields.some(field => field.name === name)) setExpanded(true); const message = event.currentTarget.validationMessage; setFieldErrors((previous) => ({ ...previous, [name]: message })); }}
            aria-describedby={fieldErrors[name] ? `financial-${name}-error` : 'financial-unit'}
          />
          <span aria-hidden="true">만 원</span>
        </div>
        {fieldErrors[name] && <p className="financial-field-error" id={`financial-${name}-error`} role="alert">{fieldErrors[name]}</p>}
      </div>
    );
  }

  return (
    <div className="financial-page">
      <div className="financial-page-heading">
        <div>
          <span className="financial-eyebrow">나에게 맞는 첫차 찾기</span><h1>재무 정보를 알려주세요</h1>
          <p>소득·지출과 예금·대출 내역을 한 번에 입력해 주세요.</p>
        </div>
        <span className="financial-stage-badge">1 / 3 · 재무 정보</span>
      </div>
      <FinancialProgress />

      <form onSubmit={handleSubmit}>
        <div className="financial-entry-grid">
          <section className="financial-entry-card" aria-labelledby="income-title">
            <h2 id="income-title">월 소득과 생활비</h2>
            <p id="financial-unit">모든 금액은 만 원 단위로 입력해 주세요.</p>
            <p className="financial-required-note">* 표시는 필수 입력 항목입니다. 지출이 없으면 0을 입력해 주세요.</p>
            <div className="financial-fields">{fields.map(renderField)}</div>

            <div className="financial-extra">
              <div className="financial-extra-heading">
                <div>
                  <h3>추가 소득과 지출 (선택)</h3>
                  <p>기타 소득·교통비·통신비가 있다면 추가해 주세요.</p>
                  <p>생활비에 포함한 항목은 다시 입력하지 않아도 됩니다.</p>
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
            <FinancialAssetsFields assets={assets} setAssets={setAssets} loans={loans} setLoans={setLoans} />
          </section>

          <FinancialBudgetSummary values={values} assets={assets} loans={loans} />
        </div>
        <div className="financial-next-row">
          <button className="financial-next-button" type="submit">{location.state?.reviewReturn ? '수정 완료' : '다음 단계'}</button>
        </div>
      </form>
    </div>
  );
}
