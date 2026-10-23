"""Relabel synthetic vehicle choices while preserving all pre-existing input values."""
import argparse
import csv
import hashlib
import json
import math
import random
import subprocess
from collections import Counter
from dataclasses import asdict
from pathlib import Path

import numpy as np

from tools.data.households.extend_training_preferences import (
    FEATURES, PREFERENCES, ROOT, TRAINING_FIELDS, FUEL_LABELS, generate, load_candidates,
    model_registry, read_csv, write_csv,
)
from vehicle_matching.finance import Assumptions, Profile, assess
from vehicle_matching.preferences import SIZE_BANDS, exclusions

SOURCE = ROOT / 'data/households/synthetic/preference-extended-v1'
OUTPUT = ROOT / 'data/households/synthetic/preference-relabelled-v1'
VERSION = 'preference-consistent-choice-v1'
NEAR_BEST = 0.025
EXTRA_FIELDS = (
    '원래선택차량_라벨코드', '원래선택차량_모델', '결과변경여부', '선택차량사양번호',
    '선택트림', '선택차량가격_원', '선택차량연료', '선택차량전장_mm_0이면미확인',
    '월저축액_원', '비상자금_원', '구매투입가능자금_원', '최소월여유자금_원',
    '구매가격상한_원_0이면미지정', '가정할부기간_개월', '가정연금리_퍼센트',
    '초기지급액_원', '월할부금_원', '월유지비_원', '차량비용차감후월잔여액_원',
    '선택점수_만점10000', '최고점수_만점10000', '선택가능모델수', '선택설명',
    '연료선호충족후보존재', '크기선호충족후보존재', '두선호동시충족후보존재',
)


class ChoicePolicy:
    def __init__(self, vehicles):
        # Sorted contiguous model groups permit vectorized reduction across trims.
        self.vehicles = sorted(vehicles, key=lambda v: (v.brand, v.model, v.id))
        self.starts = np.asarray([i for i, v in enumerate(self.vehicles)
                                  if i == 0 or (v.brand, v.model) !=
                                  (self.vehicles[i-1].brand, self.vehicles[i-1].model)])
        self.ends = np.append(self.starts[1:], len(self.vehicles))
        self.price = np.array([v.price for v in self.vehicles])
        self.length = np.array([v.length_mm or 0 for v in self.vehicles])
        self.fuel = np.array([v.fuel for v in self.vehicles])
        self.capacity = np.array([v.seats if v.seats is not None else min(v.seat_options)
                                  if v.seat_options else 0 for v in self.vehicles])
        assumptions = Assumptions()
        fuel_names = ('GASOLINE', 'HYBRID', 'DIESEL', 'LPG', 'ELECTRIC')
        self.energy_per_km = np.array([
            assumptions.energy_prices[fuel_names.index(v.fuel)] /
            (v.efficiency or sum(assumptions.efficiency_ranges[fuel_names.index(v.fuel)]) / 2)
            for v in self.vehicles])
        self.fixed = assumptions.monthly_insurance + assumptions.monthly_maintenance + assumptions.monthly_tax
        self.size_scores = {}
        for size, (low, high) in SIZE_BANDS.items():
            distance = np.maximum(np.maximum(low - self.length, self.length - high), 0)
            self.size_scores[size] = np.where(self.length > 0, np.maximum(0, 1 - distance / 1000), 0)

    def evaluate(self, row, context):
        income, _, housing, living, _, repayment, distance = (int(row[key]) for key in FEATURES[:7])
        available = income - housing - living - repayment - context['savings']
        upfront = np.minimum(context['funds'], self.price)
        principal = self.price - upfront
        rate, months = 0.06, 60
        factor = (rate / 12) / (1 - (1 + rate / 12) ** -months)
        payment = np.ceil(np.round(principal * factor, 2)).astype(np.int64)
        running = np.ceil(np.round(distance / 12 * self.energy_per_km + self.fixed, 2)).astype(np.int64)
        remaining = available - payment - running
        eligible = (remaining >= context['buffer']) & (self.capacity >= int(row[PREFERENCES[3]]))
        if context['ceiling']:
            eligible &= self.price <= context['ceiling']
        total = self.price + running * 60 + principal * (factor * 60 - 1)
        budget = max(1, available * 60 + int(row[FEATURES[1]]) - context['reserve'])
        economy = np.clip(1 - total / budget, 0, 1)
        size = {'작음': 'small', '중간': 'medium', '큼': 'large'}[row[PREFERENCES[1]]]
        preferred = next((key for key, value in FUEL_LABELS.items() if value == row[PREFERENCES[2]]), None)
        fuel_score = (self.fuel == preferred).astype(float) if preferred else np.full(len(self.vehicles), 0.5)
        target = {'출퇴근': 4100, '가족이동': 4750, '여가': 4900, '업무': 4600}[row[FEATURES[7]]]
        purpose = np.where(self.length > 0, np.maximum(0, 1 - np.abs(self.length - target) / 1500), 0)
        cost_weight = int(row[PREFERENCES[0]])
        score = (cost_weight * economy + 3 * self.size_scores[size] + 3 * fuel_score + purpose) / (cost_weight + 7)
        score = np.where(eligible, score, -np.inf)
        return score, payment, running, remaining, upfront

    def choose(self, row, context, seed):
        score, payment, running, remaining, upfront = self.evaluate(row, context)
        model_scores = np.maximum.reduceat(score, self.starts)
        feasible = np.flatnonzero(np.isfinite(model_scores))
        if not len(feasible):
            return None
        best = float(np.max(model_scores))
        shortlist = feasible[model_scores[feasible] >= best - NEAR_BEST]
        weights = np.exp((model_scores[shortlist] - best) / 0.015)
        rng = random.Random(hashlib.sha256(f'{seed}:{row["프로필_식별자"]}'.encode()).hexdigest())
        model = rng.choices(shortlist.tolist(), weights=weights.tolist())[0]
        start, end = self.starts[model], self.ends[model]
        index = int(start + np.argmax(score[start:end]))
        size = {'작음': 'small', '중간': 'medium', '큼': 'large'}[row[PREFERENCES[1]]]
        exact_size = self.size_scores[size] == 1
        exact_fuel = np.array([FUEL_LABELS[v.fuel] == row[PREFERENCES[2]]
                               for v in self.vehicles]) if row[PREFERENCES[2]] != '상관없음' else np.ones(len(score), dtype=bool)
        eligible = np.isfinite(score)
        return {'vehicle': self.vehicles[index], 'score': float(score[index]), 'best': best,
                'payment': int(payment[index]), 'running': int(running[index]),
                'remaining': int(remaining[index]), 'upfront': round(float(upfront[index])),
                'eligible_models': len(feasible),
                'fuel_available': bool(np.any(eligible & exact_fuel)),
                'size_available': bool(np.any(eligible & exact_size)),
                'both_available': bool(np.any(eligible & exact_fuel & exact_size))}


def legacy_contexts(source):
    result = {}
    for segment in ('domestic-car', 'imported-car', 'domestic-extra-90000', 'imported-extra-90000'):
        with (source / 'existing' / segment / 'owners.csv').open(encoding='utf-8-sig', newline='') as stream:
            for row in csv.DictReader(stream):
                # Existing inputs remain unchanged; only new scenario fields are derived.
                expenses = int(row[FEATURES[2]]) + int(row[FEATURES[3]])
                reserve = min(int(row[FEATURES[1]]), expenses * 3)
                result[row['프로필_식별자']] = {
                    'savings': int(row['개인_평균월저축액_원']), 'reserve': reserve,
                    'funds': int(row[FEATURES[1]]) - reserve,
                    'buffer': 0, 'ceiling': 0,
                }
    return result


def output_row(row, context, selected, labels):
    result = dict(row)
    old_label, old_model = row['선택차량_라벨코드'], row['선택차량_모델']
    vehicle = selected['vehicle'] if selected else None
    result.update({'선택차량_라벨코드': labels[vehicle.id] if vehicle else 'NO-CHOICE',
                   '선택차량_브랜드': vehicle.brand if vehicle else '해당없음',
                   '선택차량_모델': vehicle.model if vehicle else '선택없음',
                   '선택상태': '선호기반재선택' if vehicle else '조건충족후보없음'})
    result.update(dict(zip(EXTRA_FIELDS[:2], (old_label, old_model))))
    explanation = ['적격후보중최고점수와250점이내모델에서추첨']
    if vehicle and row[PREFERENCES[2]] != '상관없음' and row[PREFERENCES[2]] != FUEL_LABELS[vehicle.fuel]:
        explanation.append('연료는비용크기와절충' if selected['fuel_available'] else '선호연료적격후보없음')
    if vehicle and vehicle.length_mm:
        low, high = SIZE_BANDS[{'작음': 'small', '중간': 'medium', '큼': 'large'}[row[PREFERENCES[1]]]]
        if not low <= vehicle.length_mm <= high:
            explanation.append('크기는비용연료와절충' if selected['size_available'] else '선호크기적격후보없음')
    result.update({
        '결과변경여부': '예' if old_label != result['선택차량_라벨코드'] else '아니오',
        '선택차량사양번호': vehicle.id if vehicle else 'NO-CHOICE', '선택트림': vehicle.trim if vehicle else '해당없음',
        '선택차량가격_원': round(vehicle.price) if vehicle else 0,
        '선택차량연료': FUEL_LABELS[vehicle.fuel] if vehicle else '해당없음',
        '선택차량전장_mm_0이면미확인': vehicle.length_mm or 0 if vehicle else 0,
        '월저축액_원': context['savings'], '비상자금_원': context['reserve'],
        '구매투입가능자금_원': context['funds'], '최소월여유자금_원': context['buffer'],
        '구매가격상한_원_0이면미지정': context['ceiling'], '가정할부기간_개월': 60, '가정연금리_퍼센트': 6,
        '초기지급액_원': selected['upfront'] if selected else 0,
        '월할부금_원': selected['payment'] if selected else 0,
        '월유지비_원': selected['running'] if selected else 0,
        '차량비용차감후월잔여액_원': selected['remaining'] if selected else int(row[FEATURES[0]]) -
        int(row[FEATURES[2]]) - int(row[FEATURES[3]]) - int(row[FEATURES[5]]) - context['savings'],
        '선택점수_만점10000': round(selected['score'] * 10000) if selected else 0,
        '최고점수_만점10000': round(selected['best'] * 10000) if selected else 0,
        '선택가능모델수': selected['eligible_models'] if selected else 0,
        '선택설명': ';'.join(explanation) if selected else '월부담또는정원가격조건충족후보없음',
        '연료선호충족후보존재': ('예' if selected['fuel_available'] else '아니오') if selected else '해당없음',
        '크기선호충족후보존재': ('예' if selected['size_available'] else '아니오') if selected else '해당없음',
        '두선호동시충족후보존재': ('예' if selected['both_available'] else '아니오') if selected else '해당없음',
    })
    return result


def verify_selected(row, context, selected):
    if not selected:
        return
    vehicle = selected['vehicle']
    # Independent scalar implementation verifies vectorized monthly finance and seat policy.
    profile = Profile(monthly_income=int(row[FEATURES[0]]), monthly_expenses=int(row[FEATURES[2]]) + int(row[FEATURES[3]]),
                      existing_monthly_payment=int(row[FEATURES[5]]), liquid_assets=int(row[FEATURES[1]]),
                      down_payment=min(context['funds'], vehicle.price), emergency_reserve=context['reserve'],
                      monthly_savings=context['savings'], annual_distance=int(row[FEATURES[6]]), months=60,
                      annual_rate=0.06, minimum_buffer=context['buffer'], charging_available=True,
                      minimum_seats=int(row[PREFERENCES[3]]), preferred_size='any')
    cost = assess(profile, vehicle)
    if (not cost['eligible'] or exclusions(profile, vehicle)
            or selected['remaining'] < context['buffer']
            or math.ceil(cost['monthly_payment']) != selected['payment']
            or math.ceil(cost['monthly_running_cost']) != selected['running']
            or (context['ceiling'] and vehicle.price > context['ceiling'])
            or selected['best'] - selected['score'] > NEAR_BEST + 1e-10):
        raise AssertionError(f'Inconsistent selected vehicle: {row["프로필_식별자"]}')


def summarize_results(source=SOURCE, output=OUTPUT):
    """Compare preferences on the same selected rows, rather than changing denominators."""
    source, output = Path(source), Path(output)
    old_fuels = {}
    for path in (source / 'existing').glob('*/purchases.csv'):
        with path.open(encoding='utf-8-sig', newline='') as stream:
            for row in csv.DictReader(stream):
                fuel = FUEL_LABELS.get(row['연료'])
                if not row['연료'] and row['구매_모델'] == '모닝':
                    fuel = '가솔린'
                old_fuels[row['프로필_식별자']] = fuel
    vehicles = load_candidates()
    lengths = {}
    for v in vehicles:
        if v.length_mm:
            lengths.setdefault(v.model, set()).add(v.length_mm)
    paired, selected_by_group, mismatch_reasons = Counter(), {}, Counter()
    with (output / 'combined_training.csv').open(encoding='utf-8-sig', newline='') as stream:
        for row in csv.DictReader(stream):
            if row['선택차량_라벨코드'] == 'NO-CHOICE':
                continue
            if row['프로필_식별자'].startswith('NEW-'):
                identity = row['프로필_식별자'].rsplit('-R', 1)[0]
                selected_by_group.setdefault(identity, set()).add(row['선택차량_라벨코드'])
            else:
                old_fuel = old_fuels[row['프로필_식별자']]
                pref = row[PREFERENCES[2]]
                if old_fuel and pref != '상관없음':
                    paired['fuel_same_rows'] += 1
                    paired['fuel_before_mismatch'] += pref != old_fuel
                    paired['fuel_after_mismatch'] += pref != row['선택차량연료']
                # Original brand may differ after relabeling: require an unambiguous original model name.
                possible = lengths.get(row['원래선택차량_모델'], set())
                if len(possible) == 1 and int(row['선택차량전장_mm_0이면미확인']):
                    low, high = SIZE_BANDS[{'작음': 'small', '중간': 'medium', '큼': 'large'}[row[PREFERENCES[1]]]]
                    paired['size_same_rows'] += 1
                    paired['size_before_mismatch'] += not low <= next(iter(possible)) <= high
                    paired['size_after_mismatch'] += not low <= int(row['선택차량전장_mm_0이면미확인']) <= high
            for reason in row['선택설명'].split(';')[1:]:
                mismatch_reasons[reason] += 1
    result = {'legacy_paired_comparison': paired, 'remaining_preference_tradeoffs': mismatch_reasons,
              'new_same_input_groups_with_multiple_models': sum(len(models) > 1 for models in selected_by_group.values())}
    (output / 'before_after_comparison.json').write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')
    return result


def build(source=SOURCE, output=OUTPUT, seed=20261022):
    branch = subprocess.check_output(['git', 'branch', '--show-current'], cwd=ROOT, text=True).strip()
    if branch != 'ml/test':
        raise ValueError('Relabel only on ml/test')
    output, source = Path(output).resolve(), Path(source).resolve()
    if not output.is_relative_to((ROOT / 'data/households/synthetic').resolve()) or output == source or source in output.parents:
        raise ValueError('Use a separate synthetic output directory')
    original_hashes = {str(path): hashlib.sha256(path.read_bytes()).hexdigest()
                       for path in [source / 'combined_training.csv', *list((source / 'existing').glob('*/*.csv'))]}
    vehicles = load_candidates()
    _, baseline = read_csv(source / 'existing_training.csv')
    labels, registry = model_registry(baseline, vehicles)
    del baseline
    contexts = legacy_contexts(source)
    config = json.loads((source / 'generation_config.json').read_text(encoding='utf-8'))
    for row in generate(config['new_financial_groups_requested'], config['seed'], vehicles):
        contexts['NEW-' + row['choice_id']] = {
            'savings': row['monthly_savings'], 'reserve': row['emergency_reserve'],
            'funds': row['down_payment'], 'buffer': row['minimum_buffer'], 'ceiling': row['maximum_price']}
    policy = ChoicePolicy(vehicles)
    output.mkdir(parents=True, exist_ok=True)
    counters, samples, model_counts = {}, [], Counter()
    schema = (*TRAINING_FIELDS, *EXTRA_FIELDS)
    source_rows = 0
    with (source / 'combined_training.csv').open(encoding='utf-8-sig', newline='') as stream, (
            output / 'combined_training.csv').open('w', encoding='utf-8-sig', newline='') as destination:
        writer = csv.DictWriter(destination, fieldnames=schema)
        writer.writeheader()
        for row in csv.DictReader(stream):
            context = contexts[row['프로필_식별자']]
            selected = policy.choose(row, context, seed)
            verify_selected(row, context, selected)
            relabeled = output_row(row, context, selected, labels)
            for key in ('프로필_식별자', '재무조건그룹번호', '데이터_구분', *FEATURES, *PREFERENCES, '선호값_출처'):
                if relabeled[key] != row[key]:
                    raise AssertionError('Input changed during relabeling')
            if set(relabeled) != set(schema) or any(v in ('', None) for v in relabeled.values()):
                raise AssertionError('Incomplete relabeled row')
            writer.writerow(relabeled)
            dataset = '신규' if row['프로필_식별자'].startswith('NEW-') else '기존'
            count = counters.setdefault(dataset, Counter())
            count['rows'] += 1
            count['changed_labels'] += relabeled['결과변경여부'] == '예'
            count['no_choice'] += selected is None
            if selected:
                vehicle = selected['vehicle']
                model_counts[vehicle.model] += 1
                count['selected'] += 1
                if row[PREFERENCES[2]] != '상관없음':
                    count['fuel_compared'] += 1
                    count['fuel_mismatch'] += row[PREFERENCES[2]] != FUEL_LABELS[vehicle.fuel]
                if vehicle.length_mm:
                    count['size_compared'] += 1
                    low, high = SIZE_BANDS[{'작음': 'small', '중간': 'medium', '큼': 'large'}[row[PREFERENCES[1]]]]
                    count['size_mismatch'] += not low <= vehicle.length_mm <= high
            if len(samples) < 30 and relabeled['결과변경여부'] == '예':
                samples.append(relabeled)
            source_rows += 1
            if source_rows % 20000 == 0:
                print(f'Validated and relabeled {source_rows} rows', flush=True)
    # Read the persisted table once more to verify old inputs/order and all numeric outputs.
    with (source / 'combined_training.csv').open(encoding='utf-8-sig', newline='') as before, (
            output / 'combined_training.csv').open(encoding='utf-8-sig', newline='') as after:
        old_rows, new_rows = csv.DictReader(before), csv.DictReader(after)
        from itertools import zip_longest
        for old, new in zip_longest(old_rows, new_rows):
            if old is None or new is None:
                raise AssertionError('Saved row count changed')
            if any(old[k] != new[k] for k in (*FEATURES, *PREFERENCES, '프로필_식별자', '데이터_구분', '재무조건그룹번호')):
                raise AssertionError('Saved inputs or ordering changed')
    for path, expected in original_hashes.items():
        if hashlib.sha256(Path(path).read_bytes()).hexdigest() != expected:
            raise AssertionError('Source file modified')
    write_csv(output / 'examples.csv', schema, samples)
    write_csv(output / 'vehicle_identity_map.csv', list(registry[0]), registry)
    (output / 'catalog.json').write_text(json.dumps([asdict(v) for v in policy.vehicles], ensure_ascii=False, indent=2), encoding='utf-8')
    report = {'version': VERSION, 'rows': source_rows, 'datasets': counters, 'selected_models': model_counts,
              'source_files_unchanged': True, 'input_cell_changes': 0, 'hard_violations': 0,
              'maximum_score_regret_10000': round(NEAR_BEST * 10000)}
    settings = {'version': VERSION, 'seed': seed, 'source_hashes': original_hashes,
                'assumptions': Assumptions().to_dict(), 'months': 60, 'annual_rate_percent': 6,
                'score': '(costImportance*economy + 3*sizeMatch + 3*fuelMatch + purposeMatch)/(costImportance+7)',
                'near_best_regret': NEAR_BEST, 'model_sampling_temperature': 0.015,
                'legacy_finance': 'Keep original savings; reserve min(cash,3*living expenses); remaining cash available for down payment; no extra monthly buffer or price ceiling',
                'new_finance': 'Preserve original synthetic savings, reserve, purchase funds, buffer and price ceiling',
                'model_input_columns': [*FEATURES, *PREFERENCES, '월저축액_원', '비상자금_원', '구매투입가능자금_원',
                                        '최소월여유자금_원', '구매가격상한_원_0이면미지정'],
                'exclude_from_inputs': ['원래선택차량_라벨코드', '원래선택차량_모델', '결과변경여부', '선택차량정보', '선택후비용', '점수', '선택설명'],
                'seating': 'Known base capacity, otherwise minimum of known seat options. Unknown capacity excluded.',
                'charging': 'Not used', 'size': 'Exterior length; unknown length gets zero match score but is not excluded'}
    for name, payload in [('validation_report.json', report), ('generation_config.json', settings)]:
        (output / name).write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding='utf-8')
    summarize_results(source, output)
    print(json.dumps(report, ensure_ascii=True), flush=True)
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=OUTPUT)
    build(output=parser.parse_args().output)
