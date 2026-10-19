import test from 'node:test';
import assert from 'node:assert/strict';
import { buildFinancialRecommendation } from './buildFinancialRecommendation.js';

function diagnosis() {
  return {
    values: { income: '350', extraIncome: '20', housing: '60', fixed: '20', living: '80',
      loan: '15', savings: '100', transport: '10', phone: '5' },
    assets: { deposit: '2000', downPayment: '500', emergency: '300' },
    loans: [{ balance: '1000', payment: '15', rate: '5', months: '24' }],
    vehicle: { purpose: '주말 여가', annualDistance: '15,000km', installment: '48개월' },
  };
}

test('original diagnosis inputs suffice without demographics, gross income or new assets', () => {
  const { request, errors } = buildFinancialRecommendation(diagnosis());
  assert.deepEqual(errors, []);
  assert.equal(request.segment, 'all-cars');
  assert.equal(request.profile['개인_평균월실수령소득_원'], 3700000);
  assert.equal(request.profile['개인_평균월기타생활소비_원'], 1150000);
  assert.equal(request.profile['기존대출잔액_보정전_원'], 10000000);
  assert.equal(request.profile['기존월상환액_보정전_원'], 150000);
  assert.equal(request.profile['연간_주행거리_km'], 15000);
  assert.equal(request.profile['차량_이용목적'], '여가');
  assert.ok(!('개인_연간세전소득_원' in request.profile));
  assert.ok(!('개인_평균월저축액_원' in request.profile));
});

test('untouched default loan row follows original UI zero calculation, incomplete entered debt is rejected', () => {
  const state = diagnosis();
  state.loans = [{ balance: '', payment: '', rate: '', months: '' }];
  assert.equal(buildFinancialRecommendation(state).request.profile['기존대출잔액_보정전_원'], 0);
  state.loans = [{ balance: '', payment: '10', rate: '5', months: '' }];
  assert.equal(buildFinancialRecommendation(state).request, null);
  assert.ok(buildFinancialRecommendation(state).errors.includes('대출 잔액'));
});

test('invalid or missing diagnosis is not replaced with invented profile defaults', () => {
  assert.equal(buildFinancialRecommendation({}).request, null);
  const state = diagnosis();
  state.values.income = '-1';
  state.vehicle.annualDistance = '';
  assert.equal(buildFinancialRecommendation(state).request, null);
});

test('loan payments and target savings are not counted again as living expenses', () => {
  const state = diagnosis();
  const previous = buildFinancialRecommendation(state).request.profile['개인_평균월기타생활소비_원'];
  state.values.loan = '150';
  state.values.savings = '200';
  assert.equal(buildFinancialRecommendation(state).request.profile['개인_평균월기타생활소비_원'], previous);
});
