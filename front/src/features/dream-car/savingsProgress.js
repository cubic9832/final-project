export const progressStorageKey = 'dream-car-progress-v1';
export const planStorageKey = 'dream-car-plan-v3';
export const formatMoney = value => `${Number(value.toFixed(2)).toLocaleString('ko-KR')}만 원`;
export function currentDate() {
  return new Intl.DateTimeFormat('sv-SE', { timeZone: 'Asia/Seoul', year: 'numeric', month: '2-digit', day: '2-digit' }).format(new Date());
}
export function isSavingDate(date) {
  if (typeof date !== 'string' || !/^\d{4}-\d{2}-\d{2}$/.test(date)) return false;
  const parsed = new Date(`${date}T00:00:00Z`);
  return Number.isFinite(parsed.getTime()) && parsed.toISOString().slice(0, 10) === date;
}
export function currentMonth() {
  return new Intl.DateTimeFormat('sv-SE', { timeZone: 'Asia/Seoul', year: 'numeric', month: '2-digit' }).format(new Date());
}
export function monthIndex(month) {
  if (!/^\d{4}-(0[1-9]|1[0-2])$/.test(month)) return NaN;
  const [year, value] = month.split('-').map(Number);
  return year * 12 + value - 1;
}
export function shiftMonth(month, offset) {
  const value = monthIndex(month) + offset;
  return `${Math.floor(value / 12)}-${String(value % 12 + 1).padStart(2, '0')}`;
}
export function createProgressPlan(vehicle, inputs, target, start, id) {
  const startMonth = start.slice(0, 7);
  const startDate = start.length === 7 ? `${start}-01` : start;
  if (!Number.isFinite(target) || target <= 0 || !Number.isFinite(monthIndex(startMonth)) || !Number.isInteger(inputs.targetMonths) || inputs.targetMonths < 1) throw new Error('계획의 목표 금액과 기간을 확인해 주세요.');
  if (!isSavingDate(startDate)) throw new Error('시작 날짜를 확인해 주세요.');
  return { id, vehicleId: vehicle.id, name: `${vehicle.brand} ${vehicle.model}`, trim: vehicle.trim, target, initialSavings: inputs.savings, monthlySaving: inputs.monthlySaving, targetMonths: inputs.targetMonths, startMonth, startDate, entries: {} };
}
export function updateProgressStart(plan, startDate, initialSavings, _asOfDate) {
  if (!isSavingDate(startDate) || startDate < '2000-01-01' || startDate > '2100-12-31') throw new Error('시작일은 2000년 1월 1일부터 2100년 12월 31일 사이로 선택해 주세요.');
  if (!Number.isFinite(initialSavings) || initialSavings < 0 || initialSavings > 100000000) throw new Error('시작 자금은 0~100,000,000만 원 범위로 입력해 주세요.');
  const startMonth = startDate.slice(0, 7);
  if (getSavingRecords(plan).some(record => record.date ? record.date < startDate : record.month < startMonth)) throw new Error('이미 기록한 저축보다 늦은 날짜로 시작일을 변경할 수 없습니다. 기존 기록을 먼저 확인해 주세요.');
  return { ...plan, startDate, startMonth, initialSavings };
}
export function updateProgressSettings(plan, startDate, initialSavings, remainingMonths, monthlySaving, asOfDate) {
  if (!Number.isInteger(remainingMonths) || remainingMonths < 1 || remainingMonths > 1200) throw new Error('목표까지 남은 기간은 1~1,200개월의 정수로 입력해 주세요.');
  if (!Number.isFinite(monthlySaving) || monthlySaving < 0 || monthlySaving > 100000000) throw new Error('매월 저축할 금액은 0~100,000,000만 원 범위로 입력해 주세요.');
  const next = updateProgressStart(plan, startDate, initialSavings, asOfDate);
  const previousMonths = Math.max(0, monthIndex(asOfDate.slice(0, 7)) - monthIndex(next.startMonth));
  return { ...next, monthlySaving, targetMonths: previousMonths + remainingMonths };
}
export function isProgressPlan(plan) {
  return plan && typeof plan.id === 'string' && typeof plan.name === 'string' && Number.isFinite(monthIndex(plan.startMonth)) && ['target', 'initialSavings', 'monthlySaving', 'targetMonths'].every(key => Number.isFinite(plan[key]) && plan[key] >= 0) && plan.target > 0 && Number.isInteger(plan.targetMonths) && plan.targetMonths > 0 && plan.entries && typeof plan.entries === 'object' && !Array.isArray(plan.entries) && Object.entries(plan.entries).every(([month, entry]) => Number.isFinite(monthIndex(month)) && month >= plan.startMonth && Number.isFinite(entry.amount) && entry.amount >= 0 && typeof entry.memo === 'string') && (plan.records === undefined || Array.isArray(plan.records) && plan.records.every(record => typeof record.id === 'string' && isSavingDate(record.date) && record.date.slice(0, 7) >= plan.startMonth && Number.isFinite(record.amount) && record.amount >= 0 && typeof record.memo === 'string') && new Set(plan.records.map(record => record.id)).size === plan.records.length);
}
export function getSavingRecords(plan) {
  const legacy = Object.entries(plan.entries).map(([month, entry]) => ({ ...entry, id: `legacy-${month}`, date: '', month, legacyMonth: month }));
  return [...legacy, ...(plan.records || []).map(record => ({ ...record, month: record.date.slice(0, 7) }))].sort((a, b) => (b.date || b.month).localeCompare(a.date || a.month));
}
export function calculateSavingsProgress(plan, asOfMonth) {
  const elapsed = Math.max(0, monthIndex(asOfMonth) - monthIndex(plan.startMonth) + 1);
  const entries = getSavingRecords(plan).filter(record => record.month >= plan.startMonth && record.month <= asOfMonth);
  const total = Math.round((plan.initialSavings + entries.reduce((sum, entry) => sum + entry.amount, 0)) * 100) / 100;
  const planned = Math.min(plan.target, plan.initialSavings + elapsed * plan.monthlySaving);
  const monthlyGoal = elapsed === 0 ? 0 : Math.min(plan.monthlySaving, Math.max(0, plan.target - (plan.initialSavings + Math.max(0, elapsed - 1) * plan.monthlySaving)));
  const currentRecords = entries.filter(record => record.month === asOfMonth);
  const currentEntry = currentRecords.length ? { amount: Math.round(currentRecords.reduce((sum, record) => sum + record.amount, 0) * 100) / 100, memo: currentRecords.length === 1 ? currentRecords[0].memo : `${currentRecords.length}건 합산` } : undefined;
  const remaining = Math.max(0, plan.target - total);
  const monthlyGap = currentEntry ? Math.round((currentEntry.amount - monthlyGoal) * 100) / 100 : null;
  const missingMonths = Math.max(0, elapsed - new Set(entries.map(record => record.month)).size);
  return { total, planned, monthlyGoal, monthlyGap, currentEntry, remaining, progress: Math.min(100, total / plan.target * 100), cumulativeGap: total - planned, elapsed, missingMonths, targetMonth: shiftMonth(plan.startMonth, plan.targetMonths - 1) };
}

export function recordDailySaving(plan, date, amount, memo, asOfDate, id, editingId = null) {
  if (!isSavingDate(date) || date < (plan.startDate || `${plan.startMonth}-01`) || date > asOfDate) throw new Error('계획 시작일부터 오늘 사이의 날짜를 선택해 주세요.');
  if (!Number.isFinite(amount) || amount < 0 || amount > 100000000) throw new Error('저축액은 0~100,000,000만 원 범위로 입력해 주세요.');
  if (typeof memo !== 'string' || memo.length > 200) throw new Error('메모는 200자 이내로 입력해 주세요.');
  const existing = editingId ? getSavingRecords(plan).find(record => record.id === editingId) : null;
  if (editingId && !existing) throw new Error('수정할 기록을 찾을 수 없습니다.');
  if (typeof id !== 'string' || !id || !editingId && (plan.records || []).some(record => record.id === id)) throw new Error('기록 식별자가 올바르지 않습니다. 다시 시도해 주세요.');
  const entries = { ...plan.entries };
  if (existing?.legacyMonth) delete entries[existing.legacyMonth];
  const records = (plan.records || []).filter(record => record.id !== editingId);
  records.push({ ...(existing?.scheduleId ? { scheduleId: existing.scheduleId } : {}), id: existing && !existing.legacyMonth ? existing.id : id, date, amount, memo });
  return { ...plan, entries, records };
}
export function recordMonthlySaving(plan, month, amount, memo, asOfMonth) {
  if (!Number.isFinite(monthIndex(month)) || month < plan.startMonth || month > asOfMonth) throw new Error('시작 월부터 이번 달 사이의 월을 선택해 주세요.');
  if (!Number.isFinite(amount) || amount < 0 || amount > 100000000) throw new Error('저축액은 0~100,000,000만 원 범위로 입력해 주세요.');
  if (typeof memo !== 'string' || memo.length > 200) throw new Error('메모는 200자 이내로 입력해 주세요.');
  return { ...plan, entries: { ...plan.entries, [month]: { amount, memo } } };
}

export function deleteSavingRecord(plan, id) {
  const record = getSavingRecords(plan).find(item => item.id === id);
  if (!record) throw new Error('삭제할 저축 기록을 찾을 수 없습니다.');
  const entries = { ...plan.entries };
  if (record.legacyMonth) delete entries[record.legacyMonth];
  const deletedRecurringIds = [...(plan.deletedRecurringIds || [])];
  if (record.scheduleId || id.startsWith('recurring:')) deletedRecurringIds.push(id);
  return { ...plan, entries, records: (plan.records || []).filter(item => item.id !== id), deletedRecurringIds: [...new Set(deletedRecurringIds)] };
}
