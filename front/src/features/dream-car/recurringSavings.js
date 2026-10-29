import { isSavingDate, shiftMonth } from './savingsProgress.js';

export function isRecurringRule(rule) {
  return rule && typeof rule.id === 'string' && ['day', 'week', 'month'].includes(rule.unit) && Number.isInteger(rule.interval) && rule.interval >= 1 && rule.interval <= 365 && isSavingDate(rule.startDate) && Number.isFinite(rule.amount) && rule.amount > 0 && rule.amount <= 100000000 && typeof rule.memo === 'string' && rule.memo.length <= 200 && typeof rule.enabled === 'boolean' && (!rule.skipThrough || isSavingDate(rule.skipThrough));
}
export function scheduledDate(rule, index) {
  if (rule.unit === 'month') {
    const month = shiftMonth(rule.startDate.slice(0, 7), index * rule.interval);
    const [year, monthNumber] = month.split('-').map(Number);
    const day = Math.min(Number(rule.startDate.slice(8)), new Date(Date.UTC(year, monthNumber, 0)).getUTCDate());
    return `${month}-${String(day).padStart(2, '0')}`;
  }
  const date = new Date(`${rule.startDate}T00:00:00Z`);
  date.setUTCDate(date.getUTCDate() + index * rule.interval * (rule.unit === 'week' ? 7 : 1));
  return date.toISOString().slice(0, 10);
}
export function applyRecurringSavings(plan, asOfDate) {
  const records = [...(plan.records || [])];
  const ids = new Set([...records.map(record => record.id), ...(plan.deletedRecurringIds || [])]);
  for (const rule of plan.recurringRules || []) {
    if (!isRecurringRule(rule)) throw new Error('정기 기록 설정을 확인해 주세요.');
    if (!rule.enabled) continue;
    for (let index = 0; index < 100000; index++) {
      const date = scheduledDate(rule, index);
      if (date > asOfDate) break;
      if (date < (plan.startDate || `${plan.startMonth}-01`) || rule.skipThrough && date <= rule.skipThrough) continue;
      const id = `recurring:${rule.id}:${date}`;
      if (!ids.has(id)) { records.push({ id, date, amount: rule.amount, memo: rule.memo, scheduleId: rule.id }); ids.add(id); }
    }
  }
  return records.length === (plan.records || []).length ? plan : { ...plan, records };
}
export function addRecurringRule(plan, rule, asOfDate) {
  if (!isRecurringRule(rule) || rule.startDate < (plan.startDate || `${plan.startMonth}-01`)) throw new Error('시작일·금액·반복 간격을 확인해 주세요. 금액은 0보다 커야 합니다.');
  if ((plan.recurringRules || []).some(item => item.id === rule.id)) throw new Error('이미 등록된 설정입니다.');
  return applyRecurringSavings({ ...plan, recurringRules: [...(plan.recurringRules || []), rule] }, asOfDate);
}
export function toggleRecurringRule(plan, id, asOfDate) {
  const applied = applyRecurringSavings(plan, asOfDate);
  return { ...applied, recurringRules: (applied.recurringRules || []).map(rule => rule.id === id ? { ...rule, enabled: !rule.enabled, ...(!rule.enabled ? { skipThrough: asOfDate } : {}) } : rule) };
}
