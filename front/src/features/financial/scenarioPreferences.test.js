import test from 'node:test';
import assert from 'node:assert/strict';
import { buildCandidateRecommendation } from './buildCandidateRecommendation.js';

const input = () => ({ values: { income: '900', housing: '70', fixed: '30', living: '100' },
  assets: { deposit: '20000' }, loans: [], vehicle: { scenarioMode: true, fuel: '전기',
    preferredBodyType: 'PICKUP', preferredBrand: 'KG모빌리티', preferredModel: '무쏘 EV',
    annualDistanceKm: '30000', chargingAvailable: true, modelImportance: '5', brandImportance: '3' } });

test('scenario request uses driving context and drops old saved brand and model answers', () => {
  const { request, errors } = buildCandidateRecommendation(input());
  assert.deepEqual(errors, []);
  assert.equal('lifestyle' in request, false);
  assert.equal(request.profile.annual_distance, 30000);
  assert.equal(request.profile.charging_available, true);
  assert.equal(request.profile.preferred_body_type, 'PICKUP');
  assert.deepEqual(request.scenario, {});
  assert.equal(JSON.stringify(request).includes('무쏘 EV'), false);
  assert.equal(JSON.stringify(request).includes('KG모빌리티'), false);
});

test('invalid scenario driving context and weights stop submission', () => {
  for (const patch of [{ annualDistanceKm: 'invalid' }, { annualDistanceKm: '-1' }, { chargingAvailable: 'false' },
    { annualDistanceKm: '100000' }]) {
    const value = input(); Object.assign(value.vehicle, patch);
    assert.equal(buildCandidateRecommendation(value).request, null);
  }
});
