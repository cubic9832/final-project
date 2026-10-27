import test from 'node:test';
import assert from 'node:assert/strict';
import { buildDiagnosisSummary } from './diagnosisSummary.js';

test('진단 요약은 만 원 입력을 원으로 바꾸고 가격 상한은 그대로 둔다', () => {
  const summary = buildDiagnosisSummary(
    { values: { income: 300, extraIncome: 20, monthlyExpenses: 150 }, assets: { deposit: 2000 }, loans: [{ payment: 30 }] },
    { modelVersion: 'candidate-v2', budgetPolicy: { financialUpper: 25_000_000 } },
  );
  assert.deepEqual(summary, {
    modelVersion: 'candidate-v2',
    monthlyIncome: 3_200_000,
    monthlyExpense: 1_500_000,
    monthlyAvailable: 1_400_000,
    purchaseFunds: 20_000_000,
    priceUpper: 25_000_000,
  });
});

test('가격 상한이 없으면 null', () => {
  const summary = buildDiagnosisSummary({ values: { income: 100, monthlyExpenses: 120 }, assets: {} }, { modelVersion: 'candidate-v2' });
  assert.equal(summary.priceUpper, null);
  assert.equal(summary.monthlyAvailable, -200_000);
  assert.equal(summary.purchaseFunds, 0);
});
