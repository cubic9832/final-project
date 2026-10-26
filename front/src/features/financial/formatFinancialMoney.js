export function formatFinancialMoney(won, maximumFractionDigits = 2) {
  if (!Number.isFinite(won)) return '계산 불가';
  const amount = Math.abs(won);
  const sign = won < 0 ? '-' : '';
  if (amount < 100000000) return `${sign}${(amount / 10000).toLocaleString('ko-KR', { maximumFractionDigits })}만 원`;
  const hundredMillions = Math.floor(amount / 100000000);
  const remainder = Number(((amount % 100000000) / 10000).toFixed(maximumFractionDigits));
  return `${sign}${hundredMillions.toLocaleString('ko-KR')}억${remainder ? ` ${remainder.toLocaleString('ko-KR', { maximumFractionDigits })}만` : ''} 원`;
}
