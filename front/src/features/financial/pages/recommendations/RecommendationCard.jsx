import { useId, useState } from 'react';
import { Car, ChevronDown } from 'lucide-react';
import theme from '../../../../styles/theme.js';
import { candidateImage, candidateMoney, fuelLabels } from './candidatePresentation.js';


export default function RecommendationCard({ candidate, rank, view, comparisonSelected, comparisonFull, onToggleComparison }) {
  const [failed, setFailed] = useState(false);
  const [expanded, setExpanded] = useState(false);
  const detailsId = useId();
  const { vehicle, cost, reasons } = candidate;
  const image = candidateImage(vehicle);

  return <li className="financial-recommendation-card">
    <div className="financial-recommendation-media"><span className="financial-recommendation-rank">{candidate.seatingVerificationRequired || candidate.lengthVerificationRequired ? '확인 후보' : '추천'} {rank}</span>
      {image && !failed ? <img src={image.src} alt={image.alt} style={image.style} loading="lazy" onError={() => setFailed(true)} /> : <div className="financial-recommendation-image-placeholder"><Car size={theme.iconSize.lg} aria-hidden="true" /><span>차량 이미지 준비 중</span></div>}
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
        <h3>다른 조건 · 확인할 점</h3>
        <ul>{[...view.mismatches, ...view.unknowns].sort((a, b) => (b.weight ?? 0) - (a.weight ?? 0)).slice(0, 2).map(item => <li key={item.key}>{item.text}</li>)}</ul>
        {!view.mismatches.length && !view.unknowns.length && view.evidence && <p>지정한 연료·크기·정원에서 확인된 불일치가 없어요. 이용 목적은 길이 기준의 참고 평가예요.</p>}
      </section>
      </div></div>
      <div className={`financial-recommendation-details${expanded ? ' is-expanded' : ''}`}>
        <button type="button" className="financial-recommendation-details-toggle" aria-expanded={expanded} aria-controls={detailsId} onClick={() => setExpanded(previous => !previous)}>
          <span>점수·차량 사양·계산 근거 보기</span><ChevronDown size={theme.iconSize.sm} aria-hidden="true" />
        </button>
        <div id={detailsId} className="financial-recommendation-details-panel" inert={!expanded} aria-hidden={!expanded}>
        <div className="financial-recommendation-details-content"><div className="financial-recommendation-details-inner">
      <div className="financial-recommendation-aligned-metadata"><div data-recommendation-measure="metadata">
      <p>승차 정원 (운전자 포함): {vehicle.seats ? `${vehicle.seats}인승` : vehicle.seats_label || (vehicle.seat_options?.length ? `${vehicle.seat_options.join(' / ')}인승 사양` : '미확인')}</p>
      </div></div>
      {candidate.integratedScore && <div className="financial-recommendation-aligned-score"><div data-recommendation-measure="score"><section className="candidate-score" aria-label="종합 적합도">
        <h3>종합 적합도 {candidate.integratedScore.total.toFixed(1)} / 100</h3>
        <p>재무 부담·선호 조건·추천 모델 평가를 합산한 비교 지표예요. 차량 품질이나 구매 만족도를 뜻하지 않아요.</p>
        <dl>{candidate.integratedScore.components.filter(item => ['fuel', 'space', 'seating'].includes(item.key)).map(item => <div key={item.key}><dt>{{space: '희망 크기 일치도', fuel: '선호 연료 일치도', seating: '희망 인원 충족도'}[item.key]}</dt><dd>{item.verified === false ? '사양 미확인' : `${item.score.toFixed(0)} / 100`}</dd></div>)}</dl>
        <p>{'구매비·유지비 절약을 가성비 중요도에 따라 반영해요. 가성비 중요도가 낮아도 높은 가격에 가점을 주지는 않아요.'}</p>
      </section></div></div>}

          <div className="financial-recommendation-aligned-conditions"><section data-recommendation-measure="conditions">
          <h3>조건별 전체 평가</h3>
          <ul className="financial-additional-reasons">{[...view.matches, ...view.mismatches, ...view.unknowns].map(item => <li key={item.key}>{item.text}</li>)}</ul>
          </section></div>
          <div className="financial-recommendation-aligned-cost"><section data-recommendation-measure="cost" className="candidate-cost-section">
          <h3>비용 계산 기준</h3>
          {candidate.integratedScore && <p className="financial-recommendation-reason-note">5년 예상 비용 {candidateMoney(candidate.integratedScore.estimatedOwnershipCost)} · 차량 가격과 60개월 유지비 합계이며 잔존가치·보조금·선택 옵션은 반영하지 않았어요.</p>}
          <p className="financial-recommendation-reason-note">입력한 예금은 차량 구매와 구매 후 부족한 월 자금에 함께 사용하는 총액입니다. 차량값을 먼저 빼고, 남은 예금으로 부족액을 충당합니다. 대출·할부는 가정하지 않습니다.</p>
          <ul className="financial-additional-reasons">{reasons.map(reason => <li key={reason}>{reason}</li>)}</ul>
          {cost.efficiency_estimated && <p className="financial-recommendation-reason-note">{vehicle.efficiency_reference_only ? '정확한 기본 사양의 연비가 미확정되어 공개 인증 사양의 참조 연비로 계산했습니다.' : '연비 미확인: 연료별 가정 범위로 비용을 계산했습니다.'}</p>}
          </section></div>
        </div></div>
        </div>
      </div>
    </div>
  </li>;
}
