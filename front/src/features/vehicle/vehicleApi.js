import client from '../../shared/api/client.js';
import { resolveVehicleImage } from './resolveVehicleImage.js';

const classLabels = {
  MINI: '경차',
  SUBCOMPACT_SUV: '소형 SUV',
  COMPACT_SEDAN: '준중형 세단',
  COMPACT_SUV: '준중형 SUV',
  MIDSIZE_SEDAN: '중형 세단',
  MIDSIZE_SUV: '중형 SUV',
  LARGE_SUV: '대형 SUV',
  FULLSIZE_SEDAN: '대형 세단',
  MPV: '승합',
};

// DB 금액은 원, 화면의 비용 계산은 만 원 단위로 통일한다.
export function toVehicle(row) {
  if (!['GASOLINE', 'HYBRID'].includes(row.fuelCode) || row.efficiencyUnit !== 'km/L'
      || !(Number(row.price) > 0) || !(Number(row.efficiencyValue) > 0)) return null;
  return {
    id: String(row.id),
    name: `${row.brand} ${row.name}`,
    brand: row.brand,
    type: classLabels[row.classCode] ?? row.classCode ?? '기타',
    condition: row.conditionCode === 'NEW' ? '신차' : row.conditionCode === 'USED' ? '중고차' : '미확인',
    trim: [row.trimName, row.powertrain, row.modelYear && `${row.modelYear}년형`].filter(Boolean).join(' · '),
    price: Number(row.price) / 10000,
    priceBeforeIncentive: row.priceBeforeIncentive == null ? null : Number(row.priceBeforeIncentive) / 10000,
    efficiency: Number(row.efficiencyValue),
    cityEfficiency: row.cityEfficiency == null ? null : Number(row.cityEfficiency),
    highwayEfficiency: row.highwayEfficiency == null ? null : Number(row.highwayEfficiency),
    displacementCc: row.displacementCc == null ? null : Number(row.displacementCc),
    color: row.brand === '현대' ? '#7199b5' : '#7eafa0',
    imageUrl: (row.isExample || !row.imageUrl)
      ? resolveVehicleImage(row)?.src ?? row.imageUrl
      : row.imageUrl,
    sourceName: row.sourceName,
    sourceUrl: row.sourceUrl,
    isExample: row.isExample,
  };
}

export async function getVehicles(signal) {
  const response = await client.get('/vehicles', { signal });
  return response.data.data.map(toVehicle).filter(Boolean);
}

// Elasticsearch 가 관련도 순으로 찾은 차량 id. 화면 목록과 맞추기 위해 문자열로 돌려준다.
export async function searchVehicleIds(keyword, signal) {
  const response = await client.get('/vehicles', { params: { q: keyword }, signal });
  return response.data.data.map((row) => String(row.id));
}

export function selectPresetVehicles(ids, vehicles) {
  const models = { avante: '아반떼', ray: '레이', morning: '모닝', k5: 'K5' };
  const selected = [];
  for (const id of ids) {
    const vehicle = vehicles.find((item) => (item.id === id || item.name.includes(models[id] ?? id)) && !selected.includes(item.id));
    if (vehicle) selected.push(vehicle.id);
  }
  for (const vehicle of vehicles) {
    if (selected.length >= 3) break;
    if (!selected.includes(vehicle.id)) selected.push(vehicle.id);
  }
  return selected;
}
