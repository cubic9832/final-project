import test from 'node:test';
import assert from 'node:assert/strict';
import { calculateSavingsProgress, createProgressPlan, getSavingRecords, isProgressPlan, recordDailySaving, recordMonthlySaving, shiftMonth, updateProgressSettings, updateProgressStart } from './savingsProgress.js';
import { savingsChartScale } from './pages/progress/savingsChartScale.js';

const plan = createProgressPlan({ id: 'test', brand: '현대', model: '팰리세이드', trim: '기본' }, { savings: 1000, monthlySaving: 100, targetMonths: 40 }, 5000, '2026-10', 'test');
test('시작 자금은 한 번만 합산하고 당월 부족·누적 부족을 구분한다', () => {
  let next = recordMonthlySaving(plan, '2026-10', 100, '', '2026-11');
  next = recordMonthlySaving(next, '2026-11', 80, '이번 달', '2026-11');
  const result = calculateSavingsProgress(next, '2026-11');
  assert.equal(result.total, 1180);
  assert.equal(result.planned, 1200);
  assert.equal(result.monthlyGap, -20);
  assert.equal(result.cumulativeGap, -20);
  assert.equal(result.targetMonth, '2030-01');
});
test('미기록은 0원 기록과 다르고 같은 월 수정은 덮어쓴다', () => {
  assert.equal(calculateSavingsProgress(plan, '2026-10').monthlyGap, null);
  const zero = recordMonthlySaving(plan, '2026-10', 0, '', '2026-10');
  assert.equal(calculateSavingsProgress(zero, '2026-10').monthlyGap, -100);
  const edited = recordMonthlySaving(zero, '2026-10', 150, '', '2026-10');
  assert.equal(calculateSavingsProgress(edited, '2026-10').total, 1150);
  assert.equal(calculateSavingsProgress(edited, '2026-10').monthlyGap, 50);
});
test('목표 초과 달성은 실제 잔액을 유지하되 남은 목표와 달성률을 제한한다', () => {
  const next = recordMonthlySaving(plan, '2026-10', 5000, '', '2026-10');
  const result = calculateSavingsProgress(next, '2026-10');
  assert.equal(result.total, 6000);
  assert.equal(result.remaining, 0);
  assert.equal(result.progress, 100);
});
test('이전 월·미래 월·음수·잘못된 기록은 저장하지 않는다', () => {
  for (const [month, amount] of [['2026-09', 1], ['2026-12', 1], ['2026-13', 1], ['2026-10', -1], ['2026-10', NaN]]) assert.throws(() => recordMonthlySaving(plan, month, amount, '', '2026-11'));
  assert.ok(isProgressPlan(plan));
  assert.equal(isProgressPlan({ ...plan, entries: { '2026-13': { amount: 10, memo: '' } } }), false);
  assert.equal(shiftMonth('2026-12', 1), '2027-01');
});

test('확대 축은 최종 목표가 아닌 표시 중인 누적 자금 범위를 기준으로 잡는다', () => {
  const scale = savingsChartScale([{ planned: 1000, actual: 1000 }, { planned: 1100, actual: 1090 }, { planned: 1200, actual: 1180 }]);
  assert.ok(scale.lower > 0);
  assert.ok(scale.lower <= 1000);
  assert.ok(scale.upper >= 1200);
  assert.ok(scale.upper < 5500);
  assert.ok(275 * 10 / (scale.upper - scale.lower) > 5);
});

test('정체된 자금과 목표 초과 자금도 유효한 확대 범위에 들어간다', () => {
  for (const values of [[0, 0], [1000, 1000], [5500, 6000]]) {
    const scale = savingsChartScale([{ planned: values[0], actual: values[1] }]);
    assert.ok(scale.upper > scale.lower);
    assert.ok(scale.lower <= Math.min(...values));
    assert.ok(scale.upper >= Math.max(...values));
    assert.ok(scale.ticks.every(Number.isFinite));
  }
});

test('목표 80%부터 목표선을 같은 금액 축에 포함한다', () => {
  const far = savingsChartScale([{ planned: 1000, actual: 1000 }, { planned: 4300, actual: 4200 }], 5500);
  assert.equal(far.showTargetLine, false);
  const near = savingsChartScale([{ planned: 1000, actual: 1000 }, { planned: 4400, actual: 4400 }], 5500);
  assert.equal(near.showTargetLine, true);
  assert.ok(near.upper >= 5500);
  assert.ok(near.lower <= 5500);
});

test('목표 도달·초과 시 최고 실적에서 5%를 넘는 상단 여백을 만들지 않는다', () => {
  for (const actual of [5500, 5501, 6000, 10500]) {
    const scale = savingsChartScale([{ planned: 1000, actual: 1000 }, { planned: 5500, actual }], 5500);
    assert.equal(scale.achieved, true);
    assert.equal(scale.showTargetLine, true);
    assert.ok(scale.upper >= actual);
    assert.ok(scale.upper <= actual * 1.05);
    assert.ok(scale.ticks.every(tick => tick <= scale.upper));
  }
});

test('날짜별 여러 번 입금은 일자와 관계없이 월별로 합산하고 시작 자금은 중복하지 않는다', () => {
  let next = recordDailySaving(plan, '2026-10-02', 10, '', '2026-11-30', 'a');
  next = recordDailySaving(next, '2026-10-02', 20, '', '2026-11-30', 'b');
  next = recordDailySaving(next, '2026-10-31', 70, '', '2026-11-30', 'c');
  next = recordDailySaving(next, '2026-11-15', 50, '', '2026-11-30', 'd');
  assert.equal(next.records.length, 4);
  assert.ok(isProgressPlan(next));
  assert.equal(calculateSavingsProgress(next, '2026-10').total, 1100);
  assert.equal(calculateSavingsProgress(next, '2026-10').monthlyGap, 0);
  assert.equal(calculateSavingsProgress(next, '2026-11').total, 1150);
  assert.equal(calculateSavingsProgress(next, '2026-11').monthlyGap, -50);
  assert.equal(calculateSavingsProgress(next, '2026-11').missingMonths, 0);
});

test('기록 날짜를 다른 달로 수정하면 중복 없이 해당 월 합계를 갱신한다', () => {
  const initial = recordDailySaving(plan, '2026-10-02', 80, '', '2026-11-30', 'a');
  const edited = recordDailySaving(initial, '2026-11-03', 90, '수정', '2026-11-30', 'unused', 'a');
  assert.equal(edited.records.length, 1);
  assert.equal(edited.records[0].id, 'a');
  assert.equal(calculateSavingsProgress(edited, '2026-10').currentEntry, undefined);
  assert.equal(calculateSavingsProgress(edited, '2026-11').total, 1090);
});

test('기존 월별 기록을 보존하고 날짜별 기록으로 옮겨도 중복 합산하지 않는다', () => {
  const legacy = recordMonthlySaving(plan, '2026-10', 100, '기존 기록', '2026-10');
  assert.equal(getSavingRecords(legacy)[0].date, '');
  const migrated = recordDailySaving(legacy, '2026-10-20', 100, '옮긴 기록', '2026-10-29', 'new', 'legacy-2026-10');
  assert.deepEqual(migrated.entries, {});
  assert.equal(calculateSavingsProgress(migrated, '2026-10').total, 1100);
  assert.equal(getSavingRecords(migrated).length, 1);
});

test('잘못된 날짜·미래·시작 전·중복 식별자 기록을 거절하고 소액 합계의 오차를 제거한다', () => {
  for (const date of ['2026-10-32', '2026-02-29', '2026-09-30', '2026-11-01']) assert.throws(() => recordDailySaving(plan, date, 10, '', '2026-10-29', 'a'));
  let next = recordDailySaving({ ...plan, monthlySaving: 0.3 }, '2026-10-01', 0.1, '', '2026-10-29', 'a');
  assert.throws(() => recordDailySaving(next, '2026-10-02', 0.1, '', '2026-10-29', 'a'));
  next = recordDailySaving(next, '2026-10-02', 0.2, '', '2026-10-29', 'b');
  assert.equal(calculateSavingsProgress(next, '2026-10').currentEntry.amount, 0.3);
  assert.equal(calculateSavingsProgress(next, '2026-10').monthlyGap, 0);
});

test('과거 시작일로 변경하면 이전 저축을 기록할 수 있고 누적 목표도 다시 계산한다', () => {
  const changed = updateProgressStart(plan, '2026-08-15', 500, '2026-10-29');
  const next = recordDailySaving(changed, '2026-08-15', 100, '', '2026-10-29', 'past');
  assert.equal(next.startMonth, '2026-08');
  assert.equal(next.startDate, '2026-08-15');
  assert.equal(calculateSavingsProgress(next, '2026-10').total, 600);
  assert.equal(calculateSavingsProgress(next, '2026-10').planned, 800);
  assert.throws(() => recordDailySaving(changed, '2026-08-14', 1, '', '2026-10-29', 'too-early'));
});

test('기존 기록보다 늦은 시작일은 거절하며 새 계획도 날짜를 보존한다', () => {
  const next = recordDailySaving(plan, '2026-10-05', 10, '', '2026-10-29', 'a');
  assert.throws(() => updateProgressStart(next, '2026-10-06', 1000, '2026-10-29'));
  assert.throws(() => updateProgressStart(next, '2026-11-01', 1000, '2026-10-29'));
  const created = createProgressPlan({ id: 'car', brand: '현대', model: '차량', trim: '기본' }, { savings: 1000, monthlySaving: 100, targetMonths: 36 }, 5000, '2026-03-15', 'new');
  assert.equal(created.startDate, '2026-03-15');
  assert.equal(created.startMonth, '2026-03');
});

test('미래 계획은 2100년까지 저장하고 시작 전 목표·기록을 누적하지 않는다', () => {
  const future = updateProgressSettings(plan, '2100-12-31', 1000, 36, 100, '2026-10-29');
  assert.equal(future.startDate, '2100-12-31');
  assert.equal(future.targetMonths, 36);
  const summary = calculateSavingsProgress(future, '2026-10');
  assert.equal(summary.elapsed, 0);
  assert.equal(summary.monthlyGoal, 0);
  assert.equal(summary.planned, 1000);
  assert.equal(summary.missingMonths, 0);
  assert.throws(() => recordDailySaving(future, '2026-10-29', 100, '', '2026-10-29', 'early'));
  assert.throws(() => updateProgressSettings(plan, '2101-01-01', 1000, 36, 100, '2026-10-29'));
});

test('남은 기간과 월 저축액 변경은 실적을 유지하고 목표 시점과 계획선을 갱신한다', () => {
  const original = recordDailySaving(plan, '2026-10-05', 80, '', '2026-12-10', 'a');
  const changed = updateProgressSettings(original, '2026-10-01', 1000, 6, 150, '2026-12-10');
  const result = calculateSavingsProgress(changed, '2026-12');
  assert.equal(changed.targetMonths, 8);
  assert.equal(result.targetMonth, '2027-05');
  assert.equal(result.monthlyGoal, 150);
  assert.equal(result.planned, 1450);
  assert.equal(result.total, 1080);
  assert.deepEqual(changed.records, original.records);
  for (const months of [0, -1, 1.5, 1201]) assert.throws(() => updateProgressSettings(original, '2026-10-01', 1000, months, 100, '2026-12-10'));
  assert.throws(() => updateProgressSettings(original, '2026-10-01', 1000, 6, -1, '2026-12-10'));
});
