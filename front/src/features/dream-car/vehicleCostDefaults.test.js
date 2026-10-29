import test from 'node:test';
import assert from 'node:assert/strict';
import { annualVehicleTax, getVehicleCostDefaults, updatePlanInput } from './vehicleCostDefaults.js';
import { calculatePurchasePlan, defaultPlan } from './purchasePlan.js';
import catalog from '../../../../data/households/synthetic/sports-official-v1-20261028/catalog.json' with { type: 'json' };

test('자동차세는 구간별 전체 배기량 세율과 지방교육세를 적용한다', () => {
  assert.equal(annualVehicleTax(1000), 10.4);
  assert.equal(annualVehicleTax(1600), 29.12);
  assert.equal(annualVehicleTax(1601), 41.626);
  assert.equal(annualVehicleTax(null, true), 13);
  assert.equal(annualVehicleTax(null), null);
  assert.equal(annualVehicleTax(2200, false, 11), null);
});
test('전기차 선택 시 전비·충전 단가·보험료·세금을 함께 변경한다', () => {
  const result = getVehicleCostDefaults({ id: 'unknown', price: 50000000, fuel: 'ELECTRIC', efficiency: 5.2, seats: 5 });
  assert.deepEqual(result.inputs, { efficiency: 5.2, energyPrice: 350, insurance: 110, annualTax: 13, maintenance: 75 });
});
test('배기량 미확인은 가격 기반 예산을 채우고 연비 미확인은 유지한다', () => {
  const result = getVehicleCostDefaults({ id: 'unknown', price: 30000000, fuel: 'DIESEL', efficiency: null });
  assert.equal(result.inputs.annualTax, 30);
  assert.equal(result.inputs.maintenance, 45);
  assert.match(result.notes.annualTax, /실제 세액 아님/);
  assert.equal(result.inputs.efficiency, '');
  assert.equal(result.inputs.energyPrice, 1550);
});

test('낮은 차량가에는 최소 적립금을, 고가 차량에는 비례 비용을 적용한다', () => {
  const vehicle = { id: 'unknown', fuel: 'GASOLINE', efficiency: 10 };
  const low = getVehicleCostDefaults({ ...vehicle, price: 10000000 }).inputs;
  assert.equal(low.annualTax, 20);
  assert.equal(low.maintenance, 30);
  const high = getVehicleCostDefaults({ ...vehicle, price: 200000000 }).inputs;
  assert.equal(high.annualTax, 200);
  assert.equal(high.maintenance, 300);
});

test('주행거리 변경은 연료비·자동 정비비·유지비 예비자금을 함께 갱신한다', () => {
  const vehicle = { id: 'unknown', price: 50000000, fuel: 'GASOLINE', efficiency: 10 };
  const inputs = { ...defaultPlan, ...getVehicleCostDefaults(vehicle).inputs };
  const next = updatePlanInput(vehicle, inputs, 'annualDistance', 24000);
  assert.equal(inputs.maintenance, 75);
  assert.equal(next.maintenance, 120);
  const before = calculatePurchasePlan(5000, inputs);
  const after = calculatePurchasePlan(5000, next);
  assert.equal(after.monthlyCosts.energy, before.monthlyCosts.energy * 2);
  assert.ok(after.monthlyTotal > before.monthlyTotal);
  assert.ok(after.target > before.target);
  assert.equal(next.annualTax, inputs.annualTax);
  assert.equal(next.insurance, inputs.insurance);
});

test('수동 정비비는 주행거리 변경 시 유지하며 0km에도 고정 적립금은 남는다', () => {
  const vehicle = { id: 'unknown', price: 50000000, fuel: 'ELECTRIC', efficiency: 5 };
  assert.equal(getVehicleCostDefaults(vehicle, 0).inputs.maintenance, 30);
  const inputs = { ...defaultPlan, ...getVehicleCostDefaults(vehicle).inputs, maintenance: 200 };
  assert.equal(updatePlanInput(vehicle, inputs, 'annualDistance', 24000).maintenance, 200);
  assert.equal(updatePlanInput(vehicle, inputs, 'annualDistance', '').annualDistance, '');
});

test('같은 모델의 편의사양 트림은 세금이 같고 가격 기반 보험·정비 예산은 달라진다', () => {
  const lower = getVehicleCostDefaults(catalog.find(car => car.id === 'legacy-C0095')).inputs;
  const upper = getVehicleCostDefaults(catalog.find(car => car.id === 'legacy-C0096')).inputs;
  assert.equal(lower.annualTax, upper.annualTax);
  assert.ok(upper.insurance > lower.insurance);
  assert.ok(upper.maintenance > lower.maintenance);
});

test('같은 K8이라도 2.5와 3.5 엔진 사양은 세금과 연료비가 달라진다', () => {
  const smaller = catalog.find(car => car.id === 'V-049d84937c97ad57');
  const larger = catalog.find(car => car.id === 'legacy-C0095');
  const first = getVehicleCostDefaults(smaller).inputs;
  const second = getVehicleCostDefaults(larger).inputs;
  assert.ok(second.annualTax > first.annualTax);
  const firstPlan = calculatePurchasePlan(smaller.price / 10000, { ...defaultPlan, ...first });
  const secondPlan = calculatePurchasePlan(larger.price / 10000, { ...defaultPlan, ...second });
  assert.notEqual(secondPlan.monthlyCosts.energy, firstPlan.monthlyCosts.energy);
});
