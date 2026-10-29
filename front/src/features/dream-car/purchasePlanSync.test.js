import test from 'node:test';
import assert from 'node:assert/strict';
import { mergeExecutionSettings, mergeSavingsInputs } from './purchasePlanSync.js';

test('실행 현황의 저축 수치만 동기화하고 차량·유지비 조건은 보존한다', () => {
  const saved = { vehicleId: 'car', inputs: { savings: 1000, monthlySaving: 100, targetMonths: 36, reserveMonths: 6, efficiency: 12, insurance: 120 } };
  const next = mergeSavingsInputs(saved, { savings: 2000, monthlySaving: 300, targetMonths: 24 });
  assert.deepEqual(next.inputs, { savings: 2000, monthlySaving: 300, targetMonths: 24, reserveMonths: 6, efficiency: 12, insurance: 120 });
  assert.equal(next.vehicleId, 'car');
  assert.equal(saved.inputs.monthlySaving, 100);
});
test('미완성·음수 입력과 잘못된 기간을 저장하지 않는다', () => {
  const saved = { inputs: { monthlySaving: 100, targetMonths: 36 } };
  for (const patch of [{ monthlySaving: '' }, { savings: -1 }, { targetMonths: 0 }, { targetMonths: 1.5 }, { monthlySaving: NaN }]) assert.throws(() => mergeSavingsInputs(saved, patch));
  assert.throws(() => mergeSavingsInputs(null, { monthlySaving: 100 }));
});

test('구매 계획 저장은 기존 실행 계획 수치를 갱신하고 실적과 정기 설정을 보존한다', () => {
  const active = { id: 'active', startMonth: '2026-08', startDate: '2026-08-01', initialSavings: 1000, monthlySaving: 100, targetMonths: 36, target: 5000, entries: {}, records: [{ id: 'record', date: '2026-09-10', amount: 80, memo: '저축' }], recurringRules: [{ id: 'rule' }], deletedRecurringIds: ['deleted'] };
  const purchase = { inputs: { savings: 2000, monthlySaving: 300, targetMonths: 12, reserveMonths: 6 } };
  const next = mergeExecutionSettings(active, purchase, 5500, '2026-10-29');
  assert.equal(next.id, 'active');
  assert.equal(next.initialSavings, 2000);
  assert.equal(next.monthlySaving, 300);
  assert.equal(next.targetMonths, 14);
  assert.equal(next.target, 5500);
  assert.deepEqual(next.records, active.records);
  assert.deepEqual(next.recurringRules, active.recurringRules);
  assert.deepEqual(next.deletedRecurringIds, active.deletedRecurringIds);
  assert.equal(next.purchaseInputs.reserveMonths, 6);
  const reverse = mergeSavingsInputs(purchase, { savings: next.initialSavings, monthlySaving: next.monthlySaving, targetMonths: next.targetMonths - 2 });
  assert.deepEqual(reverse.inputs, purchase.inputs);
});
