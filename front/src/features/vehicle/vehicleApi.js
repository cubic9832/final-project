import client from '../../api/client.js';

const classLabels = { MINI: '경차', COMPACT_SEDAN: '준중형 세단', MIDSIZE_SEDAN: '중형 세단' };

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
    trim: [row.trimName, row.modelYear && `${row.modelYear}년형`].filter(Boolean).join(' · '),
    price: Number(row.price) / 10000,
    efficiency: Number(row.efficiencyValue),
    color: row.brand === '현대' ? '#7199b5' : '#7eafa0',
    imageUrl: row.imageUrl,
    sourceName: row.sourceName,
    sourceUrl: row.sourceUrl,
    isExample: row.isExample,
  };
}

export async function getVehicles(signal) {
  const response = await client.get('/vehicles', { signal });
  return response.data.data.map(toVehicle).filter(Boolean);
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
