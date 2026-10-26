// Amounts are in 만 원; round the result to one won, then return 만 원.
export function calculateLoanPayment(balance, annualRate, months) {
  if ([balance, annualRate, months].some(value => value === '' || value === null || value === undefined)) return null;
  const principal = Number(balance), rate = Number(annualRate), term = Number(months);
  if (![principal, rate, term].every(Number.isFinite) || principal < 0 || principal > 9999999999.99 || rate < 0 || rate > 100 || !Number.isInteger(term) || term < 1 || term > 1200) return null;
  const monthlyRate = rate / 1200;
  const payment = monthlyRate === 0 ? principal / term : principal * monthlyRate / -Math.expm1(-term * Math.log1p(monthlyRate));
  return Math.round(payment * 10000) / 10000;
}
