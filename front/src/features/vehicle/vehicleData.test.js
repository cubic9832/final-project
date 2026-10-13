import test from 'node:test';
import assert from 'node:assert/strict';
import { calculateCosts, defaultConditions, defaultFinance } from './vehicleData.js';

const vehicles = [{ price: 2555, efficiency: 21.1, type: '준중형 세단' }];

test('zero interest divides only the outstanding principal', () => {
  const result = calculateCosts(vehicles[0], defaultConditions, { ...defaultFinance, rate: 0 });
  assert.equal(result.installment, (vehicles[0].price - defaultConditions.downPayment) / 48);
  assert.equal(result.interest, 0);
});
test('fully paid vehicle has no installment or interest but retains running costs', () => {
  const result = calculateCosts(vehicles[0], { ...defaultConditions, downPayment: vehicles[0].price });
  assert.equal(result.installment, 0);
  assert.equal(result.interest, 0);
  assert.ok(result.total > 0);
});
test('higher down payment reduces monthly costs and total interest', () => {
  const before = calculateCosts(vehicles[0], defaultConditions);
  const after = calculateCosts(vehicles[0], { ...defaultConditions, downPayment: 800 });
  assert.ok(after.total < before.total);
  assert.ok(after.interest < before.interest);
  assert.ok(after.remaining > before.remaining);
});
test('longer term reduces installment while increasing interest', () => {
  const short = calculateCosts(vehicles[0], defaultConditions, { ...defaultFinance, months: 36 });
  const long = calculateCosts(vehicles[0], defaultConditions, { ...defaultFinance, months: 60 });
  assert.ok(long.installment < short.installment);
  assert.ok(long.interest > short.interest);
});
test('financial pressure can leave a negative remaining budget without invalid scores', () => {
  const result = calculateCosts(vehicles[0], { ...defaultConditions, income: 100, expenses: 150, limit: 1 });
  assert.equal(result.available, 0);
  assert.ok(result.remaining < 0);
  assert.ok(result.score >= 0 && result.score <= 99);
});
