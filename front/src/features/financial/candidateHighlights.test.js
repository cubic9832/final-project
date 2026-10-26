import assert from 'node:assert/strict';
import test from 'node:test';
import { buildCandidateHighlights } from './pages/recommendations/buildCandidateHighlights.js';

const candidate = (components, vehicle = {}) => ({
  vehicle: { fuel: 'ELECTRIC', length_mm: 4500, seats: 5, ...vehicle },
  cost: { monthly_running_cost: 250000, remaining_monthly: 750000 },
  integratedScore: { components },
});

test('중요한 연료 조건을 구체적인 연료명으로 먼저 설명한다', () => {
  const result = buildCandidateHighlights(candidate([
    { key: 'space', score: 100, weight: 3 }, { key: 'fuel', score: 100, weight: 5 },
  ]), { preferredSize: 'medium', fuel: '전기' });
  assert.match(result[0], /^전기 모델로, 선호하신 연료 조건에 맞아요/);
  assert.match(result[1], /25만 원.*75만 원/);
  assert.ok(!result.some(reason => reason.includes('보통 크기')));
});

test('크기와 인원 조건의 구체적인 입력과 사양을 설명하며 미확인 사양은 확정하지 않는다', () => {
  const item = candidate([{ key: 'space', score: 100, weight: 5 }, { key: 'seating', score: 100, weight: 5 }]);
  const preferences = { preferredSize: 'medium', minimumSeats: '4' };
  const result = buildCandidateHighlights(item, preferences);
  assert.match(result[0], /보통 크기.*4\.50m/);
  assert.match(result[1], /정원은 5명.*4명 이상/);
  item.lengthVerificationRequired = true;
  item.seatingVerificationRequired = true;
  assert.ok(!buildCandidateHighlights(item, preferences).some(reason => /크기 범위|탑승 조건/.test(reason)));
});

test('연료가 일치하지 않으면 일치한다는 설명을 만들지 않고 PHEV 연료명도 구분한다', () => {
  const mismatch = candidate([{ key: 'fuel', score: 0, weight: 5 }], { fuel: 'GASOLINE' });
  assert.ok(!buildCandidateHighlights(mismatch, { fuel: '전기' }).some(reason => reason.includes('연료 조건에 맞아요')));
  const phev = candidate([{ key: 'fuel', score: 100, weight: 5 }], { fuel: 'GASOLINE', original_fuel: 'PHEV' });
  assert.match(buildCandidateHighlights(phev, { fuel: '하이브리드' })[0], /^플러그인 하이브리드 모델/);
});
