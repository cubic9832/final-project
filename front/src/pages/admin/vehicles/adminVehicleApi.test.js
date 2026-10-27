import test from 'node:test';
import assert from 'node:assert/strict';
import client from '../../../shared/api/client.js';
import { saveAdminVehicle, listAdminVehicles } from './adminVehicleApi.js';

test('관리자 편집 금액을 원으로 저장하고 서버 ID·수정 버전·공개 상태를 다음 조회에서 유지한다', async () => {
  const original = client.defaults.adapter;
  let stored;
  client.defaults.adapter = async config => {
    if (config.method === 'put') {
      const body = JSON.parse(config.data);
      assert.equal(body.priceWon, 28925500);
      assert.equal(body.version, 7);
      assert.equal(body.bodyType, 'SUV');
      assert.equal(body.fuel, 'ELECTRIC');
      assert.equal(body.status, 'PUBLISHED');
      assert.equal(body.seats, 5);
      stored = { id: 'managed-existing', version: 8, status: body.status, updatedAt: '2026-10-26T12:00:00',
        vehicle: { brand: body.brand, model: body.model, trim: body.trim, year: body.year, price: body.priceWon,
          fuel: body.fuel, body_type: body.bodyType, seats: body.seats, length_mm: body.lengthMm, efficiency: body.efficiency,
          origin: body.origin, drive: body.drive, image_url: body.imageUrl, source_name: body.sourceName, source_url: body.sourceUrl, checked_on: body.checkedOn, memo: body.memo } };
    }
    return { data: { success: true, data: config.method === 'get' ? [stored] : stored }, status: 200, statusText: 'OK', headers: {}, config };
  };
  try {
    const saved = await saveAdminVehicle({ id: 'managed-existing', version: 7, brand: '현대', model: '코나 Electric', trim: '기본', year: '2026',
      price: '2892.55', fuel: '전기', body: 'SUV', seats: '5', length: '4355', efficiency: '5.5', origin: '국산', drive: '2WD', status: '공개',
      image: '', source: '공식 자료', sourceUrl: 'https://example.com/official', checkedOn: '2026-10-26', memo: '' });
    assert.equal(saved.id, 'managed-existing'); assert.equal(saved.version, 8); assert.equal(saved.price, '2892.55');
    const refreshed = await listAdminVehicles();
    assert.deepEqual(refreshed[0], saved);
  } finally { client.defaults.adapter = original; }
});
