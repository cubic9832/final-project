export function savingsChartScale(rows, target) {
  const values = rows.flatMap(row => [row.planned, row.actual]).filter(Number.isFinite);
  const dataMaximum = Math.max(...values, 1);
  const actualMaximum = Math.max(...rows.map(row => row.actual).filter(Number.isFinite), 0);
  const hasTarget = Number.isFinite(target) && target > 0;
  const showTargetLine = hasTarget && dataMaximum >= target * 0.8;
  const achieved = hasTarget && actualMaximum >= target;
  const minimum = Math.min(...values, ...(showTargetLine ? [target] : []));
  const maximum = Math.max(dataMaximum, showTargetLine ? target : 0);
  const span = Math.max(maximum - minimum, maximum * 0.02, 10);
  const rawStep = span / 4;
  const magnitude = 10 ** Math.floor(Math.log10(rawStep));
  const step = [1, 2, 2.5, 5, 10].find(value => value * magnitude >= rawStep) * magnitude;
  const lower = Math.max(0, Math.floor((minimum - span * 0.08) / step) * step);
  const paddedUpper = Math.ceil((maximum + span * 0.12) / step) * step;
  const upper = achieved ? Math.min(paddedUpper, actualMaximum * 1.05) : paddedUpper;
  const ticks = Array.from({ length: Math.floor((upper - lower) / step) + 1 }, (_, index) => Number((lower + index * step).toFixed(6)));
  return { lower, upper, ticks, showTargetLine, achieved };
}
