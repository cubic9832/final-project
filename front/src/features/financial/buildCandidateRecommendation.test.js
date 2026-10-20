import test from 'node:test';
import assert from 'node:assert/strict';
import { buildCandidateRecommendation } from './buildCandidateRecommendation.js';
import { calculateFinancialSummary } from './calculateFinancialSummary.js';

function diagnosis() {
  return { values: { income: '600', housing: '50', fixed: '20', living: '80', savings: '100', loan: '999' },
    assets: { deposit: '3000', downPayment: '2000', emergency: '500' },
    loans: [{ balance: '', payment: '20' }],
    vehicle: { purpose: '출퇴근', annualDistance: '15,000km', installment: '48개월', fuel: '하이브리드', charging: '충전 불가', minimumBuffer: '30' } };
}

test('v2 request converts units and shares detailed debt totals with the displayed budget', () => {
  const state = diagnosis();
  const { request, errors } = buildCandidateRecommendation(state);
  assert.deepEqual(errors, []);
  assert.equal(request.profile.monthly_income, 6000000);
  assert.equal(request.profile.monthly_expenses, 1500000);
  assert.equal(request.profile.existing_monthly_payment, 200000);
  assert.equal(request.profile.minimum_buffer, 300000);
  assert.equal(request.profile.preferred_fuel, 'HYBRID');
  const totals = calculateFinancialSummary(state.values, state.loans);
  assert.equal(totals.available * 10000, request.profile.monthly_income - request.profile.monthly_expenses - request.profile.existing_monthly_payment - request.profile.monthly_savings);
  state.loans[0].payment = '50';
  assert.equal(buildCandidateRecommendation(state).request.profile.existing_monthly_payment, 500000);
});

test('no fuel preference, no debt and outright payment remain explicit values', () => {
  const state = diagnosis();
  state.loans = [];
  Object.assign(state.vehicle, { fuel: '상관없음', installment: '일시불', charging: '집에서 충전 가능' });
  const { request } = buildCandidateRecommendation(state);
  assert.equal(request.profile.preferred_fuel, null);
  assert.equal(request.profile.months, 0);
  assert.equal(request.profile.charging_available, true);
  assert.equal(request.profile.existing_monthly_payment, 0);
});

test('missing required values and impossible cash plans do not reach inference', () => {
  assert.equal(buildCandidateRecommendation({}).request, null);
  for (const change of [state => { state.values.income = ''; }, state => { state.assets.downPayment = '3000'; },
    state => { state.vehicle.minimumBuffer = '-1'; }, state => { state.vehicle.fuel = '가솔린 · 하이브리드'; },
    state => { state.loans[0].payment = ''; state.loans[0].balance = '100'; }]) {
    const state = diagnosis();
    change(state);
    assert.equal(buildCandidateRecommendation(state).request, null);
  }
});
