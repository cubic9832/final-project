import { resolveVehicleDetails, specificationLabel } from '../../../vehicle/resolveVehicleDetails.js';

const labels = {
  length_mm:'전장 (mm)',width_mm:'전폭 (mm)',height_mm:'전고 (mm)',wheelbase_mm:'휠베이스 (mm)',
  seats:'정원 (명)',curb_weight_kg:'공차중량 (kg)',displacement_cc:'배기량 (cc)',
  power_ps:'최고 출력 (PS)',torque_nm:'최대 토크 (Nm)',top_speed_kmh:'최고 속도 (km/h)',
  cargo_litres:'적재 용량 가정 (L)',ground_clearance_mm:'최저 지상고 (mm)',fuel:'연료',
  efficiency:'복합 효율',efficiency_unit:'효율 단위',price_won:'차량 가격 (원)',model_year:'연식',
  body_type:'차체 형태',transmission:'변속기',drive:'구동 방식',monthly_insurance_won:'월 보험료 (원)',
  monthly_tax_won:'월 자동차세 (원)',monthly_maintenance_won:'월 정비비 (원)',seconds_0_100:'0–100km/h (초)',
  exterior_sportiness:'외관 비례 (0–1)',exterior_angularity:'차체 윤곽 (0–1)',
  interior_minimalism:'실내 단순함 가정 (0–1)',ride_comfort:'승차감 가정 (0–1)',
};
const statuses = {'estimated':'추정','official-reference':'공식 자료 참고','catalog-reference':'기존 원장','visual-review':'사진 평가',
  'cross-site-reported':'3곳 이상 제원 교차 확인','cross-site-measured':'3곳 이상 실측 교차 확인',
  'unverified':'미확인','source-conflict':'출처·조건 차이','secondary-reference':'2차 사이트 참고',
  'reported-launch-price':'출시 당시 보도','official-layout':'공식 좌석 구조',
  'estimated-price':'추정 가격','secondary-reported-price':'국내 가격 보도'};

export default function VehicleSpecifications({ vehicle, specifications }) {
  const details = resolveVehicleDetails(vehicle);
  if (specifications) return <section className="candidate-vehicle-specifications" aria-label={`${vehicle.model} 차량 상세 제원`}>
    <h3>차량 상세 제원</h3>
    <p>항목별로 기존 자료·사진 평가·추정을 구분합니다. 추정 제원과 비용은 합성 데이터용이며 실제 성능·견적·구매 가능 여부를 보증하지 않습니다.</p>
    <details><summary>제원과 추정 근거 {Object.keys(specifications).length}개 보기</summary>
      <dl>{Object.entries(specifications).map(([key, item]) => <div key={key}>
        <dt>{labels[key] ?? key} · {statuses[item.status] ?? item.status}</dt>
        <dd>{String(item.value)}<p>{item.basis}</p>
          {item.observed_range && <p>확인 범위 {item.observed_range.join('–')} · 출처 {item.source_count}곳</p>}
          {item.status === 'cross-site-reported' && <p>여러 사이트의 공개 제원이 일치한 값이며, 독립 실측 3회를 뜻하지 않습니다.</p>}
          {item.sources?.length ? <ul>{item.sources.map(source => <li key={source.url}><a href={source.url} target="_blank" rel="noreferrer">{source.publisher} 출처</a></li>)}</ul>
            : item.source_url && <a href={item.source_url} target="_blank" rel="noreferrer">항목 출처</a>}
        </dd>
      </div>)}</dl>
      <p>실내·승차감 0.5는 자료가 없어 넣은 중립 가정이며 실제 평가가 아닙니다. 추정 비용은 구매 예산 계산에 사용하지 않습니다.</p>
    </details>
  </section>;
  if (!details) return null;
  return <section className="candidate-vehicle-specifications" aria-label={`${vehicle.model} 공개 상세 제원`}>
    <h3>차량 상세 제원</h3>
    <p>{details.trim === 'research-candidate' ? details.model : details.trim}{details.year && ` · ${details.year}년형`} · {details.checked_on} 확인</p>
    <p>모델군 대표 사진으로 색상과 세부 트림 장비는 다를 수 있어요.</p>
    <details>
      <summary>공개 제원 {details.fields.length}개 보기</summary>
      <dl>{details.fields.map((field, index) => <div key={`${field.label}-${index}`}>
        <dt>{specificationLabel(field.label)}</dt>
        <dd>{field.value}{field.status === 'source-conflict' && ' (공식 원문 간 차이 있음)'}</dd>
      </div>)}</dl>
      {details.notes.map(note => <p key={note}>{note}</p>)}
      <p>표시되지 않은 항목은 확인되지 않은 값입니다.</p>
      <a href={details.source_url} target="_blank" rel="noreferrer">공식 제원 출처 확인</a>
    </details>
  </section>;
}
