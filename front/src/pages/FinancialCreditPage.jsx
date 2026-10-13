import { useState } from 'react';
import { Navigate, useLocation, useNavigate } from 'react-router-dom';
import { FinancialProgress } from './FinancialPage';
import './FinancialPage.css';
import './FinancialAssetsPage.css';
import './FinancialCreditPage.css';

const overdueOptions = ['연체 없음', '30일 미만', '30일 이상', '잘 모르겠어요'];
const selectFields = [
  { name: 'lateCount', label: '최근 1년 연체 횟수', options: ['0회', '1회', '2회', '3회 이상', '잘 모르겠어요'] },
  { name: 'newLoans', label: '최근 6개월 신규 대출', options: ['0건', '1건', '2건', '3건 이상', '잘 모르겠어요'] },
  { name: 'cards', label: '보유 카드 수', options: ['0개', '1개', '2개', '3개', '4개 이상', '잘 모르겠어요'] },
];
const scoreOptions = ['입력 안 함', '900~1,000점', '800~899점', '700~799점', '600~699점', '600점 미만'];

export default function FinancialCreditPage() {
  const { state } = useLocation();
  const navigate = useNavigate();
  const [credit, setCredit] = useState(state?.credit ?? {
    overdue: '', lateCount: '', newLoans: '', cards: '', firstCredit: '', nice: '입력 안 함', kcb: '입력 안 함',
  });
  const completed = ['overdue', 'lateCount', 'newLoans', 'cards', 'firstCredit']
    .filter((name) => credit[name] !== '').length;

  if (!state?.values) return <Navigate to="/financial" replace />;

  function update(name, value) {
    setCredit((previous) => ({ ...previous, [name]: value }));
  }

  function handleSubmit(event) {
    event.preventDefault();
    navigate('/financial/vehicle', { state: { ...state, credit } });
  }

  return (
    <div className="financial-page credit-page">
      <div className="financial-page-heading">
        <div>
          <h1>재무·신용정보 입력</h1>
          <p>정확한 점수 대신 신용거래 패턴으로 자체 위험도를 분석합니다.</p>
        </div>
        <span className="financial-stage-badge">3 / 5 · 신용정보</span>
      </div>
      <FinancialProgress current={3} />

      <form onSubmit={handleSubmit}>
        <div className="financial-entry-grid">
          <section className="financial-entry-card" aria-labelledby="credit-title">
            <h2 id="credit-title">3. 신용정보</h2>
            <p>현재 상태에 가장 가까운 항목을 선택해 주세요.</p>

            <fieldset className="credit-overdue">
              <legend>현재 연체 중인 금액이 있나요?</legend>
              <div className="credit-chip-group">
                {overdueOptions.map((option) => (
                  <label className="credit-chip" key={option}>
                    <input
                      type="radio"
                      name="overdue"
                      value={option}
                      checked={credit.overdue === option}
                      onChange={() => update('overdue', option)}
                      required
                    />
                    <span>{option}</span>
                  </label>
                ))}
              </div>
            </fieldset>

            <div className="credit-select-fields">
              {selectFields.map(({ name, label, options }) => (
                <div className="financial-field" key={name}>
                  <label htmlFor={`credit-${name}`}>{label}</label>
                  <select
                    id={`credit-${name}`}
                    value={credit[name]}
                    onChange={(event) => update(name, event.target.value)}
                    required
                  >
                    <option value="" disabled>선택해 주세요</option>
                    {options.map((option) => <option key={option} value={option}>{option}</option>)}
                  </select>
                </div>
              ))}
              <div className="financial-field">
                <label htmlFor="credit-first">최초 신용거래 시점</label>
                <select
                  id="credit-first"
                  value={credit.firstCredit}
                  onChange={(event) => update('firstCredit', event.target.value)}
                  required
                >
                  <option value="" disabled>선택해 주세요</option>
                  {['1년 미만', '1~3년', '3~5년', '5~10년', '10년 이상', '신용거래 없음', '잘 모르겠어요']
                    .map((option) => <option key={option} value={option}>{option}</option>)}
                </select>
              </div>
            </div>

            <section className="credit-scores" aria-labelledby="scores-title">
              <div className="credit-scores-heading">
                <div>
                  <h3 id="scores-title">NICE / KCB 점수</h3>
                  <p>참고용 선택정보이며 입력하지 않아도 분석할 수 있습니다.</p>
                </div>
                <span>선택 입력</span>
              </div>
              <div className="credit-score-grid">
                {['nice', 'kcb'].map((name) => (
                  <div className="financial-field" key={name}>
                    <label htmlFor={`credit-${name}`}>{name.toUpperCase()} 점수 (선택)</label>
                    <select id={`credit-${name}`} value={credit[name]} onChange={(event) => update(name, event.target.value)}>
                      {scoreOptions.map((option) => <option key={option} value={option}>{option}</option>)}
                    </select>
                  </div>
                ))}
              </div>
            </section>

            <aside className="credit-analysis-note">
              <h3>분석 방식</h3>
              <p>신용거래 기간, 연체 여부, 신규 대출, 카드 수를 조합해 프로필의 자체 위험도를 계산합니다.</p>
            </aside>
          </section>

          <aside className="financial-entry-card credit-summary" aria-labelledby="credit-summary-title">
            <h2 id="credit-summary-title">현재 입력 상태</h2>
            <p aria-live="polite">필수 항목 5개 중 {completed}개 완료</p>
            <div className="credit-status-card mint-status">
              <span>현재 연체</span>
              <strong>{credit.overdue === '연체 없음' ? '없음' : credit.overdue || '선택 전'}</strong>
              <p>현재 연체 상태를 반영합니다.</p>
            </div>
            <div className="credit-status-card yellow-status">
              <span>신규 대출</span>
              <strong>{credit.newLoans || '선택 전'}</strong>
              <p>최근 6개월 이내 발생</p>
            </div>
            <ul className="credit-summary-list">
              <li>신용점수 직접 조회 없음</li>
              <li>금융기관 심사와 분리</li>
              <li>입력값은 언제든 수정 가능</li>
            </ul>
          </aside>
        </div>

        <div className="financial-next-row assets-navigation">
          <button
            type="button"
            className="assets-previous-button"
            onClick={() => navigate('/financial/assets', { state: { ...state, credit } })}
          >
            이전
          </button>
          <button className="financial-next-button" type="submit">다음 단계</button>
        </div>
      </form>
    </div>
  );
}
