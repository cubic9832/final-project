import test from 'node:test';
import assert from 'node:assert/strict';
import catalog from './planningVehicleCatalog.json' with { type: 'json' };
import { resolvePlanningEfficiency } from './resolvePlanningEfficiency.js';
import { getVehicleCostDefaults } from '../dream-car/vehicleCostDefaults.js';
import { calculatePurchasePlan, defaultPlan } from '../dream-car/purchasePlan.js';

test('전체 트림의 연비·전비 누락을 보완하고 연료비를 계산할 수 있다', () => {
  for (const vehicle of catalog) {
    const info = resolvePlanningEfficiency(vehicle);
    assert.ok(Number.isFinite(info.value) && info.value > 0, vehicle.id);
    assert.equal(info.unit, vehicle.fuel === 'ELECTRIC' ? 'km/kWh' : 'km/L');
    const result = calculatePurchasePlan(vehicle.price / 10000, { ...defaultPlan, ...getVehicleCostDefaults(vehicle).inputs });
    assert.ok(result && Number.isFinite(result.monthlyCosts.energy), vehicle.id);
    if (vehicle.efficiency > 0) assert.equal(info.value, vehicle.efficiency);
  }
});
test('별도 등록 국내 제원을 우선 연결하고 내연기관과 전기 단위를 구분한다', () => {
  const gas = resolvePlanningEfficiency(catalog.find(vehicle => vehicle.id === 'SPORT-5ea71e4b2e97abc7'));
  assert.equal(gas.value, 9.6);
  assert.equal(gas.estimated, false);
  const electric = resolvePlanningEfficiency(catalog.find(vehicle => vehicle.id === 'SPORT-4f6544766d9ec799'));
  assert.equal(electric.value, 4.7);
  assert.equal(electric.unit, 'km/kWh');
});
test('제원에도 없는 차량은 차체·연료·고성능 가정과 추정 여부를 남긴다', () => {
  const info = resolvePlanningEfficiency(catalog.find(vehicle => vehicle.id === 'SPORT-bf59f2a2a3aaea76'));
  assert.equal(info.estimated, true);
  assert.equal(info.value, 8);
  assert.match(info.basis, /공식 인증값 아님/);
});
