import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import { resolveVehicleImage } from './resolveVehicleImage.js';
import { resolveVehicleDetails } from './resolveVehicleDetails.js';
import details from './newVehicleDetails.json' with { type: 'json' };

test('신규 차량은 모두 실제 이미지와 해당 트림의 상세 제원을 표시한다', () => {
  for (const vehicle of details.vehicles) {
    const image = resolveVehicleImage(vehicle);
    assert.ok(image, `${vehicle.brand} ${vehicle.model}`);
    assert.ok(fs.existsSync(new URL(`../../../public${image.src}`, import.meta.url)));
    assert.equal(resolveVehicleDetails(vehicle).trim, vehicle.trim);
    assert.ok(resolveVehicleDetails(vehicle).fields.length > 0);
  }
});

test('연식이나 트림이 바뀐 차량에는 이전 사양을 붙이지 않는다', () => {
  const vehicle = details.vehicles.find(item => item.trim === 'Carrera GTS');
  assert.equal(resolveVehicleDetails({ ...vehicle, year: '2020' }), undefined);
  assert.equal(resolveVehicleDetails({ ...vehicle, trim: 'GT3' }), undefined);
  assert.equal(resolveVehicleDetails({ ...vehicle, id: 'missing' }), undefined);
  const gt3 = details.vehicles.find(item => item.trim === 'GT3');
  assert.notDeepEqual(resolveVehicleDetails(vehicle).fields, resolveVehicleDetails(gt3).fields);
});

test('신규 모델의 관리자 사진과 사진 제거 설정도 우선한다', () => {
  const vehicle = details.vehicles[0];
  assert.equal(resolveVehicleImage({ ...vehicle, image_removed: true }), undefined);
  const upload = '/api/v1/vehicles/images/custom.webp';
  assert.equal(resolveVehicleImage({ ...vehicle, image_url: upload }).src, upload);
});
