import { useLocation, useNavigate } from 'react-router-dom';
import { calculateFinancialSummary } from '../../calculateFinancialSummary';
import { FinancialProgress } from '../overview/FinancialPage';
import '../../styles/FinancialPages.css';
import './FinancialReviewPage.css';

const formatAmount = (value) => Number(value || 0).toLocaleString('ko-KR', { maximumFractionDigits: 2 });
const money = (value) => value === undefined || value === '' ? '입력 안 함' : `${formatAmount(value)}만 원`;
const text = (value) => value || '입력 안 함';
const count = (value, unit) => /^\d+$/.test(value ?? '') ? `${value}${unit}` : value === '5 이상' ? `5${unit} 이상` : text(value);
const month = (value) => /^\d{4}-\d{2}$/.test(value ?? '') ? `${value.slice(0, 4)}년 ${Number(value.slice(5))}월` : text(value);

function ReviewCard({ title, id, onEdit, rows, children }) {
  return <section className="review-card" aria-labelledby={id}>
    <div className="review-card-heading"><h2 id={id}>{title}</h2><button type="button" onClick={onEdit} aria-label={`${title} 수정`}>수정</button></div>
    <dl>{rows.map(([label, value]) => <div key={label}><dt>{label}</dt><dd>{value}</dd></div>)}</dl>
    {children}
  </section>;
}

export default function FinancialReviewPage() {
  const { state } = useLocation();
  const navigate = useNavigate();
  const { values = {}, assets = {}, loans, credit = {}, vehicle = {}, priorities = [] } = state ?? {};
  const totals = calculateFinancialSummary(values);
  const edit = (path) => navigate(path, { state: { ...state, reviewReturn: true } });
  const incomeRows = [
    ['나이', values.age === undefined ? '입력 안 함' : `${values.age}세`], ['경력', values.career === undefined ? '입력 안 함' : `${values.career}년`],
    ['가구원 수', values.householdSize === undefined ? '입력 안 함' : `${values.householdSize}명`],
    ['부양 인원', values.dependents === undefined ? '입력 안 함' : `${values.dependents}명`],
    ['성별', text(values.gender)], ['직업 유형', text(values.employment)],
    ['연간 세전소득', money(values.annualGrossIncome)], ['실제 월평균 저축액', money(values.averageSavings)],
    ['월 실수령액', money(values.income)], ['기타 정기 소득', money(values.extraIncome)],
    ['월 주거비', money(values.housing)], ['월 고정 지출', money(values.fixed)], ['월 생활비', money(values.living)],
    ['현재 대출 월 상환액', money(values.loan)], ['교통비', money(values.transport)], ['통신비', money(values.phone)],
    ['월 지출·상환 합계', state?.values ? money(totals.expenses) : '입력 필요'], ['목표 저축', money(values.savings)],
    ['월 가용자금', state?.values ? money(totals.available) : '입력 필요'],
  ];
  const assetRows = [
    ['현금·사용 가능 예금', money(assets.deposit)], ['선수금', money(assets.downPayment)], ['비상자금', money(assets.emergency)],
    ['기타 금융자산', money(assets.financialAssets)], ['주거 보증금', money(assets.housingDeposit)], ['부동산 자산', money(assets.realEstate)],
    ['월 부채상환', loans ? money(loans.reduce((sum, loan) => sum + Number(loan.payment || 0), 0)) : '입력 필요'],
  ];
  const creditRows = [
    ['현재 연체', text(credit.overdue)], ['최근 1년 연체', count(credit.overdueCount, '회')],
    ['최근 6개월 신규 대출', count(credit.newLoans, '건')], ['보유 카드 수', count(credit.cards, '개')],
    ['신용거래 시작', month(credit.firstCredit)], ['NICE 점수', text(credit.nice)], ['KCB 점수', text(credit.kcb)],
  ];
  const vehicleRows = [
    ['추천 차량 범위', vehicle.segment === 'imported-car' ? '수입차' : '국내차'],
    ['목적', text(vehicle.purpose)], ['구매 구분', text(vehicle.purchase)], ['차종', text(vehicle.body)], ['연료', text(vehicle.fuel)],
    ['탑승 인원', text(vehicle.passengers)], ['연간 주행', text(vehicle.annualDistance)], ['도로 환경', text(vehicle.road)],
    ['충전 가능 여부', text(vehicle.charging)], ['할부 기간', text(vehicle.installment)],
  ];
  function handleAnalysis() {
    navigate('/financial/result', { state });
  }

  return <div className="financial-page review-page">
    <div className="financial-page-heading"><div><h1>입력정보 확인</h1><p>분석 전에 입력한 정보를 마지막으로 확인해 주세요.</p></div><span className="financial-stage-badge">5 / 5 · 확인</span></div>
    <FinancialProgress current={5} />
    <div className="review-grid">
      <ReviewCard title="소득·지출" id="review-income" rows={incomeRows} onEdit={() => edit('/financial')} />
      <ReviewCard title="자산·부채" id="review-assets" rows={assetRows} onEdit={() => edit('/financial/assets')}>
        {loans?.length > 0 && <div className="review-loans"><h3>대출 내역</h3>{loans.map((loan, index) => <div className="review-loan" key={loan.id}>
          <h4>{index + 1}. {loan.type}</h4><dl>
            <div><dt>잔액</dt><dd>{money(loan.balance)}</dd></div><div><dt>금리</dt><dd>{loan.rate === '' ? '입력 안 함' : `${loan.rate}%`}</dd></div>
            <div><dt>월 상환액</dt><dd>{money(loan.payment)}</dd></div><div><dt>남은 기간</dt><dd>{loan.months === '' ? '입력 안 함' : `${loan.months}개월`}</dd></div>
          </dl>
        </div>)}</div>}
        {loans?.length === 0 && <p className="review-empty">등록된 대출이 없습니다.</p>}
      </ReviewCard>
      <ReviewCard title="신용거래" id="review-credit" rows={creditRows} onEdit={() => edit('/financial/credit')} />
      <ReviewCard title="차량조건" id="review-vehicle" rows={vehicleRows} onEdit={() => edit('/financial/vehicle')}>
        <div className="review-priorities"><h3>중요조건 우선순위</h3>{priorities.length ? <ol>{priorities.map((item, index) => <li key={item}>{index + 1} {item}</li>)}</ol> : <p className="review-empty">입력 안 함</p>}</div>
      </ReviewCard>
    </div>
    <div className="financial-next-row review-navigation"><button type="button" className="review-previous" onClick={() => navigate('/financial/vehicle', { state: { ...state, reviewReturn: false } })}>이전</button><button type="button" className="financial-next-button" onClick={handleAnalysis}>분석 결과 확인</button></div>
    <aside className="review-note"><h2>분석 전 확인</h2><p>입력값은 추천 시뮬레이션에만 사용되며 실제 금융기관의 심사 결과를 의미하지 않습니다.</p></aside>
    <div className="review-analysis"><p>입력한 조건으로 감당 가능한 첫차 범위를 계산합니다.</p><button type="button" onClick={handleAnalysis}>분석 결과 확인하기</button></div>
  </div>;
}
