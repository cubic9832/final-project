import test from 'node:test';
import assert from 'node:assert/strict';
import { buildCandidateRecommendation } from './buildCandidateRecommendation.js';

const input = () => ({ values: { income: '600', monthlyExpenses: '200' }, assets: { deposit: '10000' }, loans: [], vehicle: { fuel: '상관없음' } });

test('쿠페·컨버터블·로드스터 선택이 실제 추천 요청으로 전달된다', () => {
  for (const body of ['COUPE', 'CONVERTIBLE', 'ROADSTER']) {
    const state = input();
    state.vehicle.preferredBodyType = body;
    const {request, errors} = buildCandidateRecommendation(state);
    assert.deepEqual(errors, []);
    assert.equal(request.profile.preferred_body_type, body);
  }
});

test('design, purpose and acceleration reach inference; retired brand preference is ignored', () => {
  const state = input();
  Object.assign(state.vehicle, { exteriorSportiness: '1', exteriorAngularity: '0', lifestylePurpose: 'family', preferredBrand: '기아', brandImportance: '0', designImportance: '5', accelerationPreference: '1', performanceImportance: '5' });
  const { request, errors } = buildCandidateRecommendation(state);
  assert.deepEqual(errors, []);
  assert.equal(request.lifestyle.sportiness, 1);
  assert.equal(request.lifestyle.angularity, 0);
  assert.equal(request.lifestyle.purpose, 'family');
  assert.equal(request.lifestyle.brand, null);
  assert.equal(request.lifestyle.design_importance, 5);
  assert.equal(request.lifestyle.acceleration, 1);
  assert.equal(request.lifestyle.performance_importance, 5);
  assert.equal(request.profile.monthly_income, 6000000);
  assert.equal(request.profile.liquid_assets, 100000000);
});

test('no preference stays null and invalid saved preferences block submission', () => {
  const state = input();
  const { request } = buildCandidateRecommendation(state);
  assert.equal(request.lifestyle.sportiness, null);
  assert.equal(request.lifestyle.brand, null);
  for (const invalid of [{ exteriorSportiness: 'NaN' }, { designImportance: '0' }, { accelerationPreference: 'invalid' }, { lifestylePurpose: 'invalid' }]) {
    assert.equal(buildCandidateRecommendation({ ...state, vehicle: { ...state.vehicle, ...invalid } }).request, null);
  }
});
