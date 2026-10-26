import test from 'node:test';
import assert from 'node:assert/strict';
import { formatFinancialMoney } from './formatFinancialMoney.js';

test('백만 원·만 원에서 환산한 금액은 억 경계에서 같은 단위로 표시한다', () => {
  assert.equal(formatFinancialMoney(100 * 1000000), '1억 원');
  assert.equal(formatFinancialMoney(10000 * 10000), '1억 원');
  assert.equal(formatFinancialMoney(125000000), '1억 2,500만 원');
  assert.equal(formatFinancialMoney(99990000), '9,999만 원');
  assert.equal(formatFinancialMoney(-100000000), '-1억 원');
});
