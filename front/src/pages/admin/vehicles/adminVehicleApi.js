import client from '../../../shared/api/client.js';
import { resolveVehicleImage } from '../../../features/vehicle/resolveVehicleImage.js';
import { bodyTypeOptions } from '../../../features/financial/vehiclePreferences.js';

const fuels = { GASOLINE: '가솔린', HYBRID: '하이브리드', DIESEL: '경유', ELECTRIC: '전기', LPG: 'LPG' };
const statuses = { DRAFT: '작성 중', REVIEW: '검수 대기', PUBLISHED: '공개', DISCONTINUED: '판매 종료' };
const reverse = (map, value) => Object.keys(map).find(key => map[key] === value);
export function toAdminVehicle(row) {
  const v = row.vehicle;
  return { id: row.id, version: row.version, brand: v.brand, model: v.model, year: v.year || '', trim: v.trim,
    fuel: fuels[v.fuel], body: bodyTypeOptions.find(item => item.value === v.body_type)?.label || '형태 미확인',
    origin: v.origin, price: String(v.price / 10000), efficiency: String(v.efficiency ?? ''), seats: String(v.seats ?? ''),
    length: String(v.length_mm ?? ''), drive: v.drive || '미확인', status: statuses[row.status],
    image: v.image_url || resolveVehicleImage(v)?.src || '', source: v.source_name || '', sourceUrl: v.source_url || '',
    checkedOn: /^\d{4}-\d{2}-\d{2}$/.test(v.checked_on) ? v.checked_on : '', memo: v.memo || '',
    updatedAt: row.updatedAt?.replace('T', ' ').slice(0, 19) || '' };
}
export const listAdminVehicles = async signal => (await client.get('/admin/vehicles', { signal })).data.data.map(toAdminVehicle);
const uploadedFiles = new WeakMap();
async function imageUrl(vehicle) {
  if (!vehicle.imageFile) return vehicle.image || '';
  if (!uploadedFiles.has(vehicle.imageFile)) {
    const data = new FormData(); data.append('file', vehicle.imageFile);
    const upload = client.post('/admin/vehicle-images', data).then(result => result.data.data.url);
    uploadedFiles.set(vehicle.imageFile, upload);
    upload.catch(() => uploadedFiles.delete(vehicle.imageFile));
  }
  return uploadedFiles.get(vehicle.imageFile);
}
export async function saveAdminVehicle(vehicle) {
  const nullableNumber = value => value === '' ? null : Number(value);
  const payload = { brand: vehicle.brand, model: vehicle.model, year: vehicle.year, trim: vehicle.trim,
    fuel: reverse(fuels, vehicle.fuel), bodyType: bodyTypeOptions.find(item => item.label === vehicle.body)?.value || null,
    origin: vehicle.origin, priceWon: Math.round(Number(vehicle.price) * 10000), efficiency: nullableNumber(vehicle.efficiency),
    seats: nullableNumber(vehicle.seats), lengthMm: nullableNumber(vehicle.length), drive: vehicle.drive,
    status: reverse(statuses, vehicle.status), imageUrl: await imageUrl(vehicle), sourceName: vehicle.source,
    sourceUrl: vehicle.sourceUrl, checkedOn: vehicle.checkedOn || null, memo: vehicle.memo, version: vehicle.version || null };
  const response = vehicle.id ? await client.put(`/admin/vehicles/${encodeURIComponent(vehicle.id)}`, payload) : await client.post('/admin/vehicles', payload);
  return toAdminVehicle(response.data.data);
}
export function adminVehicleError(error) {
  if (error.response?.status === 403) return '관리자 권한이 필요합니다.';
  if (error.response?.status === 401) return '관리자 계정으로 로그인해 주세요.';
  return error.response?.data?.detail || error.response?.data?.error?.message || '차량 정보를 처리하지 못했어요. 다시 시도해 주세요.';
}
