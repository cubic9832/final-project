"""Independent scalar finance and preference-quality audit of the completed synthetic table."""
import csv
import hashlib
import json
from collections import Counter
from decimal import Decimal, ROUND_CEILING, ROUND_HALF_EVEN, localcontext
from itertools import zip_longest
from pathlib import Path

import numpy as np

from tools.data.households.complete_preference_choices import OUTPUT
from tools.data.households.extend_training_preferences import FEATURES, PREFERENCES, ROOT, FUEL_LABELS, write_csv
from tools.data.households.relabel_preference_choices import ChoicePolicy
from vehicle_matching.catalog import read_catalog
from vehicle_matching.finance import Assumptions
from vehicle_matching.preferences import SIZE_BANDS


def cents_then_ceil(value):
    return int(value.quantize(Decimal('0.01'), rounding=ROUND_HALF_EVEN).to_integral_value(rounding=ROUND_CEILING))


def independent_cost(row, vehicle):
    """Use decimal arithmetic, not the generator's numpy or finance.assess implementation."""
    assumptions = Assumptions()
    fuels = ('GASOLINE', 'HYBRID', 'DIESEL', 'LPG', 'ELECTRIC')
    index = fuels.index(vehicle.fuel)
    with localcontext() as context:
        context.prec = 40
        price = Decimal(str(vehicle.price))
        funds = Decimal(row['구매투입가능자금_원'])
        upfront = min(price, funds)
        principal = price - upfront
        monthly_rate = Decimal(row['가정연금리_퍼센트']) / 100 / 12
        months = int(row['가정할부기간_개월'])
        payment = principal / months if not monthly_rate else principal * monthly_rate / (1 - (1 + monthly_rate) ** -months)
        efficiency = Decimal(str(vehicle.efficiency)) if vehicle.efficiency else sum(
            Decimal(str(x)) for x in assumptions.efficiency_ranges[index]) / 2
        energy = Decimal(row[FEATURES[6]]) / 12 / efficiency * Decimal(str(assumptions.energy_prices[index]))
        fixed = Decimal(str(assumptions.monthly_insurance + assumptions.monthly_maintenance + assumptions.monthly_tax))
        return int(upfront), cents_then_ceil(payment), cents_then_ceil(energy + fixed)


def write_quality_report(base, report):
    counts, pref = report['independent_checks'], report['preference_alignment']
    def percentage(number, denominator):
        return f'{number/denominator*100:.1f}%' if denominator else '해당없음'
    text = f'''# 완성본 206,156행 독립 품질 점검

## 판정

저장된 비용 가정·정원·가격 상한은 전부 충족한다. 하지만 **전체 결과가 선호와 큰 괴리 없이 맞는다고 결론 내릴 수는 없다.** 모든 행에 차량을 붙이기 위한 최소 소득 보정이 예산 경계에 사례를 몰아넣었고, 선호 불일치와 차량 분포 편향이 남았다. 이전의 ‘선택 없음·조건 위반 0건’은 이 의미상 품질을 보장하지 않는다.

## 독립 계산 및 입력 보존

206,156행 전부를 검사했다. 생성기의 numpy 계산이나 finance.assess 대신 Decimal 산술로 선택 차량의 선수금·할부금·유지비를 다시 계산했다. 원본과 수정본을 같은 순서로 읽어 변경하지 않기로 한 입력을 전수 대조했다.

| 항목 | 위반 또는 오류 |
| --- | ---: |
| 차량 식별·모델·트림·라벨 연결 | {counts['vehicle_identity_mismatch']:,} |
| 차량 가격 | {counts['price_mismatch']:,} |
| 정원 | {counts['seat_violation']:,} |
| 월 비용 차감 후 여유자금 하한 | {counts['decimal_financial_violation']:,} |
| 가격 상한 | {counts['price_ceiling_violation']:,} |
| 비상자금 보존 후 현금 초과 사용 | {counts['purchase_funds_exceed_cash_after_reserve']:,} |
| Decimal과 생성기 비용 차이 | {counts['decimal_vs_float_cost_discrepancy']:,} |
| 선택 차량의 최고 점수 대비 2.5점 초과 손실 | {counts['score_regret_over_2_5_points']:,} |
| 의도하지 않은 원래 입력 변경 | {counts['unexpected_input_changes']:,} |
| 같은 재무 그룹 정보·분할 불일치 | {counts['group_finance_or_split_mismatch']:,} |

점수 검사는 선언한 기존 점수 정책을 기준으로 한 검사다. 선호·현실의 만족도를 별도로 입증하는 지표가 아니다. 정원은 등록 자료 기준이며 모두 제조사 검증값이라는 뜻은 아니다.

## 남아 있는 괴리

| 항목 | 결과 |
| --- | --- |
| 명시한 연료 선호와 다름 | {pref['fuel_mismatch']:,}/{pref['explicit_fuel_rows']:,}행, {percentage(pref['fuel_mismatch'],pref['explicit_fuel_rows'])} |
| 확인 가능한 전장 기준 크기 선호와 다름 | {pref['size_mismatch']:,}/{pref['known_size_rows']:,}행, {percentage(pref['size_mismatch'],pref['known_size_rows'])} |
| 연료·크기 모두 선호와 다름 | {pref['both_mismatch']:,}행 |
| 크기 선호 범위와 전장 1m 이상 차이 | {pref['size_gap_at_least_1000_mm']:,}행 |
| 두 선호를 함께 맞추는 적격 후보가 있으나 다른 후보 선택 | {pref['both_match_available_but_not_selected']:,}행 |

선호는 필수 조건이 아니어서 불일치를 모두 잘못된 결과로 볼 수는 없다. 마지막 항목에는 비용·용도 절충과 근접 점수 후보 추첨이 포함된다. 다만 모든 행에 차량이 있다는 이유로 선호가 충분히 반영됐다고 설명하면 안 된다.

## 원인

1. 최소 여유자금 하한을 초과하는 금액이 **1원 이하인 행이 {counts['buffer_margin_at_most_one_won']:,}개**다. 소득 보정 행 대부분이 가장 저비용인 후보를 겨우 감당하는 경계에 있다. 형식적으로는 통과하지만, 후보 다양성과 선호 반영 여지가 작다. 이는 보정을 최소화하는 규칙의 직접적인 결과다.
2. 소득 보충액이 원래 소득의 절반을 넘는 행은 {counts['income_repair_over_50_percent']:,}개, 원래 소득 자체보다 큰 행은 {counts['income_repair_over_100_percent']:,}개다. ‘최소 보정’은 원래 분포와 차이가 작다는 뜻이 아니다.
3. 수입 후보 사양 {report['imported_catalog_candidates']}개 중 전장 확인값이 있는 사양은 {report['imported_catalog_candidates_with_known_length']}개다. 현재 점수에서 전장 미확인은 크기 점수 0을 받는다. 실제 수입차 선택은 {counts['imported_selected_rows']:,}행으로, 입력 자료 충실도와 점수 정책에 따른 불리함을 포함한다. 수입차가 현실적으로 모두 부적합하다고 해석하면 안 된다.
4. {report['catalog_models']}개 모델 표기 중 {report['selected_model_count']}개만 선택됐고, 최다 모델 모닝은 {report['top_10_models'][0][1]:,}행({report['top_model_share_percent']}%)이다. 실제 시장 비율이 아니다. 신규 동일 입력 그룹 중 여러 모델이 선택된 그룹은 {report['same_input_groups_with_multiple_models']:,}개여서 다양성이 완전히 사라진 것은 아니다.

## 판단과 후속 방향

이 데이터는 **정해진 정책을 만족하는 합성 학습 실험용 완성본**으로는 사용할 수 있지만, 선호 적합성이 충분히 검증된 정답으로 확정하기에는 보완이 필요하다. 개선할 때는 원래 입력을 보존한 기준선과 분리해, 선호를 고려한 후보 집합 안에서 재무 보정을 계획하고 적정 여유 폭을 확보하는 규칙을 검토해야 한다. 다만 그러면 보정액이 더 커질 수 있으므로 보정 규모 상한과 함께 설계해야 한다. 수입차 등 제원 미확인 후보의 불이익도 별도 해결이 필요하다.

이번 요청은 검증이므로 데이터·선호·점수·재무 보정은 추가 변경하지 않았다. 전체 JSON: complete_quality_audit.json. 점검별 소규모 예시: complete_quality_examples.csv.

재현: `python -m tools.data.households.audit_complete_choices`
'''
    (Path(base)/'complete_quality_audit.md').write_text(text,encoding='utf-8')


def audit(base=OUTPUT):
    base = Path(base)
    path = base / 'combined_training.csv'
    before_hash = hashlib.sha256(path.read_bytes()).hexdigest()
    config = json.loads((base / 'generation_config.json').read_text(encoding='utf-8'))
    source = Path(config['source_path']) / 'combined_training.csv'
    vehicles = read_catalog(base / 'catalog.json')
    lookup = {v.id: v for v in vehicles}
    policy = ChoicePolicy(vehicles)
    indexes = {v.id: index for index, v in enumerate(policy.vehicles)}
    labels = {}
    with (base / 'vehicle_identity_map.csv').open(encoding='utf-8-sig', newline='') as stream:
        labels = {r['차량사양번호']: r['선택차량_라벨코드'] for r in csv.DictReader(stream)}
    with (ROOT / 'data/seed/imported-car/owners.csv').open(encoding='utf-8-sig', newline='') as stream:
        imported_brands = {r['보유차량_브랜드'] for r in csv.DictReader(stream)}
    counts, preference, segments, model_counts = Counter(), Counter(), {}, Counter()
    evidence, evidence_counts, margins, repairs, groups, identities, repeat_models = [], Counter(), [], [], {}, set(), {}
    with path.open(encoding='utf-8-sig', newline='') as stream, source.open(encoding='utf-8-sig', newline='') as original:
        for row, previous in zip_longest(csv.DictReader(stream), csv.DictReader(original)):
            if row is None or previous is None:
                raise AssertionError('Source and completed row counts differ')
            counts['rows'] += 1
            issues = []
            def flag(condition, name):
                if condition:
                    counts[name] += 1
                    issues.append(name)
            identity = row['프로필_식별자']
            flag(identity in identities, 'duplicate_ids')
            identities.add(identity)
            flag(any(v == '' for v in row.values()), 'missing_cells_rows')
            flag(any(row[k] != previous[k] for k in (*FEATURES[1:], *PREFERENCES, '프로필_식별자', '재무조건그룹번호', '데이터_구분')), 'unexpected_input_changes')
            vehicle = lookup.get(row['선택차량사양번호'])
            if vehicle is None:
                flag(True, 'missing_or_unknown_vehicle')
                continue
            flag((row['선택차량_브랜드'], row['선택차량_모델'], row['선택트림'], row['선택차량_라벨코드']) !=
                 (vehicle.brand, vehicle.model, vehicle.trim, labels[vehicle.id]), 'vehicle_identity_mismatch')
            flag(int(row['선택차량가격_원']) != round(vehicle.price), 'price_mismatch')
            flag(row['선택차량연료'] != FUEL_LABELS[vehicle.fuel], 'fuel_metadata_mismatch')
            capacity = vehicle.seats if vehicle.seats is not None else min(vehicle.seat_options) if vehicle.seat_options else 0
            flag(capacity < int(row[PREFERENCES[3]]), 'seat_violation')
            upfront, payment, running = independent_cost(row, vehicle)
            flag(int(row['초기지급액_원']) != upfront, 'upfront_calculation_mismatch')
            discrepancy = max(abs(payment-int(row['월할부금_원'])), abs(running-int(row['월유지비_원'])))
            flag(discrepancy > 0, 'decimal_vs_float_cost_discrepancy')
            flag(discrepancy > 1, 'cost_discrepancy_over_one_won')
            available = int(row[FEATURES[0]]) - int(row[FEATURES[2]]) - int(row[FEATURES[3]]) - int(row[FEATURES[5]]) - int(row['월저축액_원'])
            remaining = available - payment - running
            flag(abs(remaining - int(row['차량비용차감후월잔여액_원'])) > 1, 'remaining_calculation_mismatch_over_one_won')
            buffer = int(row['최소월여유자금_원'])
            flag(remaining < buffer, 'decimal_financial_violation')
            flag(int(row['구매투입가능자금_원']) + int(row['비상자금_원']) > int(row[FEATURES[1]]), 'purchase_funds_exceed_cash_after_reserve')
            ceiling = int(row['구매가격상한_원_0이면미지정'])
            flag(bool(ceiling) and vehicle.price > ceiling, 'price_ceiling_violation')
            margin = remaining - buffer
            margins.append(margin)
            counts['buffer_margin_at_most_one_won'] += margin <= 1
            counts['buffer_margin_at_most_10000_won'] += margin <= 10000
            delta = int(row['월소득보정액_원'])
            old_income = int(row['보정전_월실수령소득_원'])
            flag(int(row[FEATURES[0]]) != old_income + delta or old_income != int(previous[FEATURES[0]]), 'income_correction_mismatch')
            counts['income_repair_over_50_percent'] += delta > old_income * .5
            counts['income_repair_over_100_percent'] += delta > old_income
            if delta:
                repairs.append(delta)
            context = {'savings': int(row['월저축액_원']), 'reserve': int(row['비상자금_원']),
                       'funds': int(row['구매투입가능자금_원']), 'buffer': buffer, 'ceiling': ceiling}
            score, _, _, _, _ = policy.evaluate(row, context)
            index = indexes[vehicle.id]
            flag(not np.isfinite(score[index]), 'selected_not_eligible_in_catalog_policy')
            best = float(np.max(score))
            flag(best - score[index] > .025 + 1e-10, 'score_regret_over_2_5_points')
            flag(abs(round(float(score[index])*10000) - int(row['선택점수_만점10000'])) > 1, 'score_record_mismatch')
            preferred_fuel = row[PREFERENCES[2]]
            fuel_bad = preferred_fuel != '상관없음' and preferred_fuel != FUEL_LABELS[vehicle.fuel]
            size = {'작음': 'small', '중간': 'medium', '큼': 'large'}[row[PREFERENCES[1]]]
            low, high = SIZE_BANDS[size]
            size_bad = bool(vehicle.length_mm) and not low <= vehicle.length_mm <= high
            preference['explicit_fuel_rows'] += preferred_fuel != '상관없음'
            preference['fuel_mismatch'] += fuel_bad
            preference['known_size_rows'] += vehicle.length_mm is not None
            preference['size_mismatch'] += size_bad
            preference['both_mismatch'] += fuel_bad and size_bad
            preference['size_gap_at_least_1000_mm'] += bool(vehicle.length_mm) and max(low-vehicle.length_mm, vehicle.length_mm-high, 0) >= 1000
            eligible = np.isfinite(score)
            size_match = policy.size_scores[size] == 1
            fuel_match = np.array([FUEL_LABELS[v.fuel] == preferred_fuel for v in policy.vehicles]) if preferred_fuel != '상관없음' else np.ones(len(score),dtype=bool)
            both_available = bool(np.any(eligible & size_match & fuel_match))
            preference['both_match_available'] += both_available
            preference['both_match_available_but_not_selected'] += both_available and (fuel_bad or size_bad)
            model_counts[vehicle.model] += 1
            counts['imported_selected_rows'] += vehicle.brand in imported_brands
            segment = segments.setdefault('소득보정' if delta else '소득유지', Counter())
            segment['rows'] += 1
            segment['fuel_mismatch'] += fuel_bad
            segment['size_mismatch'] += size_bad
            segment['both_mismatch'] += fuel_bad and size_bad
            segment['margin_at_most_one_won'] += margin <= 1
            finance = tuple(row[k] for k in FEATURES[:6])
            split = '평가' if row['데이터_구분']=='새선호조합평가' else row['데이터_구분']
            group = row['재무조건그룹번호']
            flag(group in groups and groups[group] != (finance,split), 'group_finance_or_split_mismatch')
            groups[group] = (finance,split)
            if identity.startswith('NEW-'):
                repeat_models.setdefault(identity.rsplit('-R',1)[0],set()).add(vehicle.model)
            if delta > old_income:
                issues.append('소득보충액이원래소득보다큼')
            if margin <= 1:
                issues.append('월여유자금경계1원이하')
            if fuel_bad and size_bad:
                issues.append('연료크기둘다선호와다름')
            if both_available and (fuel_bad or size_bad):
                issues.append('두선호충족후보있지만비용용도절충')
            for issue in issues:
                if evidence_counts[issue] < 3:
                    evidence.append({'점검항목': issue, '프로필번호': identity, '선택차량': vehicle.model,
                                     '선호연료': preferred_fuel, '실제연료': FUEL_LABELS[vehicle.fuel], '선호크기': row[PREFERENCES[1]],
                                     '실제전장_mm': vehicle.length_mm or 0, '월소득_원': row[FEATURES[0]],
                                     '보정전월소득_원': old_income, '월소득보정액_원': delta,
                                     '최소월여유자금초과액_원': margin, '선택설명': row['선택설명']})
                    evidence_counts[issue] += 1
            if counts['rows'] % 40000 == 0:
                print(f'Audited {counts["rows"]} rows',flush=True)
    zeros = ('missing_or_unknown_vehicle','missing_cells_rows','duplicate_ids','unexpected_input_changes',
             'vehicle_identity_mismatch','price_mismatch','seat_violation','decimal_financial_violation',
             'price_ceiling_violation','purchase_funds_exceed_cash_after_reserve','cost_discrepancy_over_one_won',
             'score_regret_over_2_5_points','group_finance_or_split_mismatch','decimal_vs_float_cost_discrepancy',
             'upfront_calculation_mismatch','remaining_calculation_mismatch_over_one_won',
             'income_correction_mismatch','score_record_mismatch','fuel_metadata_mismatch')
    for key in zeros:
        counts.setdefault(key,0)
    if hashlib.sha256(path.read_bytes()).hexdigest() != before_hash:
        raise AssertionError('Audit changed the input data')
    report = {'independent_checks': counts, 'preference_alignment': preference, 'segments':segments,
              'top_10_models': model_counts.most_common(10), 'selected_model_count':len(model_counts),
              'top_model_share_percent': round(model_counts.most_common(1)[0][1]/counts['rows']*100,2),
              'catalog_models':len({(v.brand,v.model) for v in vehicles}),
              'imported_catalog_candidates':sum(v.brand in imported_brands for v in vehicles),
              'imported_catalog_candidates_with_known_length':sum(v.brand in imported_brands and v.length_mm is not None for v in vehicles),
              'same_input_groups_with_multiple_models':sum(len(values)>1 for values in repeat_models.values()),
              'income_increase_median_won':round(float(np.median(repairs))),
              'buffer_excess_median_won':round(float(np.median(margins))),
              'data_unchanged':True,
              'limits':['Hard compliance is under saved catalog and cost assumptions, not observed purchase outcomes.',
                        'Ranking-regret validation uses the declared scoring policy; decimal finance is independently recomputed.',
                        'A preference mismatch is a tradeoff, not automatically a hard-condition violation.',
                        'Large income repairs, narrow affordability margins and unknown imported sizes remain quality limitations.']}
    (base/'complete_quality_audit.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    if evidence:
        write_csv(base/'complete_quality_examples.csv',list(evidence[0]),evidence)
    write_quality_report(base,report)
    print(json.dumps(report,ensure_ascii=True,indent=2))
    return report


if __name__=='__main__':
    audit()
