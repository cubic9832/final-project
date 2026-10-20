import { useState } from 'react';
import { Car } from 'lucide-react';
import theme from '../../../../styles/theme.js';
import { candidateImage, candidateMoney, fuelLabels } from './candidatePresentation.js';

export default function RecommendationCard({ candidate, rank }) {
  const [failed, setFailed] = useState(false);
  const { vehicle, cost, reasons } = candidate;
  const image = candidateImage(vehicle);
  return <li className="financial-recommendation-card">
    <div className="financial-recommendation-media"><span className="financial-recommendation-rank">추천 {rank}</span>
      {image && !failed ? <img src={image.src} alt={image.alt} loading="lazy" onError={() => setFailed(true)} /> : <div className="financial-recommendation-image-placeholder"><Car size={theme.iconSize.lg} aria-hidden="true" /><span>차량 이미지 준비 중</span></div>}
    </div>
    <div className="financial-recommendation-card-body">
      <p className="financial-recommendation-category">{vehicle.brand} · {fuelLabels[vehicle.fuel] || vehicle.fuel}</p>
      <h2>{vehicle.model}</h2><p>{vehicle.year && `${vehicle.year}년형 · `}{vehicle.trim}</p>
      <dl className="financial-recommendation-specs" aria-label={`${vehicle.model} 비용 정보`}>
        {[['차량 가격', vehicle.price], ['취득부대비 포함 가정', cost.total_purchase_cost], ['월 할부금', cost.monthly_payment], ['월 운행·고정 유지비', cost.monthly_running_cost], ['월 차량 비용 합계', cost.monthly_total], ['비용 상승 시 월 비용', cost.stress_monthly_total], ['비용 상승 후 잔여 자금', cost.stress_remaining_monthly]].map(([label, value]) => <div key={label}><dt>{label}</dt><dd>{candidateMoney(value)}</dd></div>)}
      </dl>
      <section className="financial-recommendation-reasons" aria-label={`${vehicle.model} 추천 사유`}><h3>추천 사유</h3><ul>{reasons.map(reason => <li key={reason}><p>{reason}</p></li>)}</ul>
        {cost.efficiency_estimated && <p className="financial-recommendation-reason-note">연비 미확인: 연료별 가정 범위로 비용을 계산했습니다.</p>}
        {candidate.outsideTrainingRange && <p className="financial-recommendation-reason-note">일부 조건이 학습 범위 밖입니다. 비용과 차량 사양을 추가 확인하세요.</p>}
      </section>
      <p className="financial-recommendation-reason-note">가격 확인일 {vehicle.checked_on} · 자동 추출 자료 · <a href={vehicle.source_url} target="_blank" rel="noreferrer">가격 출처 확인</a></p>
    </div>
  </li>;
}
