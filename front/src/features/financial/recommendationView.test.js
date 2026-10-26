import assert from 'node:assert/strict';
import test from 'node:test';
import { buildRecommendationView, conditionSummary, rankingNarrative, selectComparisonViews } from './pages/recommendations/buildRecommendationView.js';

function candidate(id, preferences = []) {
  return { vehicle: { id, model: id, fuel: 'ELECTRIC', length_mm: 3830, seats: 4 }, cost: { total_purchase_cost: 28470000, monthly_running_cost: 260000, remaining_monthly: 1240000 }, decisionEvidence: { vehicleId: id, preferences, financial: { eligible: true, cashAfterPurchase: 1530000 } } };
}

test('불일치는 실제 차이와 중요도 순서로 표현하며 카드와 비교가 같은 응답을 사용한다', () => {
  const source = candidate('a', [
    { key: 'space', status: 'mismatch', weight: 3, lowerMm: 4800, upperMm: 6000, actualMm: 3830, differenceMm: 970, direction: 'shorter' },
    { key: 'fuel', status: 'mismatch', weight: 5, requested: 'ELECTRIC', actual: 'LPG' },
  ]);
  const views = buildRecommendationView({ recommendations: [source, candidate('b')] });
  assert.equal(views[0].mismatches[0].key, 'fuel');
  assert.match(views[0].mismatches[1].text, /4\.8m보다 0\.97m 짧아요/);
  assert.equal(selectComparisonViews(views, ['a', 'b'])[0], views[0]);
  assert.equal(views[0].candidate, source);
});

test('전체 후보 평가가 완료되지 않았거나 미확인 사양이 있으면 불가능을 단정하지 않는다', () => {
  const summary = { complete: false, specifiedPreferenceKeys: ['fuel', 'space'], financiallyEligibleConfigurations: 10, confirmedMatchingConfigurations: 0, unresolvedConfigurations: 2 };
  assert.equal(conditionSummary(summary), null);
  assert.match(conditionSummary({ ...summary, complete: true }), /2개.*확정하지 못/);
  assert.match(conditionSummary({ ...summary, complete: true, confirmedMatchingConfigurations: 1 }), /1개/);
});

test('기여도 없는 순위를 설명하지 않으며 근소한 차이를 우월성으로 표현하지 않는다', () => {
  const candidates = [candidate('a'), candidate('b')];
  assert.match(rankingNarrative(null, candidates), /설명할 수 없어요/);
  const comparison = { higherVehicleId: 'a', lowerVehicleId: 'b', status: 'near-tie', scoreDifference: .2 };
  assert.match(rankingNarrative(comparison, candidates), /비슷한 수준/);
  assert.ok(!rankingNarrative(comparison, candidates).includes('앞에 추천'));
});

test('존재하지 않거나 중복된 차량 ID는 다른 모델로 대체해 비교하지 않는다', () => {
  const views = buildRecommendationView({ recommendations: [candidate('a'), candidate('b')] });
  assert.equal(selectComparisonViews(views, ['a', 'unknown']), null);
  assert.equal(selectComparisonViews(views, ['a', 'a']), null);
  assert.equal(selectComparisonViews(views, ['a']), null);
});
