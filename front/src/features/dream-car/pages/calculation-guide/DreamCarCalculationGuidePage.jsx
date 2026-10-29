import { Link, useSearchParams } from 'react-router-dom';
import catalog from '../../../../../../data/households/synthetic/sports-official-v1-20261028/catalog.json';
import { getVehicleCostDefaults, taxSource } from '../../vehicleCostDefaults';
import './DreamCarCalculationGuidePage.css';

export default function DreamCarCalculationGuidePage() {
  const [params] = useSearchParams();
  const vehicle = catalog.find(car => car.id === params.get('vehicle'));
  const rawDistance = params.get('distance');
  const distance = rawDistance !== null && rawDistance !== '' && Number.isFinite(Number(rawDistance)) && Number(rawDistance) >= 0 ? Number(rawDistance) : 12000;
  const defaults = vehicle ? getVehicleCostDefaults(vehicle, distance) : null;
  return <article className="dream-guide">
    <header><span>드림카 플래너</span><h1>구매·유지비 계산 기준</h1><p>자동 입력값은 자금 계획을 돕기 위한 예상치입니다. 실제 견적·납부 금액과 다를 수 있으며, 계산기에서 직접 수정할 수 있습니다.</p></header>
    {vehicle && <section><h2>선택 차량에 적용한 기준</h2><p>{vehicle.brand} {vehicle.model} · {vehicle.trim} · 연 {distance.toLocaleString('ko-KR')}km</p><dl>{Object.entries(defaults.notes).map(([key, note]) => <div key={key}><dt>{{ efficiency: '연비·전비', energyPrice: '연료·충전 단가', insurance: '연간 보험료', annualTax: '연간 자동차세', maintenance: '연간 정비·소모품' }[key]}</dt><dd>{note}</dd></div>)}</dl>{defaults.displacementSource && <a href={defaults.displacementSource} target="_blank" rel="noreferrer">선택 차량 배기량 출처</a>}</section>}
    <section><h2>연비와 연료·충전비</h2><p>연비·전비는 선택한 트림의 등록 사양을 사용합니다. 미등록 차량은 직접 입력해야 합니다. 참고용 사양은 국내 인증값과 다를 수 있습니다.</p><p className="dream-guide-formula">월 연료·충전비 = 연간 주행거리 ÷ 연비·전비 × 단가 ÷ 12</p><p>기본 단가는 가솔린·하이브리드 1,700원/L, 디젤 1,550원/L, LPG 1,000원/L, 전기 350원/kWh입니다. 실시간 시세가 아닌 계산용 가정입니다.</p></section>
    <section><h2>연간 자동차세</h2><p>배기량이 확인된 비영업용 신차는 배기량 전체에 해당 구간 세율을 적용하고 지방교육세 30%를 더합니다. 1,000cc 이하 80원/cc, 1,600cc 이하 140원/cc, 초과 200원/cc를 사용합니다. 비영업용 승용 전기차는 지방교육세를 포함해 연 13만 원을 적용합니다.</p><p className="dream-guide-formula">배기량 미확인·등록 차종 확인 필요 차량: 연 세금 예산 = 차량 가격 × 1% (최소 20만 원)</p><p>가격 기반 금액은 실제 세금 계산식이 아닌 예산용 추정입니다. 승합 등록 확인이 필요한 11인승 이상 차량도 이 추정 방식을 사용합니다. 차령 경감·연납 공제·감면은 반영하지 않습니다. 같은 배기량의 편의사양 트림은 세금이 같을 수 있습니다.</p><a href={taxSource} target="_blank" rel="noreferrer">자동차세 법령 기준 확인</a></section>
    <section><h2>연간 보험료</h2><p className="dream-guide-formula">보험료 예산 = 연 60만 원 + 차량 가격 × 1%</p><p>보험사 견적이 아닌 계획용 가정입니다. 운전자 나이·사고 이력·운전자 범위·보장 조건·주행거리 할인은 반영하지 않습니다.</p></section>
    <section><h2>연간 정비·소모품</h2><p className="dream-guide-formula">기준비 = 차량 가격 × 1.5% (최소 30만 원)<br />연 정비비 예산 = 기준비 × (40% + 60% × 연간 주행거리 ÷ 12,000km)</p><p>기준비 중 40%는 고정 적립, 60%는 주행에 따른 정비·타이어·소모품 비용으로 가정합니다. 5,000만 원 차량은 연 12,000km에서 75만 원, 24,000km에서 120만 원입니다. 최종 금액은 만 원 단위로 반올림합니다. 보증·차령·실제 정비 주기는 반영하지 않습니다.</p></section>
    <section><h2>구매 자금과 사용자가 정하는 비용</h2><p>취득·등록 비용은 차량 가격에 입력한 비율을 곱합니다. 기본 7%는 계산용 가정이며 차종별 감면·보조금은 자동 적용하지 않습니다. 주차비와 옵션·기타 초기비용은 사용자가 정합니다.</p><p className="dream-guide-formula">월 유지비 = 월 연료비 + 연 보험료 ÷ 12 + 연 자동차세 ÷ 12 + 연 정비비 ÷ 12 + 월 주차·기타 비용<br />목표 자금 = 차량 가격 + 취득·등록 비용 + 기타 초기비용 + 월 유지비 × 예비자금 개월 수</p><p>현금 구매 기준으로 할부금·감가상각·저축 이자·향후 가격 변동은 제외합니다.</p></section>
    <section><h2>자동 입력과 직접 수정</h2><p>모델·트림을 바꾸면 해당 차량의 사양과 가격으로 기본값을 다시 채웁니다. 주행거리를 바꾸면 연료비와 자동 정비비가 바뀝니다. 직접 수정한 정비비는 유지되며, ‘차량 기준값 다시 적용’을 누르면 자동 계산값으로 돌아갑니다.</p></section>
    <Link className="dream-guide-back" to="/dream-car">드림카 플래너로 이동</Link>
  </article>;
}
