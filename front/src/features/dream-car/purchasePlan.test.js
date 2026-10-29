import test from 'node:test';
import assert from 'node:assert/strict';
import { calculatePurchasePlan, defaultPlan } from './purchasePlan.js';

test('구매 목표에는 초기 비용과 유지비 예비자금을 포함하고 첫해 비용에는 중복하지 않는다', () => {
  const result = calculatePurchasePlan(3000, { ...defaultPlan, savings: 1000, monthlySaving: 100, registrationRate: 0, extras: 0, reserveMonths: 6, annualDistance: 0, insurance: 120, annualTax: 0, maintenance: 0, parking: 0 });
  assert.equal(result.target, 3060);
  assert.equal(result.months, 21);
  assert.equal(result.firstYear, 3120);
  assert.equal(result.requiredMonthly, 2060 / 36);
});
test('목표 달성 및 저축 중단 상태를 구분한다', () => {
  assert.equal(calculatePurchasePlan(3000, { ...defaultPlan, savings: 100000, monthlySaving: 0 }).months, 0);
  assert.equal(calculatePurchasePlan(3000, { ...defaultPlan, savings: 0, monthlySaving: 0 }).months, null);
});
test('유효하지 않은 금액·연비·목표기간으로 계산하지 않는다', () => {
  for (const patch of [{ efficiency: 0 }, { targetMonths: 0 }, { savings: -1 }, { monthlySaving: NaN }, { insurance: '' }]) assert.equal(calculatePurchasePlan(3000, { ...defaultPlan, ...patch }), null);
});
