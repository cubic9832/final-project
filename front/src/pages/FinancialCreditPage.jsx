import { useState } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { FinancialProgress } from './FinancialPage';
import './FinancialPage.css';
import './FinancialCreditPage.css';

const overdueOptions = ['연체 없음', '30일 미만', '30일 이상', '잘 모르겠어요'];
const countOptions = ['0', '1', '2', '3', '4', '5 이상', '잘 모르겠어요'];
const creditFields = [
  { name: 'overdueCount', label: '최근 1년 연체 횟수', options: countOptions, unit: '회' },
  { name: 'newLoans', label: '최근 6개월 신규 대출', options: countOptions, unit: '건' },
  { name: 'cards', label: '보유 카드 수', options: countOptions, unit: '개' },
];
const initialCredit = { overdue: '연체 없음', overdueCount: '0', newLoans: '1', cards: '2', firstCredit: '2021-03', nice: '', kcb: '' };
const scoreOptions = ['900~1,000점', '800~899점', '700~799점', '600~699점', '600점 미만'];
const formatCount = (value, unit) => /^\d+$/.test(value) ? `${value}${unit}` : value === '5 이상' ? `5${unit} 이상` : value;

function CreditSelect({ name, label, value, options, unit = '', onChange }) {
  return (
    <div className="financial-field">
      <label htmlFor={`credit-${name}`}>{label}</label>
      <select id={`credit-${name}`} name={name} value={value} onChange={(event) => onChange(name, event.target.value)}>
        {options.map((option) => <option key={option} value={option}>{unit ? formatCount(option, unit) : option || '입력 안 함'}</option>)}
      </select>
    </div>
  );
}

export default function FinancialCreditPage() {
  const { state } = useLocation();
  const navigate = useNavigate();
  const [credit, setCredit] = useState(() => ({ ...initialCredit, ...state?.credit }));
  const completed = ['overdue', 'overdueCount', 'newLoans', 'cards', 'firstCredit'].filter((name) => credit[name] !== '').length;
  const [currentMonth] = useState(() => {
    const today = new Date();
    return `${today.getFullYear()}-${String(today.getMonth() + 1).padStart(2, '0')}`;
  });
  const updateCredit = (name, value) => {
    setCredit((previous) => ({ ...previous, [name]: value }));
  };

  function handleSubmit(event) {
    event.preventDefault();
    navigate(state?.reviewReturn ? '/financial/review' : '/financial/vehicle', { state: { ...state, credit, reviewReturn: false } });
  }

  return (
    <div className="financial-page credit-page">
      <div className="financial-page-heading">
        <div>
          <h1>재무·신용정보 입력</h1>
          <p>정확한 점수 대신 신용거래 패턴으로 차량 예산을 분석합니다.</p>
        </div>
        <span className="financial-stage-badge">3 / 5 · 신용정보</span>
      </div>
      <FinancialProgress current={3} />
      <form onSubmit={handleSubmit}>
        <div className="financial-entry-grid">
          <section className="financial-entry-card credit-entry-card" aria-labelledby="credit-title">
            <h2 id="credit-title">3. 신용정보</h2>
            <p>현재 상태에 가장 가까운 항목을 선택해 주세요.</p>
            <fieldset className="credit-overdue">
              <legend>현재 연체 중인 금액이 있나요?</legend>
              <div className="credit-options">
                {overdueOptions.map((option) => (
                  <label key={option} className="credit-option">
                    <input type="radio" name="overdue" value={option} checked={credit.overdue === option} onChange={() => updateCredit('overdue', option)} />
                    <span>{option}</span>
                  </label>
                ))}
              </div>
            </fieldset>
            <div className="credit-fields">
              {creditFields.map((field) => <CreditSelect key={field.name} {...field} value={credit[field.name]} onChange={updateCredit} />)}
              <div className="financial-field">
                <label htmlFor="credit-first-credit">최초 신용거래 시점</label>
                <input id="credit-first-credit" type="month" required min="1950-01" max={currentMonth} value={credit.firstCredit} onChange={(event) => updateCredit('firstCredit', event.target.value)} />
              </div>
            </div>
            <section className="credit-score-panel" aria-labelledby="credit-score-title">
              <div className="credit-score-heading">
                <h3 id="credit-score-title">NICE / KCB 점수</h3>
                <span>선택 입력</span>
              </div>
              <p>참고용 선택정보이며 입력하지 않아도 분석할 수 있습니다.</p>
              <div className="credit-score-fields">
                <CreditSelect name="nice" label="NICE 점수" value={credit.nice} options={['', ...scoreOptions]} onChange={updateCredit} />
                <CreditSelect name="kcb" label="KCB 점수" value={credit.kcb} options={['', ...scoreOptions]} onChange={updateCredit} />
              </div>
            </section>
            <aside className="credit-method">
              <h3>분석 방식</h3>
              <p>신용거래 기간, 연체 여부, 신규 대출, 카드 수를 종합해 프로젝트 자체 위험도를 계산합니다.</p>
            </aside>
          </section>
          <aside className="credit-summary" aria-labelledby="credit-summary-title">
            <h2 id="credit-summary-title">현재 입력 상태</h2>
            <p aria-live="polite">필수 항목 5개 중 {completed}개 완료</p>
            <div className="credit-status-card credit-status-overdue" aria-live="polite">
              <h3>현재 연체</h3>
              <strong>{credit.overdue === '연체 없음' ? '없음' : credit.overdue}</strong>
              <p>{credit.overdue === '연체 없음' ? '위험도를 낮추는 요인' : credit.overdue === '잘 모르겠어요' ? '현재 연체 여부 확인 필요' : '분석 시 연체 기간을 함께 반영'}</p>
            </div>
            <div className="credit-status-card credit-status-loans" aria-live="polite">
              <h3>신규 대출</h3>
              <strong>{formatCount(credit.newLoans, '건')}</strong>
              <p>최근 6개월 이내 발생</p>
            </div>
            <ul className="credit-summary-notes">
              <li>신용점수 직접 조회 없음</li>
              <li>금융기관 심사와 분리</li>
              <li>입력값은 언제든 수정 가능</li>
            </ul>
          </aside>
        </div>
        <div className="financial-next-row credit-navigation">
          <button type="button" className="credit-previous-button" onClick={() => navigate('/financial/assets', { state: { ...state, credit } })}>이전</button>
          <button type="submit" className="financial-next-button">{state?.reviewReturn ? '수정 완료' : '다음 단계'}</button>
        </div>
      </form>
    </div>
  );
}
