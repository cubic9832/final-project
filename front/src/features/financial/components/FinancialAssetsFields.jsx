import { useState } from 'react';
import './FinancialAssetsFields.css';

const assetFields = [{ name: 'deposit', label: '사용 가능 예금' }];
const loanFields = [
  { name: 'balance', label: '잔액 (선택 · 현황 확인용)', unit: '만 원', step: '0.01' },
  { name: 'payment', label: '월 상환액', unit: '만 원', step: '0.01' },
];
const createLoan = () => ({ id: crypto.randomUUID(), balance: '', payment: '' });

export default function FinancialAssetsFields({ assets, setAssets, loans, setLoans }) {
  const [fieldErrors, setFieldErrors] = useState({});
  function updateLoan(id, name, value) {
    setLoans((previous) => previous.map((loan) => loan.id === id ? { ...loan, [name]: value } : loan));
  }

  function renderInput({ name, label, unit = '만 원', step = '0.01' }, loan) {
    const id = loan ? `loan-${loan.id}-${name}` : `asset-${name}`;
    return (
      <div className="financial-field" key={name}>
        <label htmlFor={id}>{label}</label>
        <div className="financial-input-wrap">
          <input
            id={id}
            name={id}
            type="number"
            required={!loan || name === 'payment'}
            min="0"
            step={step}
            inputMode={name === 'months' ? 'numeric' : 'decimal'}
            placeholder="0"
            value={loan ? loan[name] : assets[name]}
            aria-label={`${label} (${unit})`}
            aria-invalid={Boolean(fieldErrors[id])}
            aria-describedby={fieldErrors[id] ? `${id}-error` : undefined}
            onInvalid={(event) => { event.preventDefault(); const message = event.currentTarget.validationMessage; setFieldErrors((previous) => ({ ...previous, [id]: message })); }}
            onChange={(event) => {
              const value = event.target.value;
              setFieldErrors((previous) => ({ ...previous, [id]: '' }));
              if (loan) updateLoan(loan.id, name, value);
              else setAssets((previous) => ({ ...previous, [name]: value }));
            }}
          />
          <span aria-hidden="true">{unit}</span>
        </div>
        {fieldErrors[id] && <p className="financial-field-error" id={`${id}-error`} role="alert">{fieldErrors[id]}</p>}
      </div>
    );
  }

  return <div className="financial-assets-fields">
            <h2 id="assets-title">자산과 대출 내역</h2>
            <p>차량 구매에 사용할 수 있는 예금을 입력해 주세요. 단위는 만 원입니다.</p>
            <div className="assets-fields">{assetFields.map((field) => renderInput(field))}</div>

            <details className="financial-disclosure assets-debt-details" open={loans.length > 0} onInvalidCapture={event => { event.currentTarget.open = true; }}>
              <summary>갚고 있는 대출이 있나요? <span>선택 입력</span></summary>
            <div className="assets-loan-heading">
              <div>
                <h3>대출 내역</h3>
                <p>매달 갚는 금액을 입력하면 유지비 예산에 반영합니다.</p>
              </div>
              <button
                type="button"
                className="assets-add-button"
                onClick={() => setLoans((previous) => [...previous, createLoan()])}
              >
                대출 추가
              </button>
            </div>

            <div className="assets-loans">
              {loans.map((loan, index) => (
                <section className="assets-loan-card" key={loan.id} aria-labelledby={`loan-title-${loan.id}`}>
                  <div className="assets-loan-card-heading">
                    <h4 id={`loan-title-${loan.id}`}>대출 {index + 1}</h4>
                    <button
                      type="button"
                      className="assets-delete-button"
                      aria-label={`${index + 1}번째 대출 삭제`}
                      onClick={() => setLoans((previous) => previous.filter((item) => item.id !== loan.id))}
                    >
                      삭제
                    </button>
                  </div>
                  <div className="assets-loan-fields">
                    {loanFields.map((field) => renderInput(field, loan))}
                  </div>
                </section>
              ))}
              {loans.length === 0 && <p className="assets-empty">등록된 대출이 없습니다. 대출이 있다면 추가해 주세요.</p>}
            </div>

            <aside className="assets-input-tip">
              <h3>입력 팁</h3>
              <p>학자금대출·자동차대출·카드론 등 상환액이 있다면 함께 입력해 주세요.</p>
            </aside>
            </details>
  </div>;
}
