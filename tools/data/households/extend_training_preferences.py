"""Preserve seed values and extend the eight legacy ML inputs with four preferences."""
import argparse
import csv
import hashlib
import io
import json
import random
import shutil
import subprocess
from collections import Counter
from itertools import zip_longest
from pathlib import Path

from tools.data.households.generate_candidate_choices import ROOT, generate, load_candidates

FEATURES = (
    '개인_평균월실수령소득_원', '개인_현금성자산_원', '개인_평균월주거비_원',
    '개인_평균월기타생활소비_원', '기존대출잔액_보정전_원', '기존월상환액_보정전_원',
    '연간_주행거리_km', '차량_이용목적',
)
PREFERENCES = ('가성비중요도_1부터5', '선호크기', '선호연료', '최소탑승인원_명')
TRAINING_FIELDS = ('프로필_식별자', '재무조건그룹번호', '데이터_구분', *FEATURES, *PREFERENCES,
                   '선택차량_라벨코드', '선택차량_브랜드', '선택차량_모델', '선택상태', '선호값_출처')
PURPOSES = {'commute': '출퇴근', 'leisure': '여가', 'family': '가족이동', 'business': '업무'}
FUELS = ('가솔린', '하이브리드', '디젤', 'LPG', '전기', '상관없음')
FUEL_LABELS = dict(zip(('GASOLINE', 'HYBRID', 'DIESEL', 'LPG', 'ELECTRIC'), FUELS))
VERSION = 'legacy-inputs-with-preferences-v2'

ADDITIONAL_SOURCES = (
    ('domestic-extra-90000', '국내차_보유자_추가90000_학습데이터.csv', '국내차_추가90000_트림옵션_구매자금내역.csv'),
    ('imported-extra-90000', '수입차_보유자_추가90000_학습데이터.csv', '수입차_추가90000_트림옵션_구매자금내역.csv'),
)


def read_csv(path):
    with Path(path).open(encoding='utf-8-sig', newline='') as stream:
        reader = csv.DictReader(stream)
        return reader.fieldnames, list(reader)


def write_csv(path, columns, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('w', encoding='utf-8-sig', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=columns)
        writer.writeheader()
        writer.writerows(rows)


def independent_preferences(profile_id, purpose, seed):
    """Never read the existing selected vehicle, label, price, or trim."""
    rng = random.Random(hashlib.sha256(f'{seed}:{profile_id}'.encode()).hexdigest())
    seats = rng.choice((3, 4)) if purpose == '가족이동' else rng.choice((1, 2, 4))
    return dict(zip(PREFERENCES, (rng.randint(1, 5), rng.choice(('작음', '중간', '큼')),
                                  rng.choice(FUELS), seats)))


def extend_owners(rows, seed):
    if any(set(PREFERENCES) & row.keys() for row in rows):
        raise ValueError('Source already contains preference columns; refusing to overwrite')
    return [{**row, **independent_preferences(row['프로필_식별자'], row['차량_이용목적'], seed)}
            for row in rows]


def assert_preserved(original, extended, columns):
    if len(original) != len(extended):
        raise AssertionError('Original row count changed')
    for before, after in zip(original, extended):
        if any(before[column] != after[column] for column in columns):
            raise AssertionError('Original value or row order changed')
        if any(after[column] in ('', None) for column in PREFERENCES):
            raise AssertionError('Missing appended preference')


def verify_main_csv(path):
    """Read main without checkout; compare cells without holding both CSVs in memory."""
    reference = subprocess.Popen(['git', 'show', f'main:{path.relative_to(ROOT).as_posix()}'],
                                 cwd=ROOT, stdout=subprocess.PIPE, text=True, encoding='utf-8-sig')
    try:
        with path.open(encoding='utf-8-sig', newline='') as stream:
            for local, original in zip_longest(csv.reader(stream), csv.reader(reference.stdout)):
                if local != original:
                    raise ValueError(f'Source differs from main: {path}')
        if reference.wait() != 0:
            raise ValueError(f'Cannot read main source: {path}')
    finally:
        reference.stdout.close()
        if reference.poll() is None:
            reference.terminate()
        reference.wait()
    return hashlib.sha256(path.read_bytes()).hexdigest()


def extend_additional_source(owners_path, purchases_path, target, seed, expected_rows=90000):
    """Preserve all source cells and append preferences in original order."""
    _, purchases = read_csv(purchases_path)
    by_id = {row['프로필_식별자']: row for row in purchases}
    if len(by_id) != len(purchases):
        raise ValueError('Duplicate additional purchase ID')
    baseline, seen = [], set()
    target.mkdir(parents=True, exist_ok=True)
    with owners_path.open(encoding='utf-8-sig', newline='') as source, (target / 'owners.csv').open(
            'w', encoding='utf-8-sig', newline='') as destination:
        reader = csv.DictReader(source)
        columns = reader.fieldnames
        if set(PREFERENCES) & set(columns):
            raise ValueError('Additional source already contains preferences')
        writer = csv.DictWriter(destination, fieldnames=[*columns, *PREFERENCES])
        writer.writeheader()
        for original in reader:
            identity = original['프로필_식별자']
            if identity in seen or identity not in by_id:
                raise ValueError('Additional profile/purchase join is not one-to-one')
            seen.add(identity)
            extended = extend_owners([original], seed)[0]
            writer.writerow(extended)
            baseline.extend(legacy_training([extended], [by_id[identity]]))
    if len(seen) != expected_rows or seen != set(by_id):
        raise ValueError('Unexpected additional row count or unmatched purchase')
    # Verify the saved output against the original, including order and every old cell.
    with owners_path.open(encoding='utf-8-sig', newline='') as source, (target / 'owners.csv').open(
            encoding='utf-8-sig', newline='') as destination:
        for original, extended in zip_longest(csv.DictReader(source), csv.DictReader(destination)):
            if original is None or extended is None:
                raise AssertionError('Additional output row count changed')
            assert_preserved([original], [extended], columns)
    shutil.copyfile(purchases_path, target / 'purchases.csv')
    if (target / 'purchases.csv').read_bytes() != purchases_path.read_bytes():
        raise AssertionError('Additional purchase bytes changed')
    return baseline, {'rows': len(baseline), 'original_cell_changes': 0,
                      'original_columns': len(columns), 'appended_columns': len(PREFERENCES),
                      'purchase_bytes_unchanged': True}


def legacy_training(owners, purchases):
    lookup = {row['프로필_식별자']: row for row in purchases}
    if len(lookup) != len(purchases) or len(lookup) != len(owners):
        raise ValueError('Purchase/profile join is not one-to-one')
    rows = []
    for owner in owners:
        identity = owner['프로필_식별자']
        purchase = lookup[identity]
        rows.append({
            '프로필_식별자': identity, '재무조건그룹번호': identity, '데이터_구분': owner['데이터_구분'],
            **{key: purchase[key] if key in FEATURES[4:6] else owner[key] for key in FEATURES},
            **{key: owner[key] for key in PREFERENCES},
            '선택차량_라벨코드': owner['보유차량_라벨코드'],
            '선택차량_브랜드': owner['보유차량_브랜드'], '선택차량_모델': owner['보유차량_모델'],
            '선택상태': '기존합성선택', '선호값_출처': '기존선택과무관한합성보충',
        })
    return rows


def model_registry(legacy_rows, vehicles):
    known = {}
    for row in legacy_rows:
        key = (row['선택차량_브랜드'], row['선택차량_모델'])
        if key in known and known[key] != row['선택차량_라벨코드']:
            raise ValueError('Conflicting legacy model labels')
        known[key] = row['선택차량_라벨코드']
    lookup = {}
    for vehicle in vehicles:
        key = (vehicle.brand, vehicle.model)
        lookup[vehicle.id] = known.get(key) or 'NEW-' + hashlib.sha256(
            json.dumps(key, ensure_ascii=False).encode()).hexdigest()[:12]
    registry = [{'차량사양번호': v.id, '선택차량_라벨코드': lookup[v.id], '브랜드': v.brand,
                 '모델': v.model, '트림': v.trim, '연결방식': '브랜드모델완전일치' if (v.brand, v.model) in known
                 else '신규모델라벨_기존모델과자동동일시안함'} for v in vehicles]
    return lookup, registry


def new_training(rows, labels, seed):
    result, housing = [], {}
    for row in rows:
        group = row['financial_group_id']
        if group not in housing:
            # Derived only from pre-choice finance inputs and seed, never the chosen car.
            rng = random.Random(hashlib.sha256(f'housing:{seed}:{group}'.encode()).hexdigest())
            housing[group] = round(row['monthly_expenses'] * rng.uniform(0.2, 0.5))
        chosen = bool(row['selected_vehicle_id'])
        result.append({
            '프로필_식별자': 'NEW-' + row['choice_id'], '재무조건그룹번호': 'NEW-' + group,
            '데이터_구분': {'train': '학습', 'validation': '검증', 'test': '평가',
                        'combination_test': '새선호조합평가'}[row['split']],
            FEATURES[0]: row['monthly_income'], FEATURES[1]: row['liquid_assets'],
            FEATURES[2]: housing[group], FEATURES[3]: row['monthly_expenses'] - housing[group],
            FEATURES[4]: row['existing_debt_balance_won'], FEATURES[5]: row['existing_monthly_payment'],
            FEATURES[6]: row['annual_distance'], FEATURES[7]: PURPOSES[row['purpose']],
            PREFERENCES[0]: row['cost_importance'],
            PREFERENCES[1]: {'small': '작음', 'medium': '중간', 'large': '큼'}[row['preferred_size']],
            PREFERENCES[2]: FUEL_LABELS.get(row['preferred_fuel'], '상관없음'),
            PREFERENCES[3]: row['minimum_seats'],
            '선택차량_라벨코드': labels[row['selected_vehicle_id']] if chosen else 'NO-CHOICE',
            '선택차량_브랜드': row['selected_brand'] if chosen else '해당없음',
            '선택차량_모델': row['selected_model'] if chosen else '선택없음',
            '선택상태': '신규합성선택' if chosen else '조건충족후보없음',
            '선호값_출처': '차량선택전합성생성',
        })
    return result


def validate_training(rows):
    ids, groups = set(), {}
    numeric = (*FEATURES[:7], PREFERENCES[0], PREFERENCES[3])
    for row in rows:
        if set(row) != set(TRAINING_FIELDS) or any(value in ('', None) for value in row.values()):
            raise AssertionError('Training row is incomplete')
        if row['프로필_식별자'] in ids:
            raise AssertionError('Duplicate profile ID')
        ids.add(row['프로필_식별자'])
        if any(not str(row[key]).isdigit() for key in numeric):
            raise AssertionError('Non-integer or negative model input')
        if not 1 <= int(row[PREFERENCES[0]]) <= 5 or not 1 <= int(row[PREFERENCES[3]]) <= 9:
            raise AssertionError('Invalid preference range')
        group = row['재무조건그룹번호']
        split = '평가' if row['데이터_구분'] == '새선호조합평가' else row['데이터_구분']
        finance = tuple(str(row[key]) for key in FEATURES[:6])
        if group in groups and groups[group] != (split, finance):
            raise AssertionError('Finance mismatch or group split leakage')
        groups[group] = (split, finance)
    return {'rows': len(rows), 'missing_cells': 0, 'duplicate_profile_ids': 0,
            'financial_group_leakage': 0, 'split_counts': dict(Counter(r['데이터_구분'] for r in rows))}


def build(output, groups=1000, seed=20261022):
    if subprocess.check_output(['git', 'branch', '--show-current'], cwd=ROOT, text=True).strip() != 'ml/test':
        raise ValueError('This data extension must run on ml/test')
    main_before = subprocess.check_output(['git', 'rev-parse', 'main'], cwd=ROOT, text=True).strip()
    output = Path(output)
    if output.resolve() == (ROOT / 'data/seed').resolve() or (ROOT / 'data/seed').resolve() in output.resolve().parents:
        raise ValueError('Output must not overwrite seed source data')
    output.mkdir(parents=True, exist_ok=True)
    original_hashes, baseline, reports = {}, [], {}
    for segment in ('domestic-car', 'imported-car'):
        paths = {name: ROOT / 'data/seed' / segment / name for name in ('owners.csv', 'purchases.csv')}
        for name, path in paths.items():
            payload = path.read_bytes()
            reference = subprocess.check_output(['git', 'show', f'main:{path.relative_to(ROOT).as_posix()}'], cwd=ROOT)
            # Git checkout can convert newlines; compare every parsed CSV cell with main.
            if list(csv.reader(io.StringIO(payload.decode('utf-8-sig')))) != list(
                    csv.reader(io.StringIO(reference.decode('utf-8-sig')))):
                raise ValueError(f'Source differs from main; inspect before extending: {path}')
            original_hashes[str(path.relative_to(ROOT))] = hashlib.sha256(payload).hexdigest()
        columns, owners = read_csv(paths['owners.csv'])
        _, purchases = read_csv(paths['purchases.csv'])
        extended = extend_owners(owners, seed)
        target = output / 'existing' / segment
        write_csv(target / 'owners.csv', [*columns, *PREFERENCES], extended)
        shutil.copyfile(paths['purchases.csv'], target / 'purchases.csv')
        _, reread = read_csv(target / 'owners.csv')
        assert_preserved(owners, reread, columns)
        if (target / 'purchases.csv').read_bytes() != paths['purchases.csv'].read_bytes():
            raise AssertionError('Purchase source bytes changed')
        baseline.extend(legacy_training(reread, purchases))
        reports[segment] = {'rows': len(owners), 'original_cell_changes': 0,
                            'original_columns': len(columns), 'appended_columns': len(PREFERENCES),
                            'purchase_bytes_unchanged': True}
    for segment, owners_name, purchases_name in ADDITIONAL_SOURCES:
        directory = ROOT / 'data/households/synthetic' / segment
        if output.resolve() == directory.resolve() or directory.resolve() in output.resolve().parents:
            raise ValueError('Output must not overwrite additional source data')
        for name in (owners_name, purchases_name):
            path = directory / name
            original_hashes[str(path.relative_to(ROOT))] = verify_main_csv(path)
        added, reports[segment] = extend_additional_source(
            directory / owners_name, directory / purchases_name, output / 'existing' / segment, seed)
        baseline.extend(added)
        del added
    vehicles = load_candidates()
    labels, registry = model_registry(baseline, vehicles)
    generated = generate(groups, seed, vehicles)
    from tools.data.households.generate_candidate_choices import validate
    generator_report = validate(generated, vehicles)
    new = new_training(generated, labels, seed)
    combined = baseline + new
    reports['existing_training'] = validate_training(baseline)
    reports['new_training'] = validate_training(new)
    reports['combined_training'] = validate_training(combined)
    reports['new_choice_rules'] = generator_report
    def combination(row):
        return tuple(str(row[key]) for key in (PREFERENCES[0], PREFERENCES[1], FEATURES[7]))
    legacy_combinations = {combination(row) for row in baseline if row['데이터_구분'] == '학습'}
    new_heldout = {combination(row) for row in new if row['데이터_구분'] == '새선호조합평가'}
    reports['combined_combination_overlap'] = len(legacy_combinations & new_heldout)
    for name, rows in [('existing_training.csv', baseline), ('new_training.csv', new),
                       ('combined_training.csv', combined)]:
        write_csv(output / name, TRAINING_FIELDS, rows)
        _, reread = read_csv(output / name)
        validate_training(reread)
    write_csv(output / 'vehicle_identity_map.csv', list(registry[0]), registry)
    write_csv(output / 'examples.csv', TRAINING_FIELDS, baseline[:5] + new[:12])
    for path, expected in original_hashes.items():
        if hashlib.sha256((ROOT / path).read_bytes()).hexdigest() != expected:
            raise AssertionError('Original seed changed during generation')
    config = {'version': VERSION, 'seed': seed, 'new_financial_groups_requested': groups,
              'source_main_commit': main_before, 'work_branch': 'ml/test',
              'legacy_inputs': FEATURES, 'added_preferences': PREFERENCES,
              'source_sha256': original_hashes,
              'preference_backfill': 'Independent of existing vehicle and label; synthetic, not observed',
              'new_choice_policy': 'generate_candidate_choices v3, 60 months, 6 percent assumed rate',
              'no_choice': 'Explicit NO-CHOICE target; never fabricate a qualifying vehicle',
              'housing_split': '20..50 percent of pre-choice living expenses; remainder is other consumption'}
    for name, value in [('generation_config.json', config), ('validation_report.json', reports)]:
        (output / name).write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding='utf-8')
    if subprocess.check_output(['git', 'rev-parse', 'main'], cwd=ROOT, text=True).strip() != main_before:
        raise AssertionError('Main branch reference changed during generation')
    return reports


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=ROOT / 'data/households/synthetic/preference-extended-v1')
    parser.add_argument('--groups', type=int, default=1000)
    parser.add_argument('--seed', type=int, default=20261022)
    args = parser.parse_args()
    report = build(args.output, args.groups, args.seed)
    print(json.dumps({key: value for key, value in report.items() if key != 'new_choice_rules'}, ensure_ascii=False))


if __name__ == '__main__':
    main()
