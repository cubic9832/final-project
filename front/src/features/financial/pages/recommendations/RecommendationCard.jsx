import { useState } from 'react';
import { Car } from 'lucide-react';
import theme from '../../../../styles/theme.js';
import { candidateImage, candidateMoney, fuelLabels } from './candidatePresentation.js';
import VehiclePreferenceSummary from './VehiclePreferenceSummary.jsx';


export default function RecommendationCard({ candidate, rank, view, comparisonSelected, comparisonFull, onToggleComparison }) {
  const [failedSrc, setFailedSrc] = useState(null);
  const { vehicle, cost } = candidate;
  const image = candidateImage(vehicle);

  return <li className="financial-recommendation-card">
    <div className="financial-recommendation-media"><span className="financial-recommendation-rank">{candidate.seatingVerificationRequired || candidate.lengthVerificationRequired ? '확인 후보' : '추천'} {rank}</span>
      {image && failedSrc !== image.src ? <img key={image.src} src={image.src} alt={image.alt} style={image.style} loading="lazy" onError={() => setFailedSrc(image.src)} /> : <div className="financial-recommendation-image-placeholder"><Car size={theme.iconSize.lg} aria-hidden="true" /><span>차량 이미지 준비 중</span></div>}
    </div>
    <div className="financial-recommendation-card-body">
      <div className="financial-recommendation-aligned-summary"><div data-recommendation-measure="summary">
      <p className="financial-recommendation-category">{vehicle.brand} · {{MILD_HYBRID: '마일드 하이브리드', PHEV: '플러그인 하이브리드'}[vehicle.original_fuel] || fuelLabels[vehicle.fuel] || vehicle.fuel}</p>
      {onToggleComparison && <label className="candidate-comparison-select"><input type="checkbox" aria-label={`${vehicle.model} 비교 선택`} checked={comparisonSelected} disabled={comparisonFull && !comparisonSelected} onChange={() => onToggleComparison(vehicle.id)} />{comparisonSelected ? '비교 목록에 담았어요' : '비교 목록에 담기'}</label>}
      <h2>{vehicle.model}</h2><p>{vehicle.year && `${vehicle.year}년형 · `}{vehicle.trim}</p>

      {candidate.seatingVerificationRequired && <p className="financial-candidate-alert">희망 인원 탑승 가능 여부를 확인해 주세요.</p>}
      {candidate.lengthVerificationRequired && <p className="financial-candidate-alert">차량 크기 확인이 필요한 후보입니다.</p>}
      {view?.financial?.fundingSource === 'assets' && <p className="financial-candidate-alert">예금 사용형 추천 · 생활 적자와 차량 유지비를 합해 예금에서 매월 {candidateMoney(view.financial.monthlyAssetDrawdown)}을 사용해요. 구매 후 예금으로 약 {view.financial.assetRunwayMonths}개월 유지 가능하며, 최소 {view.financial.requiredAssetCoverageMonths}개월 충당 기준을 적용했어요.</p>}
      <dl className="financial-recommendation-specs" aria-label={`${vehicle.model} 비용 정보`}>
        {[['차량 가격', vehicle.price], ['예상 월 유지비', cost.monthly_running_cost], ['구매 후 남는 예금', view.financial?.cashAfterPurchase], ['유지비 지출 후 월 잔여금', cost.remaining_monthly]].map(([label, value]) => <div key={label}><dt>{label}</dt><dd>{candidateMoney(value)}</dd></div>)}
      </dl>
      <section className="financial-recommendation-reasons" aria-label={`${vehicle.model} 맞는 조건`}>
        <h3>맞는 조건</h3>
        <ul>{view.matches.slice(0, 2).map(item => <li key={item.key}><p>{item.text}</p></li>)}</ul>
        {!view.matches.length && <p className="candidate-condition-note">{view.evidence ? '지정한 연료·크기·정원 중 일치가 확인된 선호가 없어요. 구매 가능 여부와 비용도 함께 비교해 주세요.' : '조건별 평가 근거를 불러오지 못했어요. 조건을 다시 적용해 추천받아 주세요.'}</p>}
      </section>
      <section className="candidate-tradeoffs" aria-label={`${vehicle.model} 다른 조건`}>
        <h3>다른 조건 · 확인할 점</h3>{candidate.preferenceCompromise && <p>일부 선호 조건을 조정한 절충 후보예요.</p>}
        <ul>{[...view.mismatches, ...view.unknowns].sort((a, b) => (b.weight ?? 0) - (a.weight ?? 0)).slice(0, 2).map(item => <li key={item.key}>{item.text}</li>)}</ul>
        {!view.mismatches.length && !view.unknowns.length && view.evidence && <p>지정한 연료·크기·정원에서 확인된 불일치가 없어요.</p>}
      </section>
      </div></div>
      <VehiclePreferenceSummary vehicle={vehicle} specifications={candidate.lifestyleEvidence?.specifications} values={candidate.lifestyleEvidence?.values} evidence={candidate.lifestyleEvidence?.evidence} />
    </div>
  </li>;
}
