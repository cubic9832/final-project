// 금액 단위: 만 원. 수익률·물가·잔존가치를 가정하지 않는 현금 구매 계획.
export const defaultPlan = { savings: 1000, monthlySaving: 100, targetMonths: 36, annualDistance: 12000, energyPrice: 1700, efficiency: 12, insurance: 120, annualTax: 50, maintenance: 60, parking: 10, registrationRate: 7, extras: 100, reserveMonths: 6 };

export function calculatePurchasePlan(price, inputs) {
  if (!Number.isFinite(price) || price <= 0 || Object.values(inputs).some(value => !Number.isFinite(value) || value < 0) || inputs.efficiency <= 0 || inputs.targetMonths <= 0) return null;
  const energy = inputs.annualDistance / inputs.efficiency * inputs.energyPrice / 10000 / 12;
  const monthlyCosts = { energy, insurance: inputs.insurance / 12, tax: inputs.annualTax / 12, maintenance: inputs.maintenance / 12, parking: inputs.parking };
  const monthlyTotal = Object.values(monthlyCosts).reduce((sum, value) => sum + value, 0);
  const registration = price * inputs.registrationRate / 100;
  const reserve = monthlyTotal * inputs.reserveMonths;
  const purchaseTotal = price + registration + inputs.extras;
  const target = purchaseTotal + reserve;
  const remaining = Math.max(0, target - inputs.savings);
  const months = remaining === 0 ? 0 : inputs.monthlySaving > 0 ? Math.ceil(remaining / inputs.monthlySaving) : null;
  return { monthlyCosts, monthlyTotal, registration, reserve, purchaseTotal, target, remaining, months, requiredMonthly: remaining / inputs.targetMonths, progress: Math.min(100, inputs.savings / target * 100), fasterMonths: remaining === 0 ? 0 : Math.ceil(remaining / (inputs.monthlySaving + 30)), firstYear: purchaseTotal + monthlyTotal * 12 };
}
