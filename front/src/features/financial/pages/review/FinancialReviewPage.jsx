import { normalizeCharging } from '../../chargingPreferences.js';
import { useLocation, useNavigate } from 'react-router-dom';
import { calculateFinancialSummary } from '../../calculateFinancialSummary';
import { importanceLabel, sizeLabel } from '../../vehiclePreferences.js';
import { FinancialProgress } from '../overview/FinancialPage';
import '../../styles/FinancialPages.css';
import './FinancialReviewPage.css';

const formatAmount = (value) => Number(value || 0).toLocaleString('ko-KR', { maximumFractionDigits: 2 });
const money = (value) => value === undefined || value === '' ? '입력 안 함' : `${formatAmount(value)}만 원`;
const text = (value) => value || '입력 안 함';
function ReviewCard({ title, id, onEdit, rows, detailsRows = [], children }) {
  return <section className="review-card" aria-labelledby={id}>
    <div className="review-card-heading"><h2 id={id}>{title}</h2><button type="button" onClick={onEdit} aria-label={`${title} 수정`}>수정</button></div>
    <dl>{rows.map(([label, value]) => <div key={label}><dt>{label}</dt><dd>{value}</dd></div>)}</dl>
    {detailsRows.length > 0 && <details className="financial-disclosure"><summary>입력 내역 전체 보기</summary><dl>{detailsRows.map(([label, value]) => <div key={label}><dt>{label}</dt><dd>{value}</dd></div>)}</dl></details>}
    {children}
  </section>;
}

export default function FinancialReviewPage() {
  const { state } = useLocation();
  const navigate = useNavigate();
  const { values = {}, assets = {}, loans = [], vehicle = {} } = state ?? {};
  const totals = calculateFinancialSummary(values, loans);
  const edit = (path) => navigate(path, { state: { ...state, reviewReturn: true } });
  const incomeRows = [
    ['월 실수령액', money(values.income)], ['기타 정기 소득', money(values.extraIncome)],
    ['월 주거비', money(values.housing)], ['월 고정 지출', money(values.fixed)], ['월 생활비', money(values.living)],
    ['현재 대출 월 상환액', money(totals.loanPayment)], ['교통비', money(values.transport)], ['통신비', money(values.phone)],
    ['월 지출·상환 합계', state?.values ? money(totals.expenses) : '입력 필요'], ['목표 저축', money(values.savings)],
    ['월 가용자금', state?.values ? money(totals.available) : '입력 필요'],
  ];
  const assetRows = [
    ['사용 가능 예금', money(assets.deposit)],
    ['월 부채상환', loans ? money(loans.reduce((sum, loan) => sum + Number(loan.payment || 0), 0)) : '입력 필요'],
  ];
  const vehicleRows = [['추천용 이용 목적', text(vehicle.purpose)], ['선호 연료', text(vehicle.fuel)], ...(vehicle.fuel === '전기' ? [['충전 환경', text(normalizeCharging(vehicle.charging))]] : []), ['가성비 중요도', importanceLabel(vehicle.costImportance)], ['공간 중요도', importanceLabel(vehicle.spaceImportance)], ['연료 중요도', importanceLabel(vehicle.fuelImportance ?? '3')], ['인원 중요도', importanceLabel(vehicle.seatingImportance ?? '3')], ['목적 중요도', importanceLabel(vehicle.purposeImportance ?? '1')], ['선호 크기', sizeLabel(vehicle.preferredSize)], ['희망 탑승 인원', Number(vehicle.minimumSeats) > 0 ? `${vehicle.minimumSeats}명` : '미지정']];
  function handleAnalysis() {
    navigate('/financial/result', { state });
  }

  return <div className="financial-page review-page">
    <div className="financial-page-heading"><div><span className="financial-eyebrow">이제 준비가 끝났어요</span><h1>입력한 내용을 확인해 주세요</h1><p>분석 전에 입력한 정보를 마지막으로 확인해 주세요.</p></div><span className="financial-stage-badge">3 / 3 · 확인</span></div>
    <FinancialProgress current={3} />
    <div className="review-grid">
      <ReviewCard title="소득·지출" id="review-income" rows={incomeRows.filter(([label]) => ['월 실수령액', '월 지출·상환 합계', '목표 저축', '월 가용자금'].includes(label))} detailsRows={incomeRows.filter(([label]) => !['월 실수령액', '월 지출·상환 합계', '목표 저축', '월 가용자금'].includes(label))} onEdit={() => edit('/financial')} />
      <ReviewCard title="자산·부채" id="review-assets" rows={assetRows} onEdit={() => edit('/financial')}>
        {loans?.length > 0 && <div className="review-loans"><h3>대출 내역</h3>{loans.map((loan, index) => <div className="review-loan" key={loan.id}>
          <h4>대출 {index + 1}</h4><dl>
            <div><dt>잔액</dt><dd>{money(loan.balance)}</dd></div>
            <div><dt>월 상환액</dt><dd>{money(loan.payment)}</dd></div>
          </dl>
        </div>)}</div>}
        {loans?.length === 0 && <p className="review-empty">등록된 대출이 없습니다.</p>}
      </ReviewCard>
      <ReviewCard title="차량 이용" id="review-vehicle" rows={vehicleRows.filter(([label]) => ['추천용 이용 목적', '선호 연료', '선호 크기', '희망 탑승 인원'].includes(label))} detailsRows={vehicleRows.filter(([label]) => !['추천용 이용 목적', '선호 연료', '선호 크기', '희망 탑승 인원'].includes(label))} onEdit={() => edit('/financial/vehicle')} />
    </div>
    <div className="financial-next-row review-navigation"><button type="button" className="review-previous" onClick={() => navigate('/financial/vehicle', { state: { ...state, reviewReturn: false } })}>이전</button><button type="button" className="financial-next-button" onClick={handleAnalysis}>분석 결과 확인</button></div>
    <aside className="review-note"><h2>분석 전 확인</h2><p>월 소득에서 생활비·기존 대출 상환·목표 저축을 제외한 뒤, 후보별 예상 유지비를 계산합니다. 입력한 예금으로 구매하고 월 유지비를 감당할 수 있는 차량을 추천합니다.</p></aside>

  </div>;
}
