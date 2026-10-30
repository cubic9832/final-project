import test from 'node:test';
import assert from 'node:assert/strict';
import { buildCandidateRecommendation } from './buildCandidateRecommendation.js';
import { createVehiclePreferences } from './createVehiclePreferences.js';

const input = () => ({ values: { income: '900', housing: '70', fixed: '30', living: '100' },
  assets: { deposit: '20000' }, loans: [], vehicle: { scenarioMode: true, fuel: '전기',
    preferredBodyType: 'PICKUP', preferredBrand: 'KG모빌리티', preferredModel: '무쏘 EV',
    annualDistanceKm: '30000', chargingAvailable: true, modelImportance: '5', brandImportance: '3' } });

test('비교 기준은 화면을 이동한 뒤에도 각각 독립적으로 추천 요청에 반영된다', () => {
  const fields = [
    ['costImportance', 'profile', 'cost_importance'],
    ['assetRetentionImportance', 'scenario', 'asset_retention_importance'],
    ['runningCostImportance', 'scenario', 'running_cost_importance'],
    ['designImportance', 'scenario', 'design_importance'],
    ['performanceImportance', 'scenario', 'performance_importance'],
    ['fuelImportance', 'profile', 'fuel_importance'],
    ['spaceImportance', 'profile', 'space_importance'],
  ];
  const state = input();
  const baseline = createVehiclePreferences(state.vehicle);
  for (const [changed] of fields) {
    for (const selected of ['1', '5']) {
      state.vehicle = createVehiclePreferences({ ...baseline, [changed]: selected });
      const { request, errors } = buildCandidateRecommendation(state);
      assert.deepEqual(errors, []);
      for (const [field, section, key] of fields) {
        assert.equal(request[section][key], field === changed ? Number(selected) : 3, `${changed}: ${field}`);
      }
    }
  }
  state.vehicle = { ...state.vehicle, costImportance: '5', assetRetentionImportance: undefined, runningCostImportance: undefined };
  const { request } = buildCandidateRecommendation(state);
  assert.equal(request.scenario.asset_retention_importance, 3);
  assert.equal(request.scenario.running_cost_importance, 3);
});

test('scenario request uses driving context and drops old saved brand and model answers', () => {
  const { request, errors } = buildCandidateRecommendation(input());
  assert.deepEqual(errors, []);
  assert.equal('lifestyle' in request, false);
  assert.equal(request.profile.annual_distance, 15000);
  assert.equal(request.profile.charging_available, true);
  assert.equal(request.profile.preferred_body_type, 'any');
  assert.equal(request.scenario.sportiness, null);
  assert.equal(request.scenario.asset_retention_importance, 3);
  assert.equal(request.scenario.running_cost_importance, 3);
  assert.equal(JSON.stringify(request).includes('무쏘 EV'), false);
  assert.equal(JSON.stringify(request).includes('KG모빌리티'), false);
});

test('invalid scenario driving context and weights stop submission', () => {
  for (const patch of [{ chargingAvailable: 'false' },
    { assetRetentionImportance: '0' }, { runningCostImportance: '6' },
    { exteriorAngularity: '2' }, { designImportance: '1.5' }]) {
    const value = input(); Object.assign(value.vehicle, patch);
    assert.equal(buildCandidateRecommendation(value).request, null);
  }
});

test('retired distance and hidden charging answers do not affect non-electric recommendations', () => {
  const value = input();
  Object.assign(value.vehicle, { fuel: '가솔린', chargingAvailable: true, annualDistanceKm: 'invalid' });
  const { request, errors } = buildCandidateRecommendation(value);
  assert.deepEqual(errors, []);
  assert.equal(request.profile.annual_distance, 15000);
  assert.equal(request.profile.charging_available, false);
  value.vehicle.fuel = '전기';
  assert.equal(buildCandidateRecommendation(value).request.profile.charging_available, true);
});

test('scenario personality answers reach the recommendation contract without losing financial constraints', () => {
  const value = input();
  Object.assign(value.vehicle, { exteriorSportiness: '1', exteriorAngularity: '0', accelerationPreference: '0.5',
    designImportance: '5', performanceImportance: '1', assetRetentionImportance: '1', runningCostImportance: '5' });
  const { request, errors } = buildCandidateRecommendation(value);
  assert.deepEqual(errors, []);
  assert.deepEqual(request.scenario, { sportiness: null, angularity: 0, acceleration: .5,
    design_importance: 5, performance_importance: 1, asset_retention_importance: 1, running_cost_importance: 5 });
  assert.equal(request.profile.liquid_assets, 200000000);
  assert.equal(request.profile.preferred_body_type, 'any');
});
