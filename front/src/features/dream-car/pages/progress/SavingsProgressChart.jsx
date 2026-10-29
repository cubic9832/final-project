import { useId, useState } from 'react';
import { calculateSavingsProgress, formatMoney, shiftMonth } from '../../savingsProgress';
import { savingsChartScale } from './savingsChartScale';

export default function SavingsProgressChart({ plan, asOfMonth }) {
  const [hovered, setHovered] = useState(null);
  const summary = calculateSavingsProgress(plan, asOfMonth);
  const [range, setRange] = useState('6');
  const gradientId = useId().replaceAll(':', '');
  // 실제 기록 이후 두 달의 계획만 표시해 다음 목표와 여유 공간을 제공한다.
  const currentIndex = Math.min(600, Math.max(1, summary.elapsed));
  const end = currentIndex + 2;
  const start = range === 'all' ? 0 : Math.max(0, currentIndex - Number(range));
  const rows = Array.from({ length: end - start + 1 }, (_, offset) => {
    const index = start + offset;
    const month = shiftMonth(plan.startMonth, index - 1);
    const monthly = index === 0 ? null : calculateSavingsProgress(plan, month);
    const actual = index === 0 ? plan.initialSavings : monthly.total;
    const shortfall = monthly?.monthlyGap < 0 ? -monthly.monthlyGap : 0;
    return { index, month, shortfall, recorded: index === 0 || Boolean(monthly?.currentEntry), planned: Math.min(plan.target, plan.initialSavings + index * plan.monthlySaving), actual: index <= summary.elapsed ? actual : null };
  });
  const width = 900, height = 435, left = 90, right = 34, top = 110, bottom = 50;
  const { lower, upper, ticks, showTargetLine } = savingsChartScale(rows, plan.target);
  const x = index => left + (index - start) / Math.max(1, end - start) * (width - left - right);
  const y = value => height - bottom - (value - lower) / (upper - lower) * (height - top - bottom);
  const path = (values, key) => values.filter(row => row[key] !== null).map((row, index) => `${index ? 'L' : 'M'}${x(row.index)},${y(row[key])}`).join(' ');
  const actualRows = rows.filter(row => row.actual !== null);
  const focused = rows.find(row => row.index === hovered) || actualRows.at(-1) || rows[0];
  const tickStep = Math.max(1, Math.ceil((end - start) / 6));
  const labelRows = end - start <= 12 ? actualRows.filter(row => row.shortfall > 0 && row.recorded) : focused?.shortfall > 0 ? [focused] : [];
  return <>
    <div className="savings-chart-toolbar"><div className="savings-legend"><span className="planned">계획 누적액</span><span className="actual">기록한 누적액</span><span className="shortfall">월 목표 미달</span><span className="goal">최종 목표</span></div><div className="savings-range" aria-label="차트 표시 기간">{[['6', '6개월'], ['12', '12개월'], ['all', '전체']].map(([value, label]) => <button type="button" key={value} aria-pressed={range === value} onClick={() => { setRange(value); setHovered(null); }}>{label}</button>)}</div></div>
    <div className="savings-chart-zoom-note"><span>누적 자금 확대 보기</span><strong>{formatMoney(lower)} ~ {formatMoney(upper)}</strong></div>
    <div className="savings-chart-scroll"><svg viewBox={`0 0 ${width} ${height}`} className="savings-chart" role="img" aria-label={`확대 누적 저축 차트. 표시 범위 ${formatMoney(lower)}부터 ${formatMoney(upper)}. 최종 목표 ${formatMoney(plan.target)}는 상단에 별도 표시합니다.`}>
      <title>누적 자금과 목표 달성 차트</title><desc>상단은 최종 목표 안내입니다. 그래프가 목표 금액의 80% 수준에 가까워지면 금액 축에 목표선을 표시합니다. 목표 초과 시 세로축 상한은 실제 최고 금액의 105% 이내입니다. 파란 점선은 계획, 민트 선은 기록 누적액, 빨간 원은 월 목표 미달입니다. 이후 두 달은 계획만 표시합니다.</desc>
      <defs><linearGradient id={gradientId} x1="0" x2="0" y1="0" y2="1"><stop offset="0%" stopColor="var(--color-mint)" stopOpacity="0.25" /><stop offset="100%" stopColor="var(--color-mint)" stopOpacity="0.025" /></linearGradient></defs>
      <rect x={left} y={4} width={width - left - right} height={62} rx={8} className="savings-target-band" />
      <text x={left + 16} y={29} className="savings-target-caption">최종 목표 · {summary.targetMonth}</text><text x={width - right - 16} y={40} textAnchor="end" className="savings-target-amount">{formatMoney(plan.target)}</text>
      <line x1={left + 16} x2={width - right - 16} y1={53} y2={53} className="savings-goal-line" />
      <text x={left} y={92}>단위: 만 원 · 확대 축</text>
      {ticks.map(value => <g key={value}><line x1={left} x2={width - right} y1={y(value)} y2={y(value)} className="savings-gridline" /><text x={left - 12} y={y(value) + 4} textAnchor="end">{value.toLocaleString('ko-KR', { maximumFractionDigits: 1 })}</text></g>)}
      {actualRows.length > 0 && <path d={`${path(actualRows, 'actual')} L${x(actualRows.at(-1).index)},${height - bottom} L${x(actualRows[0].index)},${height - bottom} Z`} fill={`url(#${gradientId})`} />}
      {actualRows.slice(1).map((row, index) => <path key={row.index} d={`M${x(actualRows[index].index)},${y(actualRows[index].planned)} L${x(row.index)},${y(row.planned)} L${x(row.index)},${y(row.actual)} L${x(actualRows[index].index)},${y(actualRows[index].actual)} Z`} className={row.actual < row.planned ? 'savings-gap-area' : 'savings-ahead-area'} />)}
      <path d={path(rows, 'planned')} className="savings-planned-line" />
      <path d={path(actualRows, 'actual')} className="savings-actual-line" />
      {showTargetLine && <g className={summary.remaining === 0 ? 'savings-goal-reached' : undefined}><line x1={left} x2={width - right} y1={y(plan.target)} y2={y(plan.target)} className="savings-goal-line savings-target-in-chart" /><text x={width - right} y={y(plan.target) - 10} textAnchor="end" className="savings-goal-label">{summary.remaining === 0 ? '목표 달성' : '최종 목표'} {formatMoney(plan.target)}</text></g>}
      {rows.map(row => <g key={row.index}>{row.actual !== null && row.recorded && <circle cx={x(row.index)} cy={y(row.actual)} r={row.shortfall > 0 ? 5 : 4} className={`savings-actual-dot${row.shortfall > 0 ? ' savings-shortfall-dot' : ''}`}><title>{row.month}: {row.shortfall > 0 ? `${formatMoney(row.shortfall)} 부족` : '월 목표 달성'}</title></circle>}{(row.index === start || row.index >= currentIndex || (row.index - start) % tickStep === 0) && <text x={x(row.index)} y={height - 14} textAnchor="middle">{row.index === 0 ? '시작' : `${row.month.slice(2, 4)}.${row.month.slice(5)}`}</text>}<rect x={x(row.index) - Math.max(4, (width - left - right) / (end - start + 1) / 2)} y={top} width={Math.max(8, (width - left - right) / (end - start + 1))} height={height - top - bottom} fill="transparent" onMouseEnter={() => setHovered(row.index)} onClick={() => setHovered(row.index)} /></g>)}
      {labelRows.map((row, index) => <text key={row.index} x={x(row.index) + (row.index === end ? -12 : 12)} y={Math.max(top + 14, y(row.actual) - 18 - (index % 2) * 16)} textAnchor={row.index === end ? 'end' : 'start'} className="savings-shortfall-label">{formatMoney(row.shortfall)} 부족</text>)}
      {focused && <line x1={x(focused.index)} x2={x(focused.index)} y1={top} y2={height - bottom} className="savings-cursor" />}
    </svg></div>
    {focused && <div className="savings-chart-detail"><strong>{focused.index === 0 ? '시작 자금' : focused.month}</strong><span>계획 {formatMoney(focused.planned)}</span><span>기록 누적 {focused.actual === null ? '아직 도래하지 않은 월' : formatMoney(focused.actual)}</span>{focused.shortfall > 0 && <span className="savings-shortfall-detail">월 목표보다 {formatMoney(focused.shortfall)} 부족</span>}{focused.index > 0 && focused.actual !== null && !focused.recorded && <span>해당 월 미기록</span>}</div>}
    
  </>;
}
