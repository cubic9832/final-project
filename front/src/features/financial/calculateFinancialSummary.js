export function calculateFinancialSummary(values = {}) {
  const amount = (name) => Number(values[name] || 0);
  const income = amount('income') + amount('extraIncome');
  const expenses = ['housing', 'fixed', 'living', 'loan', 'transport', 'phone']
    .reduce((sum, name) => sum + amount(name), 0);
  const savings = amount('savings');
  return { income, expenses, savings, available: income - expenses - savings };
}
