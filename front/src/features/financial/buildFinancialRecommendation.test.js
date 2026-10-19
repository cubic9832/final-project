import test from 'node:test';
import assert from 'node:assert/strict';
import { buildFinancialRecommendation } from './buildFinancialRecommendation.js';

function diagnosis() {
  return {
    values: { age: '30', career: '5', householdSize: '2', dependents: '0', gender: '남성', employment: '근로자',
      income: '350', annualGrossIncome: '5000', housing: '60', fixed: '20', living: '80', phone: '5', transport: '10',
      savings: '100', averageSavings: '70', loan: '25' },
    assets: { deposit: '2000', financialAssets: '500', housingDeposit: '3000', realEstate: '0', downPayment: '1000', emergency: '300' },
    loans: [{ balance: '1000' }, { balance: '500' }],
    vehicle: { segment: 'domestic-car', purpose: '주말 여가', annualDistance: '15,000km' },
  };
}

test('diagnosis reuses existing finances and uses annual gross income and actual savings independently', () => {
  const { request, errors } = buildFinancialRecommendation(diagnosis());
  assert.deepEqual(errors, []);
  assert.equal(request.profile['개인_연간세전소득_원'], 50000000);
  assert.equal(request.profile['개인_평균월저축액_원'], 700000);
  assert.equal(request.profile['개인_평균월기타생활소비_원'], 1150000);
  assert.equal(request.profile['기존대출잔액_보정전_원'], 15000000);
  assert.equal(request.profile['개인_현금성자산_원'], 20000000);
  assert.equal(request.profile['차량_이용목적'], '여가');
  assert.equal(request.profile['연간_주행거리_km'], 15000);
});

test('explicitly having no loans is valid but missing loan balances are not silently zeroed', () => {
  const state = diagnosis();
  state.loans = [];
  assert.equal(buildFinancialRecommendation(state).request.profile['기존대출잔액_보정전_원'], 0);
  state.loans = [{ balance: '' }];
  assert.equal(buildFinancialRecommendation(state).request, null);
});

test('old diagnosis missing required model data requests edits without inventing values', () => {
  const state = diagnosis();
  delete state.values.annualGrossIncome;
  delete state.assets.realEstate;
  const { request, errors } = buildFinancialRecommendation(state);
  assert.equal(request, null);
  assert.ok(errors.some(({ path }) => path === '/financial'));
  assert.ok(errors.some(({ path }) => path === '/financial/assets'));
});

test('unsupported vehicle conditions do not trigger inference with a made-up default', () => {
  const state = diagnosis();
  state.vehicle.purpose = '다른 목적';
  state.vehicle.annualDistance = '';
  assert.equal(buildFinancialRecommendation(state).request, null);
  assert.equal(buildFinancialRecommendation({}).request, null);
});
