import test from 'node:test';
import assert from 'node:assert/strict';
import { calculateLoanPayment } from './calculateLoanPayment.js';

test('무이자와 원리금균등 대출의 월 상환액을 원 단위로 계산한다', () => {
  assert.equal(calculateLoanPayment('1200', '0', '12'), 100);
  assert.ok(Math.abs(calculateLoanPayment('1000', '6', '12') - 86.0664) < 0.0002);
  assert.ok(calculateLoanPayment('1000', '6', '24') < calculateLoanPayment('1000', '6', '12'));
});
test('미입력이나 잘못된 금리·기간으로 상환액을 만들지 않는다', () => {
  for (const args of [['', 0, 12], [1000, '', 12], [1000, 101, 12], [1000, 5, 0], [1000, 5, 1.5]]) assert.equal(calculateLoanPayment(...args), null);
});
