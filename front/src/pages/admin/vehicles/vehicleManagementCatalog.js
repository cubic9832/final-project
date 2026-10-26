import catalog from '../../../../../data/households/synthetic/curated-current-v2-20261026/catalog.json';
import { resolveVehicleImage } from '../../../features/vehicle/resolveVehicleImage.js';
import { emptyVehicle } from './vehicleManagementExamples.js';

const fuelLabels = { GASOLINE: '가솔린', HYBRID: '하이브리드', DIESEL: '경유', ELECTRIC: '전기', LPG: 'LPG' };
const domesticBrands = new Set(['현대', '기아', '제네시스', 'KG모빌리티', '르노코리아', '쉐보레']);

// 학습 시 고정한 전체 추천 카탈로그. 저장·공개 상태 변경은 UI 안에서만 적용한다.
export const catalogVehicles = catalog.map(vehicle => ({
  ...emptyVehicle,
  id: vehicle.id,
  brand: vehicle.brand,
  model: vehicle.model,
  year: vehicle.year || '',
  trim: vehicle.trim,
  fuel: fuelLabels[vehicle.fuel] || vehicle.fuel,
  body: '미확인',
  origin: domesticBrands.has(vehicle.brand) ? '국산' : '수입',
  price: String(vehicle.price / 10000),
  efficiency: String(vehicle.efficiency ?? ''),
  seats: String(vehicle.seats ?? ''),
  length: String(vehicle.length_mm ?? ''),
  drive: '미확인',
  status: '카탈로그 포함',
  updatedAt: vehicle.checked_on ? vehicle.checked_on.replaceAll('-', '.') : '확인일 미기록',
  image: resolveVehicleImage(vehicle)?.src || '',
  source: vehicle.quality || '',
  sourceUrl: vehicle.source_url || '',
  checkedOn: vehicle.checked_on || '',
  memo: [vehicle.default_configuration, vehicle.source_note].filter(Boolean).join('\n'),
}));
