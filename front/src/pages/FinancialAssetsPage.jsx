import { useState } from 'react';
import { Navigate, useLocation, useNavigate } from 'react-router-dom';
import { FinancialProgress } from './FinancialPage';
import './FinancialPage.css';
import './FinancialAssetsPage.css';

const assetFields = [
  { name: 'deposit', label: '사용 가능 예금' },
  { name: 'downPayment', label: '차량 선수금' },
  { name: 'emergency', label: '비상 자금' },
];

const loanFields = [
  { name: 'balance', label: '잔액', unit: '만 원', step: '0.01' },
  { name: 'rate', label: '금리', unit: '%', step: '0.01' },
  { name: 'payment', label: '월 상환액', unit: '만 원', step: '0.01' },
  { name: 'months', label: '남은 기간', unit: '개월', step: '1' },
];

const loanTypes = ['신용대출', '주택담보대출', '전세자금대출', '학자금대출', '자동차대출', '카드론', '기타 대출'];
const createLoan = () => ({ id: crypto.randomUUID(), type: '신용대출', balance: '', rate: '', payment: '', months: '' });
const format = (value) => value.toLocaleString('ko-KR', { maximumFractionDigits: 2 });

export default function FinancialAssetsPage() {
  const { state } = useLocation();
  const navigate = useNavigate();
  const [assets, setAssets] = useState(state?.assets ?? { deposit: '', downPayment: '', emergency: '' });
  const [loans, setLoans] = useState(() => state?.loans ?? [createLoan()]);
  const income = Number(state?.values?.income || 0);
  const balance = loans.reduce((sum, loan) => sum + Number(loan.balance || 0), 0);
  const payment = loans.reduce((sum, loan) => sum + Number(loan.payment || 0), 0);
  const ratio = income > 0 ? payment / income * 100 : null;
  const available = Math.max(0, Number(assets.deposit || 0) - Number(assets.emergency || 0));

  if (!state?.values) return <Navigate to="/financial" replace />;

  function updateLoan(id, name, value) {
    setLoans((previous) => previous.map((loan) => loan.id === id ? { ...loan, [name]: value } : loan));
  }

  function handleSubmit(event) {
    event.preventDefault();
    navigate('/financial/credit', { state: { ...state, assets, loans } });
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
            min="0"
            step={step}
            inputMode={name === 'months' ? 'numeric' : 'decimal'}
            placeholder="0"
            value={loan ? loan[name] : assets[name]}
            aria-label={`${label} (${unit})`}
            onChange={(event) => {
              const value = event.target.value;
              if (loan) updateLoan(loan.id, name, value);
              else setAssets((previous) => ({ ...previous, [name]: value }));
            }}
          />
          <span aria-hidden="true">{unit}</span>
        </div>
      </div>
    );
  }

  return (
    <div className="financial-page assets-page">
      <div className="financial-page-heading">
        <div>
          <h1>재무·신용정보 입력</h1>
          <p>구매에 활용할 자금과 현재 갚고 있는 부채를 입력해 주세요.</p>
        </div>
        <span className="financial-stage-badge">2 / 5 · 자산·부채</span>
      </div>
      <FinancialProgress current={2} />

      <form onSubmit={handleSubmit}>
        <div className="financial-entry-grid">
          <section className="financial-entry-card assets-entry-card" aria-labelledby="assets-title">
            <h2 id="assets-title">2. 자산·부채</h2>
            <p>모든 금액은 만 원 단위이며 실제 구매에 사용할 수 있는 범위만 입력합니다.</p>
            <div className="assets-fields">{assetFields.map((field) => renderInput(field))}</div>

            <div className="assets-loan-heading">
              <div>
                <h3>대출 내역</h3>
                <p>대출을 추가하면 월 부채부담이 자동으로 계산됩니다.</p>
              </div>
              <button
                type="button"
                className="assets-add-button"
                onClick={() => setLoans((previous) => [...previous, createLoan()])}
              >
                + 대출 추가
              </button>
            </div>

            <div className="assets-loans">
              {loans.map((loan, index) => (
                <section className="assets-loan-card" key={loan.id} aria-labelledby={`loan-title-${loan.id}`}>
                  <div className="assets-loan-card-heading">
                    <h4 id={`loan-title-${loan.id}`}>{loan.type}</h4>
                    <button
                      type="button"
                      className="assets-delete-button"
                      aria-label={`${index + 1}번째 ${loan.type} 삭제`}
                      onClick={() => setLoans((previous) => previous.filter((item) => item.id !== loan.id))}
                    >
                      삭제
                    </button>
                  </div>
                  <div className="assets-loan-fields">
                    <div className="financial-field assets-loan-type">
                      <label htmlFor={`loan-${loan.id}-type`}>종류</label>
                      <select
                        id={`loan-${loan.id}-type`}
                        value={loan.type}
                        onChange={(event) => updateLoan(loan.id, 'type', event.target.value)}
                      >
                        {loanTypes.map((type) => <option key={type} value={type}>{type}</option>)}
                      </select>
                    </div>
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
          </section>

          <aside className="financial-live-card assets-live-card" aria-labelledby="debt-title">
            <h2 id="debt-title">월 부채부담 요약</h2>
            <p>소득 대비 월 상환 비율</p>
            <strong className="financial-available" aria-live="polite">
              {ratio === null ? '—' : `${ratio.toFixed(1)}%`}
            </strong>
            <span className="assets-ratio-badge">
              {ratio === null ? '소득 입력 필요' : ratio <= 20 ? '참고 범위 이내' : '상환 부담 확인'}
            </span>
            <dl>
              <div><dt>월 실수령액</dt><dd>{format(income)}만 원</dd></div>
              <div><dt>총 대출 잔액</dt><dd>{format(balance)}만 원</dd></div>
              <div><dt>월 상환액</dt><dd>{format(payment)}만 원</dd></div>
              <div className="assets-purchase-amount"><dt>구매 활용 가능액</dt><dd>{format(available)}만 원</dd></div>
            </dl>
            <div className="assets-evaluation">
              <h3>계산 기준</h3>
              <p>월 상환액 합계 ÷ 월 실수령액 × 100</p>
              <p>구매 활용 가능액은 사용 가능 예금에서 비상 자금을 제외한 금액입니다. 선수금은 그 안에서 사용할 계획 금액입니다.</p>
              <p>20% 표시는 화면의 참고 기준이며 실제 금융 심사 결과가 아닙니다.</p>
            </div>
          </aside>
        </div>

        <div className="financial-next-row assets-navigation">
          <button
            type="button"
            className="assets-previous-button"
            onClick={() => navigate('/financial', { state: { ...state, assets, loans } })}
          >
            이전
          </button>
          <button className="financial-next-button" type="submit">다음 단계</button>
        </div>
      </form>
    </div>
  );
}
