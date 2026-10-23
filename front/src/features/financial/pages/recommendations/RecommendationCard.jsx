import { useState } from 'react';
import { Car } from 'lucide-react';
import theme from '../../../../styles/theme.js';
import { candidateImage, candidateMoney, fuelLabels } from './candidatePresentation.js';
import { buildCandidateHighlights } from './buildCandidateHighlights.js';

export default function RecommendationCard({ candidate, rank, preferences }) {
  const [failed, setFailed] = useState(false);
  const { vehicle, cost, reasons } = candidate;
  const image = candidateImage(vehicle);
  const highlights = buildCandidateHighlights(candidate, preferences);
  return <li className="financial-recommendation-card">
    <div className="financial-recommendation-media"><span className="financial-recommendation-rank">{candidate.seatingVerificationRequired || candidate.lengthVerificationRequired ? '확인 후보' : '추천'} {rank}</span>
      {image && !failed ? <img src={image.src} alt={image.alt} style={image.style} loading="lazy" onError={() => setFailed(true)} /> : <div className="financial-recommendation-image-placeholder"><Car size={theme.iconSize.lg} aria-hidden="true" /><span>차량 이미지 준비 중</span></div>}
    </div>
    <div className="financial-recommendation-card-body">
      <p className="financial-recommendation-category">{vehicle.brand} · {{MILD_HYBRID: '마일드 하이브리드', PHEV: '플러그인 하이브리드'}[vehicle.original_fuel] || fuelLabels[vehicle.fuel] || vehicle.fuel}</p>
      <h2>{vehicle.model}</h2><p>{vehicle.year && `${vehicle.year}년형 · `}{vehicle.trim}</p>

      {candidate.seatingVerificationRequired && <p className="financial-candidate-alert">희망 인원 탑승 가능 여부를 확인해 주세요.</p>}
      {candidate.lengthVerificationRequired && <p className="financial-candidate-alert">차량 크기 확인이 필요한 후보입니다.</p>}
      {vehicle.original_fuel && vehicle.original_fuel !== vehicle.fuel && <p className="financial-candidate-alert">전기 주행·충전 절감 효과는 유지비에 반영하지 않았습니다.</p>}
      <dl className="financial-recommendation-specs" aria-label={`${vehicle.model} 비용 정보`}>
        {[['차량 가격', vehicle.price], ['예상 월 유지비', cost.monthly_running_cost], ['유지비 지출 후 월 잔여금', cost.remaining_monthly]].map(([label, value]) => <div key={label}><dt>{label}</dt><dd>{candidateMoney(value)}</dd></div>)}
      </dl>
      <section className="financial-recommendation-reasons" aria-label={`${vehicle.model} 추천 사유`}>
        <h3>이 차를 추천하는 이유</h3>
        <ul>{highlights.map(reason => <li key={reason}><p>{reason}</p></li>)}</ul>
      </section>
      {cost.efficiency_estimated && <p className="financial-candidate-alert">예상 유지비에 참조 연비 또는 연료별 가정값이 포함돼 있습니다.</p>}
      {candidate.outsideTrainingRange && <p className="financial-candidate-alert">일부 입력이 학습 범위를 벗어납니다. 비용과 사양을 확인해 주세요.</p>}
      <details className="financial-recommendation-details">
        <summary>점수·차량 사양·계산 근거 보기</summary>
        <div className="financial-recommendation-details-content">
      <p>승차 정원 (운전자 포함): {vehicle.seats_label || (vehicle.seats ? `${vehicle.seats}명` : vehicle.seat_options?.length ? `${vehicle.seat_options.join(' / ')}인승 사양` : vehicle.assumed_seat_range ? '2~4인승 가정' : '미확인')} {vehicle.seats_source_url && <a href={vehicle.seats_source_url} target="_blank" rel="noreferrer">좌석 정보 출처</a>}</p>
      {vehicle.seats_note && <p className="financial-recommendation-reason-note">{vehicle.seats_note}</p>}
      {vehicle.assumed_seat_range && <p className="financial-recommendation-reason-note">실제 승차 정원 확인값이 없어 인원 점수에는 중립값을 적용했습니다. 사양을 확인하세요.</p>}
      {vehicle.seat_options?.length > 1 && <p className="financial-recommendation-reason-note">모델의 정원 선택지입니다. 표시 가격에 포함된 좌석 사양과 추가 옵션 비용은 견적에서 확인하세요.</p>}
      {candidate.seatingVerificationRequired && <p className="financial-recommendation-reason-note"><strong>좌석 확인 필요 · 인원 조건 충족 미확정</strong><br />재무 조건은 충족하지만 요청한 인원을 태울 수 있는 사양인지 확인해야 합니다.</p>}
      {candidate.lengthVerificationRequired && <p className="financial-recommendation-reason-note"><strong>전장 확인 필요 · 선호 크기 일치 미확정</strong><br />크기 자료가 없어 중립 점수를 적용했습니다.</p>}
      {vehicle.original_fuel && vehicle.original_fuel !== vehicle.fuel && <p className="financial-recommendation-reason-note">{cost.efficiency_estimated ? '가솔린 운행 비용 가정을 적용했습니다.' : '공개된 휘발유 연비로 유지비를 계산했습니다.'} 전기 주행·충전 절감 효과는 반영하지 않았습니다.</p>}
      {vehicle.default_configuration && <p className="financial-recommendation-reason-note">유지비 계산 기준: {vehicle.default_configuration}</p>}
      {candidate.integratedScore && <section className="candidate-score" aria-label="통합 점수">
        <h3>통합 점수 {candidate.integratedScore.total.toFixed(1)} / 100</h3>
        <p>사용자 중요도 가중 평균 · 확률이 아닙니다</p>
        {candidate.integratedScore.monthlyAffordability && <p>월 유지비 부담률 {(candidate.integratedScore.monthlyAffordability.runningCostRatio * 100).toFixed(1)}% · 부담 점수 {candidate.integratedScore.monthlyAffordability.score.toFixed(1)}점<br />생활비·상환·저축을 제외한 월 가용자금 기준입니다. 가성비 점수는 구매비와 월 유지비 부담을 절반씩 반영합니다.</p>}
        <dl>{candidate.integratedScore.components.map(item => <div key={item.key}><dt>{{cost: '가성비', space: '선호 크기', fuel: '선호 연료', seating: '선호 인원', purpose: '이용 목적', model: 'ML 참고', budget: '예산 적합도'}[item.key]} · 가중치 {item.weight}</dt><dd>{item.score.toFixed(1)}점</dd></div>)}</dl>
        <p>5년 예상 비용 {candidateMoney(candidate.integratedScore.estimatedOwnershipCost)} · 잔존가치·보조금·선택 옵션 미반영</p>
        {vehicle.length_mm && <p>전장 {(vehicle.length_mm / 1000).toFixed(2)}m · 실내 공간 평가는 아닙니다 {vehicle.space_source_url && <a href={vehicle.space_source_url} target="_blank" rel="noreferrer">제원 출처</a>}</p>}
        {!candidate.integratedScore.spaceEvaluated && <p>{candidate.lengthVerificationRequired ? '전장 미확인: 크기 점수 중립값 적용' : '선호 크기 미지정: 공간 평가 제외'}</p>}
      </section>}

          <h3>비용 계산 기준</h3>
          <p className="financial-recommendation-reason-note">구매 예산은 입력한 사용 가능 예금이며, 대출·할부를 가정하지 않습니다. 월 잔여금은 생활비·저축·기존 상환·차량 유지비를 반영합니다.</p>
          <ul className="financial-additional-reasons">{reasons.map(reason => <li key={reason}>{reason}</li>)}</ul>
          {cost.efficiency_estimated && <p className="financial-recommendation-reason-note">{vehicle.efficiency_reference_only ? '정확한 기본 사양의 연비가 미확정되어 공개 인증 사양의 참조 연비로 계산했습니다.' : '연비 미확인: 연료별 가정 범위로 비용을 계산했습니다.'}</p>}
      <p className="financial-recommendation-reason-note">가격 확인일 {vehicle.checked_on} · {vehicle.quality === 'legacy-price-snapshot' ? '기존 차량 가격 자료' : '자동 추출 자료'} · <a href={vehicle.source_url} target="_blank" rel="noreferrer">가격 출처 확인</a></p>
      {vehicle.source_note && <p className="financial-recommendation-reason-note">{vehicle.source_note}</p>}
        </div>
      </details>
    </div>
  </li>;
}
