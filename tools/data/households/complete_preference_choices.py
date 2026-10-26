"""Complete every synthetic row after explicit authorization for minimal financial repairs."""
import argparse
import csv
import hashlib
import json
import subprocess
from collections import Counter
from itertools import zip_longest
from pathlib import Path

import numpy as np

from tools.data.households.relabel_preference_choices import (
    ChoicePolicy, EXTRA_FIELDS, FEATURES, OUTPUT as SOURCE, PREFERENCES,
    output_row, verify_selected,
)
from tools.data.households.extend_training_preferences import ROOT, TRAINING_FIELDS, write_csv
from vehicle_matching.catalog import read_catalog

OUTPUT = ROOT / 'data/households/synthetic/preference-complete-v1'
VERSION = 'complete-preference-choice-v1'
REPAIR_FIELDS = ('보정전_월실수령소득_원', '월소득보정액_원', '보정전_구매가격상한_원',
                 '보정전_선택차량_라벨코드', '보정전_선택차량_모델', '보정내용')


def context_from_row(row):
    return {'savings': int(row['월저축액_원']), 'reserve': int(row['비상자금_원']),
            'funds': int(row['구매투입가능자금_원']), 'buffer': int(row['최소월여유자금_원']),
            'ceiling': int(row['구매가격상한_원_0이면미지정'])}


def repair_plan(policy, row):
    """Find a feasible input adjustment before choosing any new output vehicle."""
    context = context_from_row(row)
    score, payment, running, remaining, _ = policy.evaluate(row, context)
    if np.any(np.isfinite(score)):
        return {'income_delta': 0, 'ceiling': context['ceiling']}
    seats = policy.capacity >= int(row[PREFERENCES[3]])
    if not np.any(seats):
        raise ValueError('Catalog cannot support minimum seats; do not invent a vehicle or reduce required seats')
    budget = int(row[FEATURES[0]]) - int(row[FEATURES[2]]) - int(row[FEATURES[3]]) \
        - int(row[FEATURES[5]]) - context['savings'] - context['buffer']
    monthly = payment + running
    price_allowed = policy.price <= context['ceiling'] if context['ceiling'] else np.ones(len(monthly), dtype=bool)
    # If finance is already sufficient, change only a conflicting price ceiling.
    affordable = seats & (monthly <= budget)
    if np.any(affordable):
        minimum_price = int(np.min(policy.price[affordable]))
        return {'income_delta': 0, 'ceiling': max(context['ceiling'], minimum_price) if context['ceiling'] else 0}
    # Prefer preserving a usable original price ceiling when it has seat-compatible cars.
    allowed = seats & price_allowed
    if not np.any(allowed):
        minimum_price = int(np.min(policy.price[seats]))
        ceiling = max(context['ceiling'], minimum_price)
        allowed = seats & (policy.price <= ceiling)
    else:
        ceiling = context['ceiling']
    required = int(np.min(monthly[allowed])) - budget
    # One won avoids a floating-point -0.0 at the exact installment boundary.
    return {'income_delta': max(0, required) + (1 if required > 0 else 0), 'ceiling': ceiling}


def make_group_plans(policy, source_path):
    plans, increases = {}, {}
    with source_path.open(encoding='utf-8-sig', newline='') as stream:
        for row in csv.DictReader(stream):
            plan = repair_plan(policy, row)
            plans[row['프로필_식별자']] = plan
            group = row['재무조건그룹번호']
            increases[group] = max(increases.get(group, 0), plan['income_delta'])
    return plans, increases


def build(source=SOURCE, output=OUTPUT, seed=20261022):
    if subprocess.check_output(['git', 'branch', '--show-current'], cwd=ROOT, text=True).strip() != 'ml/test':
        raise ValueError('Run only on ml/test')
    source, output = Path(source).resolve(), Path(output).resolve()
    if not output.is_relative_to((ROOT / 'data/households/synthetic').resolve()) or output == source or source in output.parents:
        raise ValueError('Use a separate output folder')
    source_path = source / 'combined_training.csv'
    source_hash = hashlib.sha256(source_path.read_bytes()).hexdigest()
    main_ref = subprocess.check_output(['git', 'rev-parse', 'main'], cwd=ROOT, text=True).strip()
    policy = ChoicePolicy(read_catalog(source / 'catalog.json'))
    with (source / 'vehicle_identity_map.csv').open(encoding='utf-8-sig', newline='') as stream:
        labels = {row['차량사양번호']: row['선택차량_라벨코드'] for row in csv.DictReader(stream)}
    plans, increases = make_group_plans(policy, source_path)
    output.mkdir(parents=True, exist_ok=True)
    counters, models, income_changes, examples, changes, example_counts = Counter(), Counter(), [], [], [], Counter()
    schema = (*TRAINING_FIELDS, *EXTRA_FIELDS, *REPAIR_FIELDS)
    # Entire feasibility planning is complete before sampling any new chosen vehicle.
    with source_path.open(encoding='utf-8-sig', newline='') as stream, (output / 'combined_training.csv').open(
            'w', encoding='utf-8-sig', newline='') as destination:
        writer = csv.DictWriter(destination, fieldnames=schema)
        writer.writeheader()
        for original in csv.DictReader(stream):
            row = dict(original)
            identity = row['프로필_식별자']
            delta = increases[row['재무조건그룹번호']]
            before_income = int(row[FEATURES[0]])
            row[FEATURES[0]] = str(before_income + delta)
            context = context_from_row(row)
            # A group-wide income correction may remove the need to relax a price cap.
            final_plan = repair_plan(policy, row)
            if final_plan['income_delta']:
                raise AssertionError('Group repair did not provide sufficient monthly income')
            context['ceiling'] = final_plan['ceiling']
            selected = policy.choose(row, context, seed)
            if selected is None:
                raise AssertionError(f'Incomplete row after repair: {identity}')
            verify_selected(row, context, selected)
            result = output_row(row, context, selected, labels)
            # Preserve the full lineage, including original pre-relabel vehicle labels.
            result['원래선택차량_라벨코드'] = original['원래선택차량_라벨코드']
            result['원래선택차량_모델'] = original['원래선택차량_모델']
            result['결과변경여부'] = '예' if original['원래선택차량_라벨코드'] != result['선택차량_라벨코드'] else '아니오'
            note = []
            if delta:
                note.append('재무그룹공통최소소득보충')
                income_changes.append(delta)
                changes.append({'프로필번호': identity, '변경항목': FEATURES[0], '변경전': before_income,
                                '변경후': before_income + delta, '사유': '원래조건의최소차량월부담부족분보충'})
            old_ceiling = int(original['구매가격상한_원_0이면미지정'])
            if final_plan['ceiling'] != old_ceiling:
                note.append('탑승인원과충돌한가격상한최소확대')
                changes.append({'프로필번호': identity, '변경항목': '구매가격상한_원_0이면미지정',
                                '변경전': old_ceiling, '변경후': final_plan['ceiling'], '사유': '정원과예산조건을함께만족하는최소가격'})
            result.update({
                '보정전_월실수령소득_원': before_income, '월소득보정액_원': delta,
                '보정전_구매가격상한_원': old_ceiling,
                '보정전_선택차량_라벨코드': original['선택차량_라벨코드'],
                '보정전_선택차량_모델': original['선택차량_모델'], '보정내용': ';'.join(note) if note else '입력보정없음',
            })
            preserved = (FEATURES[1:], PREFERENCES)
            for keys in preserved:
                if any(result[key] != original[key] for key in keys):
                    raise AssertionError('Unapproved feature or preference change')
            if set(result) != set(schema) or any(value in ('', None) for value in result.values()):
                raise AssertionError('Missing complete row value')
            writer.writerow(result)
            counters['rows'] += 1
            counters['income_adjusted_rows'] += bool(delta)
            counters['ceiling_adjusted_rows'] += final_plan['ceiling'] != old_ceiling
            counters['previous_no_choice_filled'] += original['선택차량_라벨코드'] == 'NO-CHOICE'
            counters['new_rows'] += identity.startswith('NEW-')
            counters['income_adjustment_exceeds_original_income_rows'] += delta > before_income
            counters['any_input_adjusted_rows'] += bool(delta or final_plan['ceiling'] != old_ceiling)
            counters['previously_selected_input_adjusted_rows'] += bool(delta or final_plan['ceiling'] != old_ceiling) and original['선택차량_라벨코드'] != 'NO-CHOICE'
            models[result['선택차량_모델']] += 1
            example_type = '가격상한조정' if final_plan['ceiling'] != old_ceiling else '소득보정' if delta else '입력유지'
            if example_counts[example_type] < 10:
                examples.append(result)
                example_counts[example_type] += 1
            if counters['rows'] % 20000 == 0:
                print(f'Completed and verified {counters["rows"]} rows', flush=True)
    # Re-read the persisted complete data and compare every unchanged input with its source.
    finance_groups, ids = {}, set()
    with source_path.open(encoding='utf-8-sig', newline='') as before, (output / 'combined_training.csv').open(
            encoding='utf-8-sig', newline='') as after:
        for original, result in zip_longest(csv.DictReader(before), csv.DictReader(after)):
            if original is None or result is None:
                raise AssertionError('Row count changed')
            if result['선택차량_라벨코드'] == 'NO-CHOICE' or any(value == '' for value in result.values()):
                raise AssertionError('Saved complete row contains no recommendation')
            if any(result[key] != original[key] for key in (*FEATURES[1:], *PREFERENCES, '프로필_식별자', '재무조건그룹번호', '데이터_구분')):
                raise AssertionError('Saved inputs or row order changed')
            if result['프로필_식별자'] in ids:
                raise AssertionError('Duplicate row identity')
            ids.add(result['프로필_식별자'])
            group = result['재무조건그룹번호']
            split = '평가' if result['데이터_구분'] == '새선호조합평가' else result['데이터_구분']
            value = (tuple(result[key] for key in FEATURES[:6]), split)
            if group in finance_groups and finance_groups[group] != value:
                raise AssertionError('Finance group inconsistency or split leakage')
            finance_groups[group] = value
    if hashlib.sha256(source_path.read_bytes()).hexdigest() != source_hash:
        raise AssertionError('Source data changed')
    if subprocess.check_output(['git', 'rev-parse', 'main'], cwd=ROOT, text=True).strip() != main_ref:
        raise AssertionError('Main reference changed')
    write_csv(output / 'examples.csv', schema, examples)
    write_csv(output / 'adjustments.csv', ['프로필번호', '변경항목', '변경전', '변경후', '사유'], changes)
    for name in ('catalog.json', 'vehicle_identity_map.csv'):
        (output / name).write_bytes((source / name).read_bytes())
    report = {**counters, 'no_choice_rows': 0, 'missing_cells': 0, 'hard_condition_violations': 0,
              'income_adjusted_groups': sum(value > 0 for value in increases.values()),
              'income_increase_median_won': round(float(np.median(income_changes))) if income_changes else 0,
              'income_increase_max_won': max(income_changes, default=0),
              'four_preferences_unchanged': True, 'all_other_original_model_inputs_unchanged': True,
              'source_unchanged': True, 'main_unchanged': True, 'selected_models': models}
    config = {'version': VERSION, 'seed': seed, 'source_path': str(source), 'source_sha256': source_hash,
              'source_main_ref': main_ref, 'financial_repair_authorization': 'User explicitly selected minimal financial repairs with original values preserved',
              'income_policy': 'Minimum additional monthly income plus one won numeric boundary guard; maximum delta shared by entire original financial group',
              'ceiling_policy': 'Only relax when no feasible candidate; use lowest required price consistent with seats or affordability',
              'preferences': 'Keep all four preferences and minimum seats; do not derive preferences from the selected vehicle',
              'selection_policy': 'preference-consistent-choice-v1; 60 months and annual 6 percent, near-best sampling',
              'future_data_requirement': 'Run feasibility repair planning before choosing any label; fail instead of writing missing labels',
              'exclude_from_training_inputs': list(REPAIR_FIELDS) + ['원래선택차량정보', '선택후차량비용', '점수', '결과변경여부'],
              'limitations': 'Synthetic repairs do not recover real income; large corrections must be inspected. All-selected set excludes real-world no-recommendation behavior.'}
    for name, value in [('validation_report.json', report), ('generation_config.json', config)]:
        (output / name).write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps({k: v for k, v in report.items() if k != 'selected_models'}, ensure_ascii=True))
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=OUTPUT)
    parser.add_argument('--source', type=Path, default=SOURCE)
    parser.add_argument('--seed', type=int, default=20261022)
    args = parser.parse_args()
    build(source=args.source, output=args.output, seed=args.seed)
