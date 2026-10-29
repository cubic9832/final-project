export default function VehicleTraitEvidence({ evidence }) {
  if (!evidence) return null;
  const acceleration = evidence.acceleration_performance;
  const estimated = acceleration?.kind === 'estimated-acceleration';
  const crossSite = acceleration?.kind === 'cross-site-acceleration';
  return <section aria-label="차량 특성 평가 근거">
    <h4>외관·윤곽·가속 정보</h4>
    <p>{evidence.exterior_sportiness?.basis ?? '외관 평가 미확인'}</p>
    <p>{estimated ? '추정' : crossSite ? '여러 출처 교차 확인' : '공식 공개'} 0–100km/h 가속: {acceleration?.seconds_0_100 ? `${acceleration.seconds_0_100}초` : '미확인'}</p>
    {estimated && <p>합성 데이터용 추정값입니다. 가정 범위 {acceleration.heuristic_range_seconds?.join('–')}초이며, 실측값이나 통계적 신뢰구간이 아닙니다.</p>}
    {acceleration?.limitation && <p>{acceleration.limitation}</p>}
    {acceleration?.source_url && <a href={acceleration.source_url} target="_blank" rel="noreferrer">가속 제원과 측정 조건 확인</a>}
    <p>대표 모델 사진을 바탕으로 한 주관적 평가이며 트림·연식에 따라 다를 수 있습니다.</p>
    {evidence.exterior_sportiness?.source_url && <a href={evidence.exterior_sportiness.source_url} target="_blank" rel="noreferrer">공식 이미지 출처 확인</a>}
  </section>;
}
