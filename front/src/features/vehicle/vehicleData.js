export const vehicles = [
  { id: 'avante', name: '현대 아반떼 하이브리드', brand: 'HYUNDAI', type: '준중형 세단', condition: '신차', trim: '스마트 · 1.6 HEV · 2026년형', price: 2380, efficiency: 21.1, color: '#7199b5' },
  { id: 'ray', name: '기아 레이 1.0', brand: 'KIA', type: '경차', condition: '중고차', trim: '1.0 가솔린 · 2024년형', price: 1390, efficiency: 13, color: '#7eafa0' },
  { id: 'seltos', name: '기아 셀토스 1.6', brand: 'KIA', type: '소형 SUV', condition: '신차', trim: '1.6 가솔린 · 2026년형', price: 2270, efficiency: 12.8, color: '#d89c60' },
  { id: 'kona', name: '현대 코나 1.6', brand: 'HYUNDAI', type: '소형 SUV', condition: '중고차', trim: '1.6 가솔린 · 2024년형', price: 2490, efficiency: 13.6, color: '#5682a0' },
  { id: 'arkana', name: '르노 아르카나 1.6', brand: 'RENAULT', type: '준중형 SUV', condition: '신차', trim: '1.6 하이브리드 · 2026년형', price: 2300, efficiency: 17.4, color: '#6e9c86' },
  { id: 'casper', name: '현대 캐스퍼 1.0', brand: 'HYUNDAI', type: '경형 SUV', condition: '중고차', trim: '1.0 가솔린 · 2024년형', price: 1480, efficiency: 14.3, color: '#cf8b72' },
];
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
