import { candidateMoney, fuelLabels } from './candidatePresentation.js';
import { bodyTypeLabel } from '../../vehiclePreferences.js';

export const evaluationLabels = { body: '차체 형태 적합도', cost: '구매비·유지비 부담', fuel: '연료 적합도', space: '크기 적합도', seating: '탑승 인원', purpose: '이용 목적 참고', model: '모델 참고 평가', budget: '예산 가격대' };
const fuelName = fuel => ({ PHEV: '플러그인 하이브리드', MILD_HYBRID: '마일드 하이브리드', ...fuelLabels })[fuel] ?? fuel;
const meters = value => (value / 1000).toLocaleString('ko-KR', { maximumFractionDigits: 3 });
// 현재 차체·연료 라벨의 영문 약어(SUV, MPV, LPG)는 모두 모음으로 끝나게 읽는다.
const preferenceEnding = (label, consonantEnding, vowelEnding) => {
  const last = label.charCodeAt(label.length - 1);
  const hasFinalConsonant = last >= 0xac00 && last <= 0xd7a3 && (last - 0xac00) % 28 !== 0;
  return `${label}${hasFinalConsonant ? consonantEnding : vowelEnding}`;
};

export function describePreference(item) {
  if (item.status === 'reference') return null;
  if (item.key === 'body') return { ...item, text: item.status === 'unknown' ? '차체 형태 정보가 없어 선호 일치 여부를 확인할 수 없어요.' : item.status === 'match' ? `${bodyTypeLabel(item.actual)} 모델로, 선호하신 차체 형태에 맞아요.` : `선호하신 형태는 ${preferenceEnding(bodyTypeLabel(item.requested), '이지만', '지만')}, 이 차량은 ${preferenceEnding(bodyTypeLabel(item.actual), '이에요', '예요')}.` };
  if (item.status === 'unknown') return { ...item, text: item.key === 'space' ? '전장 정보가 없어 희망 크기 충족 여부를 확인할 수 없어요.' : '기본 승차 정원이 없어 희망 인원 충족 여부를 확인할 수 없어요.' };
  let text;
  if (item.key === 'fuel') text = item.status === 'match'
    ? `${fuelName(item.actual)} 모델로, 선호하신 ${fuelName(item.requested)} 조건에 맞아요.`
    : `선호하신 연료는 ${preferenceEnding(fuelName(item.requested), '이지만', '지만')}, 이 차량은 ${fuelName(item.actual)} 모델이에요.`;
  if (item.key === 'space') text = item.status === 'match'
    ? `전장 ${meters(item.actualMm)}m로, 희망 크기 범위에 들어요.`
    : `전장 ${meters(item.actualMm)}m로, 희망 범위${item.direction === 'shorter' ? '의 최소 길이' : '의 최대 길이'} ${meters(item.direction === 'shorter' ? item.lowerMm : item.upperMm)}m보다 ${meters(item.differenceMm)}m ${item.direction === 'shorter' ? '짧아요' : '길어요'}.`;
  if (item.key === 'seating') text = item.status === 'match'
    ? `등록된 기본 정원 ${item.actual}명으로, 희망하신 ${item.requested}명 이상 조건에 맞아요.`
    : `등록된 기본 정원은 ${item.actual}명으로, 희망하신 ${item.requested}명보다 ${item.difference}명 적어요.`;
  return text ? { ...item, text } : null;
}

export function rankingNarrative(comparison, candidates) {
  if (!comparison || comparison.status === 'unavailable') return '항목별 순위 근거가 제공되지 않아 후보 간 순위 차이를 설명할 수 없어요.';
  if (comparison.status === 'only-candidate') return '현재 표시된 후보가 한 대여서 차량 간 순위 비교는 제공하지 않아요.';
  const higher = candidates.find(item => item.vehicle.id === comparison.higherVehicleId);
  const lower = candidates.find(item => item.vehicle.id === comparison.lowerVehicleId);
  if (!higher || !lower || !Number.isFinite(comparison.scoreDifference)) return '후보 간 순위 근거를 확인할 수 없어요.';
  const pair = `두 차량(${higher.vehicle.model}, ${lower.vehicle.model})`;
  if (comparison.status === 'near-tie') return `${pair}의 가중합 점수 차이는 ${Math.abs(comparison.scoreDifference).toFixed(2)}점으로 비슷한 수준이에요. 1점 미만을 근소한 차이로 표시하며 만족도 차이를 뜻하지 않아요.`;
  const deltas = comparison.contributionDifferences ?? [];
  const positives = deltas.filter(item => item.difference > 0.005).slice(0, 2);
  if (!positives.length) return '항목별 기여도 차이를 확인할 수 없어 순위 차이를 설명하지 않아요.';
  const names = positives.map(item => `${evaluationLabels[item.key] ?? item.key}(+${item.difference.toFixed(2)}점)`).join('·');
  const loss = [...deltas].filter(item => item.difference < -0.005).sort((a, b) => a.difference - b.difference)[0];
  return `${higher.vehicle.model} 차량은 ${lower.vehicle.model}보다 ${names}의 기여도가 높아 앞에 추천됐어요.${loss ? ` 반면 ${evaluationLabels[loss.key] ?? loss.key} 기여도는 ${Math.abs(loss.difference).toFixed(2)}점 낮아요.` : ''} 전체 가중합 차이는 ${comparison.scoreDifference.toFixed(2)}점이에요.`;
}

export function buildRecommendationView(result) {
  const candidates = result.recommendations ?? [];
  return candidates.map(candidate => {
    const evidence = candidate.decisionEvidence;
    const items = (evidence?.preferences ?? []).map(describePreference).filter(Boolean)
      .sort((a, b) => (b.weight ?? 0) - (a.weight ?? 0));
    const financial = evidence?.financial;
    return {
      id: candidate.vehicle.id, candidate, evidence,
      matches: items.filter(item => item.status === 'match'),
      mismatches: items.filter(item => item.status === 'mismatch'),
      unknowns: items.filter(item => item.status === 'unknown'),
      financial,
      rankExplanation: rankingNarrative(candidate.rankingComparison, candidates),
      fuel: fuelName(candidate.vehicle.original_fuel || candidate.vehicle.fuel),
      body: bodyTypeLabel(candidate.vehicle.body_type),
      length: candidate.vehicle.length_mm ? `${meters(candidate.vehicle.length_mm)}m` : '미확인',
      seats: candidate.vehicle.seats ? `${candidate.vehicle.seats}명 (등록 기본 정원)` : candidate.vehicle.seat_options?.length ? `${Math.min(...candidate.vehicle.seat_options)}명부터 (좌석 사양 확인)` : '미확인',
      purchasePrice: candidateMoney(candidate.cost.total_purchase_cost ?? candidate.vehicle.price),
      monthlyCost: candidateMoney(candidate.cost.monthly_running_cost),
      cashRemaining: financial ? candidateMoney(financial.cashAfterPurchase) : '근거 미제공',
      monthlyRemaining: candidateMoney(candidate.cost.remaining_monthly),
    };
  });
}

export function conditionSummary(summary) {
  if (!summary?.complete || !summary.specifiedPreferenceKeys?.length) return null;
  const names = summary.specifiedPreferenceKeys.map(key => ({ body: '차체 형태', fuel: '연료', space: '크기', seating: '정원' })[key]).join('·');
  if (!summary.financiallyEligibleConfigurations) return '현재 불러온 차량 목록에서 구매 자금과 월 유지비 조건을 충족하는 차량이 없어요.';
  if (summary.confirmedMatchingConfigurations > 0) return `재무 조건을 충족한 전체 후보 중 ${names} 선호를 동시에 충족하는 가격 사양은 ${summary.confirmedMatchingConfigurations}개예요. 표시된 순서는 전체 가중합 평가에 따른 결과예요.`;
  return `재무 조건을 충족한 전체 후보에서 등록된 사양으로 ${names} 선호를 동시에 만족하는 차량은 없어요.${summary.unresolvedConfigurations ? ` ${summary.unresolvedConfigurations}개 가격 사양은 제원 부족으로 충족 여부를 확정하지 못했어요.` : ''} 카드에서 맞는 조건과 조정이 필요한 조건을 함께 확인해 주세요.`;
}

export function selectComparisonViews(views, ids) {
  if (!Array.isArray(ids) || ids.length < 2 || ids.length > 3 || new Set(ids).size !== ids.length) return null;
  const selected = ids.map(id => views.find(view => view.id === id));
  return selected.every(Boolean) ? selected : null;
}
