import test from 'node:test';
import assert from 'node:assert/strict';
import registry from './newVehicleSales.json' with { type: 'json' };
import { resolveVehicleSales } from './resolveVehicleSales.js';

test('과거 추천 화면도 최신 가격·국내 정보를 표시하고 점수 입력은 바꾸지 않는다', () => {
  const record = registry.vehicles.find(row => row.identity.model === 'Temerario');
  const item = { vehicle: { ...record.identity, price: 473000000 }, rankingScore: .7,
    salesVerification: { price: { value: null } },
    specifications: { price_won: { value: '미확인' }, length_mm: { value: 4706 } } };
  const before = structuredClone(item);
  const displayed = resolveVehicleSales(item);
  assert.equal(displayed.verification.price.value, 473000000);
  assert.match(displayed.verification.domestic.value, /2026-05.*인도/);
  assert.equal(displayed.specifications.price_won.value, 473000000);
  assert.deepEqual(item, before);
  assert.deepEqual(displayed.specifications.length_mm, item.specifications.length_mm);
});

test('연식·트림이 다른 차량에는 이전 판매 자료를 붙이지 않는다', () => {
  const record = registry.vehicles.find(row => row.identity.model === 'Revuelto');
  const item = { vehicle: { ...record.identity, year: '2030' }, specifications: { price_won: { value: 123 } } };
  assert.equal(resolveVehicleSales(item).verification, undefined);
  assert.equal(resolveVehicleSales(item).specifications, item.specifications);
});

test('추정 가격은 공식가와 구분하고 국내 공개와 판매 개시를 혼동하지 않는다', () => {
  const record = registry.vehicles.find(row => row.identity.model === 'Amalfi Spider');
  const display = resolveVehicleSales({ vehicle: record.identity });
  assert.equal(display.verification.price.value, 433000000);
  assert.equal(display.verification.price.status, 'estimated-price');
  assert.match(display.verification.domestic.value, /국내 첫 공개/);
  assert.doesNotMatch(display.verification.domestic.value, /국내 판매 개시/);
});
