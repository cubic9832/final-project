export const defaultConditions = { income: 300, expenses: 90, debt: 25, cash: 1500, downPayment: 500, limit: 45, condition: '상관없음' };
export const defaultFinance = { months: 48, rate: 5.5, distance: 15000 };
export const formatAmount = (value) => `${Math.round(value).toLocaleString('ko-KR')}만 원`;
export function calculateCosts(vehicle, conditions, finance = defaultFinance) {
  const principal = Math.max(0, vehicle.price - conditions.downPayment);
  const rate = finance.rate / 1200;
  const installment = rate === 0 ? principal / finance.months : principal * rate / (1 - (1 + rate) ** -finance.months);
  const fuel = finance.distance / 12 / vehicle.efficiency * 1700 / 10000;
  const insurance = 9;
  const tax = vehicle.type.includes('경') ? 1 : 2;
  const maintenance = 3;
  const total = installment + fuel + insurance + tax + maintenance;
  const available = Math.max(0, (conditions.income - conditions.expenses - conditions.debt) * 0.4);
  return { installment, fuel, insurance, tax, maintenance, total, interest: installment * finance.months - principal, available, remaining: available - total, score: Math.max(0, Math.min(99, Math.round(100 - Math.max(0, total - conditions.limit) * 1.5))) };
}
