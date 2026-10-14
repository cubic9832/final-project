import { calculateFinancialSummary } from './calculateFinancialSummary.js';

// 화면용 시뮬레이션 가정. 실제 대출 금리·유지비·심사 결과가 아니다.
export function calculateVehicleBudget({ values = {}, assets = {}, vehicle = {} } = {}) {
  const totals = calculateFinancialSummary(values);
  const operatingCost = 20;
  const annualRate = 0.06;
  const months = vehicle.installment === '일시불' ? 0 : Number.parseInt(vehicle.installment, 10);
  const deposit = Math.max(0, Number(assets.deposit || 0) - Number(assets.emergency || 0));
  const downPayment = Math.min(deposit, Math.max(0, Number(assets.downPayment || 0)));
  const monthlyPayment = Math.max(0, totals.available * 0.75 - operatingCost);
  const monthlyRate = annualRate / 12;
  const loan = months > 0 ? monthlyPayment * (1 - (1 + monthlyRate) ** -months) / monthlyRate : 0;
  const budget = downPayment + loan;
  const valid = ['income', 'housing', 'fixed', 'living'].every((key) => values[key] !== undefined && values[key] !== '')
    && ['deposit', 'downPayment', 'emergency'].every((key) => assets[key] !== undefined && assets[key] !== '')
    && Number.isFinite(months);
  return { ...totals, operatingCost, annualRate, months, downPayment, monthlyPayment: months === 0 ? 0 : monthlyPayment,
    low: downPayment + loan * 0.8, high: budget, valid };
}
