export function calculateFinancialSummary(values = {}, loans = []) {
  const amount = (name) => Number(values[name] || 0);
  const income = amount('income') + amount('extraIncome');
  const loanPayment = loans.reduce((sum, loan) => sum + Number(loan.payment || 0), 0);
  const livingExpenses = values.monthlyExpenses !== undefined
    ? amount('monthlyExpenses')
    : ['housing', 'fixed', 'living', 'transport', 'phone'].reduce((sum, name) => sum + amount(name), 0);
  const expenses = livingExpenses + loanPayment;
  const savings = 0; // Removed input: old navigation state must not reduce the budget.
  return { income, expenses, savings, loanPayment, available: income - expenses - savings };
}
