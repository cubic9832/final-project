import { defaultFinance } from './vehicleData.js';

export function calculateSearchSummary(conditions) {
  const amount = (key) => Math.max(0, Number(conditions[key]) || 0);
  const available = Math.max(0, (amount('income') - amount('expenses') - amount('debt')) * 0.4);
  const monthlyLimit = Math.min(amount('limit'), available);
  const downPayment = Math.min(amount('downPayment'), amount('cash'));
  // 차량별 유지비 확정 전에는 월 20만 원을 확보한 참고 구매 예산을 표시한다.
  const monthlyInstallment = Math.max(0, monthlyLimit - 20);
  const rate = defaultFinance.rate / 1200;
  const principal = monthlyInstallment * (1 - (1 + rate) ** -defaultFinance.months) / rate;
  return { available, monthlyLimit, downPayment, budget: downPayment + principal, debt: amount('debt') };
}
