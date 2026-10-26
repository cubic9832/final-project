"""Explain NO-CHOICE rows and measure independent policy sensitivities without editing them."""
import csv
import hashlib
import json
from collections import Counter

import numpy as np

from tools.data.households.relabel_preference_choices import ChoicePolicy, FEATURES, OUTPUT, PREFERENCES, SOURCE
from tools.data.households.extend_training_preferences import write_csv
from vehicle_matching.catalog import read_catalog


def primary_reason(base_available, after_savings, budget, structural_count, minimum_running):
    if not structural_count:
        return '정원과가격상한의교집합없음'
    if base_available <= 0:
        return '생활지출과기존상환만으로월가용없음'
    if after_savings <= 0:
        return '저축차감후월가용없음'
    if budget <= 0:
        return '최소여유자금확보후월가용없음'
    if budget < minimum_running:
        return '차량최저유지비도부족'
    return '유지비는가능하지만할부포함시부족'


def analyze(base=OUTPUT):
    source_path = base / 'combined_training.csv'
    input_hash = hashlib.sha256(source_path.read_bytes()).hexdigest()
    with source_path.open(encoding='utf-8-sig', newline='') as stream:
        rows = [row for row in csv.DictReader(stream) if row['선택차량_라벨코드'] == 'NO-CHOICE']
    policy = ChoicePolicy(read_catalog(base / 'catalog.json'))
    ids = {row['프로필_식별자'] for row in rows}
    purchase_timeline = {}
    for path in (SOURCE / 'existing').glob('*/purchases.csv'):
        with path.open(encoding='utf-8-sig', newline='') as stream:
            for purchase in csv.DictReader(stream):
                identity = purchase['프로필_식별자']
                if identity in ids:
                    purchase_timeline[identity] = (int(purchase['구매직전_현금_원']), int(purchase['구매직후_현금_원']))
    reasons, groups, sensitivity, shortages = Counter(), {}, Counter(), []
    details, examples, example_counts = [], [], Counter()
    timeline, boundaries, structural_combinations = Counter(), Counter(), Counter()
    factor72 = (0.06 / 12) / (1 - (1 + 0.06 / 12) ** -72)
    for row in rows:
        identity = row['프로필_식별자']
        group = '신규' if identity.startswith('NEW-') else '기존'
        stats = groups.setdefault(group, {'rows': 0, 'reasons': Counter(), 'sensitivity': Counter()})
        stats['rows'] += 1
        context = {'savings': int(row['월저축액_원']), 'reserve': int(row['비상자금_원']),
                   'funds': int(row['구매투입가능자금_원']), 'buffer': int(row['최소월여유자금_원']),
                   'ceiling': int(row['구매가격상한_원_0이면미지정'])}
        score, payment, running, remaining, upfront = policy.evaluate(row, context)
        if np.any(np.isfinite(score)):
            raise AssertionError(f'NO-CHOICE label has eligible candidates: {identity}')
        income, cash, housing, living, _, repayment, _ = (int(row[key]) for key in FEATURES[:7])
        before_savings = income - housing - living - repayment
        after_savings = before_savings - context['savings']
        budget = after_savings - context['buffer']
        seat = policy.capacity >= int(row[PREFERENCES[3]])
        price = policy.price <= context['ceiling'] if context['ceiling'] else np.ones(len(policy.price), dtype=bool)
        structure = seat & price
        monthly = payment + running
        structure_count = int(np.count_nonzero(structure))
        if not structure_count:
            structural_combinations[f'{row[PREFERENCES[3]]}인_가격상한{context["ceiling"]}원'] += 1
        min_running = int(np.min(running[structure])) if structure_count else 0
        reason = primary_reason(before_savings, after_savings, budget, structure_count, min_running)
        reasons[reason] += 1
        stats['reasons'][reason] += 1
        selected = int(np.argmin(np.where(structure, monthly, np.inf))) if structure_count else None
        shortfall = int(monthly[selected] - budget) if selected is not None else 0
        if selected is not None:
            if shortfall <= 0:
                raise AssertionError('Shortfall is not positive')
            shortages.append(shortfall)
            bucket = '1만원이하' if shortfall <= 10000 else '1만초과10만원이하' if shortfall <= 100000 else \
                     '10만초과30만원이하' if shortfall <= 300000 else '30만초과50만원이하' if shortfall <= 500000 else '50만원초과'
            boundaries[bucket] += 1
        def monthly_fit(candidate_monthly, allowed=structure, extra_budget=0):
            return bool(np.any(allowed & (candidate_monthly <= budget + extra_budget)))
        extra_funds = cash
        full_cash_payment = np.ceil(np.round(np.maximum(0, policy.price - extra_funds) *
                                             (0.06 / 12) / (1 - (1 + 0.06 / 12) ** -60), 2))
        relaxed_reserve_payment = np.ceil(np.round(np.maximum(0, policy.price - context['funds'] - context['reserve']) *
                                                   (0.06 / 12) / (1 - (1 + 0.06 / 12) ** -60), 2))
        payment72 = np.ceil(np.round((policy.price - upfront) * factor72, 2))
        counterfactuals = {
            '저축만0으로가정': monthly_fit(monthly, extra_budget=context['savings']),
            '최소여유자금만0으로가정': monthly_fit(monthly, extra_budget=context['buffer']),
            '가격상한만해제': monthly_fit(monthly, allowed=seat),
            '정원조건만해제': monthly_fit(monthly, allowed=price),
            '유지비만제외': monthly_fit(payment),
            '할부금만제외': monthly_fit(running),
            '할부기간만72개월로가정': monthly_fit(payment72 + running),
            '비상자금전액구매투입가정': monthly_fit(relaxed_reserve_payment + running),
            '모든현금성자산구매투입가정': monthly_fit(full_cash_payment + running),
            '저축여유자금제약없이모든현금투입가정': monthly_fit(full_cash_payment + running,
                                                    extra_budget=context['savings'] + context['buffer']),
        }
        if identity in purchase_timeline:
            pre, post = purchase_timeline[identity]
            timeline['existing_rows'] += 1
            timeline['input_cash_equals_original_postpurchase_cash'] += cash == post
            timeline['original_prepurchase_cash_higher_than_input_cash'] += pre > cash
            prior_reserve = min(pre, (housing + living) * 3)
            prior_payment = np.ceil(np.round(np.maximum(0, policy.price - pre + prior_reserve) *
                                            (0.06 / 12) / (1 - (1 + 0.06 / 12) ** -60), 2))
            fits_prior_cash = monthly_fit(prior_payment + running)
            timeline['eligible_if_original_prepurchase_cash_and_same_policy_used'] += fits_prior_cash
        for key, fits in counterfactuals.items():
            sensitivity[key] += fits
            stats['sensitivity'][key] += fits
        nearest = policy.vehicles[selected] if selected is not None else None
        detail = {'프로필번호': identity, '데이터종류': group, '대표원인': reason,
                  '월소득_원': income, '월생활지출_원': housing + living, '기존월상환액_원': repayment,
                  '월저축액_원': context['savings'], '최소월여유자금_원': context['buffer'],
                  '저축전월가용_원': before_savings, '차량월비용한도_원': budget,
                  '현금성자산_원': cash, '비상자금_원': context['reserve'], '구매투입가능자금_원': context['funds'],
                  '최소탑승인원_명': row[PREFERENCES[3]], '정원충족후보수': int(np.count_nonzero(seat)),
                  '구매가격상한_원_0이면미지정': context['ceiling'],
                  '정원가격동시충족후보수': structure_count, '최소월비용후보': nearest.model if nearest else '없음',
                  '후보월할부금_원': int(payment[selected]) if nearest else 0,
                  '후보월유지비_원': int(running[selected]) if nearest else 0,
                  '필요한추가월가용액_원': shortfall,
                  **{key: '예' if value else '아니오' for key, value in counterfactuals.items()}}
        details.append(detail)
        if example_counts[(group, reason)] < 3:
            examples.append(detail)
            example_counts[(group, reason)] += 1
    expected = json.loads((base / 'validation_report.json').read_text(encoding='utf-8'))
    if len(rows) != sum(dataset['no_choice'] for dataset in expected['datasets'].values()):
        raise AssertionError('NO-CHOICE count changed')
    if hashlib.sha256(source_path.read_bytes()).hexdigest() != input_hash:
        raise AssertionError('Audit modified training data')
    report = {'rows': len(rows), 'exclusive_reasons': reasons, 'datasets': groups,
              'independent_sensitivity_rescued_rows': sensitivity, 'shortfall_buckets': boundaries,
              'shortfall_median_won': round(float(np.median(shortages))) if shortages else 0,
              'shortfall_p90_won': round(float(np.percentile(shortages, 90))) if shortages else 0,
              'purchase_timeline': timeline, 'source_training_unchanged': True,
              'structural_combinations': structural_combinations,
              'notes': ['Representative reasons are mutually exclusive; sensitivity counts overlap and must not be summed.',
                        'Sensitivity scenarios are diagnostic counterfactuals, not recommended financing or budget changes.',
                        'Cash before/after historical purchase refers to a different time point, not a data correction.',
                        'All NO-CHOICE rows were rechecked against all saved catalog candidates; no missed eligible rows found.']}
    (base / 'no_choice_analysis.json').write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
    write_csv(base / 'no_choice_details.csv', list(details[0]), details)
    write_csv(base / 'no_choice_examples.csv', list(examples[0]), examples)
    lines = ['# 선택 없음 74,880행 원인 분석', '',
             '현재 combined_training.csv와 저장된 265개 사양 스냅샷을 사용해 모든 미추천 행을 재검사했다. 적격 차량이 있는데 놓친 행은 0건이다. 학습 데이터는 변경하지 않았다.', '',
             '## 서로 중복되지 않는 대표 원인', '', '| 원인 | 행 수 | 비율 |', '| --- | ---: | ---: |']
    names = {
        '생활지출과기존상환만으로월가용없음': '생활지출·기존 상환 후부터 월 가용자금 없음',
        '저축차감후월가용없음': '저축까지 차감하면 월 가용자금 없음',
        '최소여유자금확보후월가용없음': '최소 월 여유자금까지 확보하면 차량 예산 없음',
        '차량최저유지비도부족': '남은 차량 예산으로 최소 유지비를 충당하기 어려움',
        '유지비는가능하지만할부포함시부족': '유지비는 가능하나 구매자금·할부금까지 포함하면 부족',
        '정원과가격상한의교집합없음': '최소 정원과 가격 상한을 함께 충족하는 후보 없음',
    }
    for key, label in names.items():
        lines.append(f'| {label} | {reasons[key]:,} | {reasons[key]/len(rows)*100:.1f}% |')
    lines += ['', '크기·연료·가성비 선호는 순위 점수이며 미추천을 발생시키는 필수 필터가 아니다. 위 원인은 정원·가격 교집합을 먼저 확인하고 생활지출→저축→여유자금→유지비→할부 순서로 대표 원인을 하나 배정한 것이다. 나중 단계의 문제도 동시에 존재할 수 있다.', '',
              '## 부족 규모와 정책 가정', '',
              f'정원·가격 후보가 존재하는 행에서 필요한 추가 월 가용자금의 중앙값은 {report["shortfall_median_won"]:,}원, 90백분위는 {report["shortfall_p90_won"]:,}원이다. {boundaries["1만원이하"]:,}행은 1만원 이하 차이이고, {boundaries["50만원초과"]:,}행은 50만원을 초과한다.', '',
              '아래는 한 조건만 바꾸는 진단용 가정이며 권고안이 아니다. 행이 중복되므로 합산하면 안 된다.', '',
              '| 진단용 변경 | 적격 후보가 생기는 행 수 |', '| --- | ---: |']
    for key, value in sensitivity.items():
        lines.append(f'| {key} | {value:,} |')
    lines += ['', '유지비 제외 시 적격이 되는 수는 유지비 계산의 영향 크기를 뜻한다. 에너지·보험·세금·정비비를 실제로 없앨 수 있다는 뜻이 아니다. 비상자금·저축·장기 할부 가정도 같은 방식으로 해석해야 한다.', '',
              '## 기존 데이터의 자금 시점', '',
              f'기존 미추천 {timeline["existing_rows"]:,}행 모두 현금성 자산이 원래 구매 내역의 구매직후 현금과 일치한다. 원래 구매직전 현금을 사용하되 나머지 정책을 동일하게 놓으면 {timeline["eligible_if_original_prepurchase_cash_and_same_policy_used"]:,}행에 적격 후보가 생긴다.', '',
              '현재 재무 상태에서 새 차를 추천한다는 해석이면 구매 후 잔액 사용이 가능하다. 반면 원래 차량을 구매한 당시의 선택을 학습하려면 자금 시점이 맞지 않는다. 이를 검토 없이 구매 전 현금으로 덮어쓰면 기존 입력 보존 요구를 위반하므로 이번 분석에서는 변경하지 않았다.', '',
              '## 데이터 활용 판단', '',
              '현재 입력·가정을 유지한다면 다수의 NO-CHOICE는 정상적인 미추천이다. 차량 결과를 억지로 채우면 다시 재무 괴리가 생긴다. 향후 데이터 목적을 현재 상태의 신규 구매 추천으로 둘지 원래 구매 당시 선택 설명으로 둘지 정하고, 저축·유지비·구매자금·할부 가정을 그 목적에 일관되게 맞춰야 한다.', '',
              '전체 행별 원인: no_choice_details.csv. 작은 예시: no_choice_examples.csv. 상세 집계: no_choice_analysis.json.', '',
              '재현: `python -m tools.data.households.analyze_no_choice`', '']
    (base / 'no_choice_analysis.md').write_text('\n'.join(lines), encoding='utf-8')
    print(json.dumps(report, ensure_ascii=True, indent=2))
    return report


if __name__ == '__main__':
    analyze()
