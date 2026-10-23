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
  assert.equal(request.profile.minimum_buffer, 0);
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
  assert.equal('months' in request.profile, false);
  assert.equal(request.profile.charging_available, false);
  assert.equal(request.profile.existing_monthly_payment, 0);
});

test('importance and spatial requirements reach v2 without changing financial amounts', () => {
  const state = diagnosis();
  Object.assign(state.vehicle, { costImportance: '5', spaceImportance: '1', fuelImportance: '4', seatingImportance: '2', purposeImportance: '5', minimumSeats: '4', preferredSize: 'small' });
  const { request } = buildCandidateRecommendation(state);
  assert.equal(request.profile.cost_importance, 5);
  assert.equal(request.profile.space_importance, 1);
  assert.equal(request.profile.fuel_importance, 4);
  assert.equal(request.profile.seating_importance, 2);
  assert.equal(request.profile.purpose_importance, 5);
  assert.equal(request.profile.minimum_seats, 4);
  assert.equal(request.profile.preferred_size, 'small');
  assert.equal(request.profile.existing_monthly_payment, 200000);
  state.vehicle.spaceImportance = '1.5';
  assert.equal(buildCandidateRecommendation(state).request, null);
});

test('missing required values and impossible cash plans do not reach inference', () => {
  assert.equal(buildCandidateRecommendation({}).request, null);
  for (const change of [state => { state.values.income = ''; }, state => { state.assets.deposit = '-1'; },
    state => { state.vehicle.fuel = '가솔린 · 하이브리드'; },
    state => { state.loans[0].payment = ''; state.loans[0].balance = '100'; }]) {
    const state = diagnosis();
    change(state);
    assert.equal(buildCandidateRecommendation(state).request, null);
  }
});

test('recommendation requests exclude financing and ignore old saved purchase plans', () => {
  const state = diagnosis();
  delete state.assets.downPayment;
  const first = buildCandidateRecommendation(state);
  assert.deepEqual(first.errors, []);
  for (const field of ['down_payment', 'financing_mode', 'months', 'annual_rate']) assert.equal(field in first.request.profile, false);
  state.assets.downPayment = '999999';
  state.vehicle.installment = '일시불';
  assert.deepEqual(buildCandidateRecommendation(state), first);
});

test('charging is optional information and does not block electric recommendations', () => {
  const state = diagnosis();
  delete state.vehicle.charging;
  assert.deepEqual(buildCandidateRecommendation(state).errors, []);
  state.vehicle.fuel = '전기';
  assert.equal(buildCandidateRecommendation(state).request.profile.charging_available, false);
  for (const [charging, expected] of [
    ['집·직장에서 충전 가능', true], ['공용 충전소를 정기적으로 이용 가능', true],
    ['충전 환경이 불편하거나 확보되지 않음', false], ['잘 모르겠음', false],
    ['직장에서 충전 가능', true],
  ]) {
    state.vehicle.charging = charging;
    const result = buildCandidateRecommendation(state);
    assert.deepEqual(result.errors, []);
    assert.equal(result.request.profile.charging_available, expected);
  }
  state.vehicle.fuel = '가솔린';
  state.vehicle.charging = '공용 충전소를 정기적으로 이용 가능';
  assert.equal(buildCandidateRecommendation(state).request.profile.charging_available, false);
});

test('mileage input is unnecessary and old saved mileage cannot affect recommendations', () => {
  const state = diagnosis();
  delete state.vehicle.annualDistance;
  const first = buildCandidateRecommendation(state);
  assert.deepEqual(first.errors, []);
  assert.equal(first.request.profile.annual_distance, 15000);
  state.vehicle.annualDistance = '30,000km';
  assert.deepEqual(buildCandidateRecommendation(state), first);
});


test('removed reserve inputs cannot silently reduce the purchase or monthly budget', () => {
  const state = diagnosis();
  delete state.assets.emergency;
  delete state.vehicle.minimumBuffer;
  const first = buildCandidateRecommendation(state);
  assert.deepEqual(first.errors, []);
  assert.equal(first.request.profile.emergency_reserve, 0);
  assert.equal(first.request.profile.minimum_buffer, 0);
  assert.equal(first.request.profile.liquid_assets, 30000000);
  for (const obsolete of ['999999', '-1', 'invalid']) {
    state.assets.emergency = obsolete;
    state.vehicle.minimumBuffer = obsolete;
    assert.deepEqual(buildCandidateRecommendation(state), first);
  }
});
