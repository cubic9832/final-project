export function calculateFinancialSummary(values = {}, loans = []) {
  const amount = (name) => Number(values[name] || 0);
  const income = amount('income') + amount('extraIncome');
  const loanPayment = loans.reduce((sum, loan) => sum + Number(loan.payment || 0), 0);
  const expenses = ['housing', 'fixed', 'living', 'transport', 'phone']
    .reduce((sum, name) => sum + amount(name), loanPayment);
  const savings = amount('savings');
  return { income, expenses, savings, loanPayment, available: income - expenses - savings };
}
