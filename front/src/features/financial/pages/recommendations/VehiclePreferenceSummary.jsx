import { fuelLabels } from './candidatePresentation.js';

const bodyLabels = { SEDAN: '세단', SUV: 'SUV', HATCHBACK: '해치백', WAGON: '왜건',
  VAN: '미니밴·승합', MINIVAN: '미니밴·승합', BOX: '박스카', COUPE: '쿠페',
  CONVERTIBLE: '컨버터블', ROADSTER: '로드스터' };
const styles = ['크고 무거운 디자인', '균형 잡힌 디자인', '빠르고 날렵한 디자인'];
const contours = ['둥글고 부드럽게', '직선과 곡선의 조화', '각지고 또렷하게'];
const ordinalLabel = (value, labels) => Number.isFinite(value) ? labels[value < .25 ? 0 : value < .75 ? 1 : 2] : '정보 준비 중';

export default function VehiclePreferenceSummary({ vehicle, specifications, values, evidence }) {
  const fact = key => specifications?.[key]?.value;
  const sportiness = fact('exterior_sportiness') ?? values?.exterior_sportiness;
  const angularity = fact('exterior_angularity') ?? values?.exterior_angularity;
  const seconds = fact('seconds_0_100') ?? evidence?.acceleration_performance?.seconds_0_100;
  const length = fact('length_mm') ?? vehicle.length_mm;
  const seats = fact('seats') ?? vehicle.seats;
  const rows = [
    ['연료', { PHEV: '플러그인 하이브리드', MILD_HYBRID: '마일드 하이브리드' }[vehicle.original_fuel] ?? fuelLabels[vehicle.fuel ?? fact('fuel')] ?? '정보 준비 중'],
    ['차체 형태', bodyLabels[vehicle.body_type ?? fact('body_type')] ?? '정보 준비 중'],
    ['크기', Number.isFinite(length) ? `${length <= 4200 ? '작게' : length >= 4800 ? '크게' : '보통'} · 전장 ${length.toLocaleString('ko-KR')}mm` : '정보 준비 중'],
    ['탑승 인원', Number.isFinite(seats) ? `${seats}명` : typeof seats === 'string' && seats.startsWith('2+') ? '2+ 좌석' : vehicle.seats_label || '정보 준비 중'],
    ['외관 스타일', ordinalLabel(sportiness, styles)],
    ['차체 윤곽', ordinalLabel(angularity, contours)],
    ['가속 성능', Number.isFinite(seconds) ? `0–100km/h ${seconds}초` : '정보 준비 중'],
  ];
  return <section className="vehicle-preference-summary" aria-label={`${vehicle.model} 취향 비교 정보`}>
    <h4>차량 특징</h4>
    <dl>{rows.map(([label, value]) => <div key={label}><dt>{label}</dt><dd>{value}</dd></div>)}</dl>
  </section>;
}
