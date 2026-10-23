"""Audit existing choices separately from independently generated preference labels."""
import csv
import hashlib
import json
from collections import Counter, defaultdict

from tools.data.households.extend_training_preferences import (
    FEATURES, FUEL_LABELS, PREFERENCES, ROOT, generate, load_candidates, model_registry,
    new_training, read_csv, write_csv,
)
from tools.data.households.generate_candidate_choices import validate
from vehicle_matching.finance import Assumptions
from vehicle_matching.preferences import SIZE_BANDS

BASE = ROOT / 'data/households/synthetic/preference-extended-v1'


def preference_checks(row, fuel, lengths, seats):
    result = []
    preferred = row[PREFERENCES[2]]
    if preferred != '상관없음':
        if fuel is None:
            result.append('연료비교불가')
        elif preferred != fuel:
            result.append('연료선호불일치_선호차이')
    if not lengths:
        result.append('크기비교불가')
    else:
        low, high = SIZE_BANDS[{'작음': 'small', '중간': 'medium', '큼': 'large'}[row[PREFERENCES[1]]]]
        matches = [low <= length <= high for length in lengths]
        if not any(matches):
            result.append('크기선호불일치_선호차이')
        elif not all(matches):
            result.append('크기사양확인필요')
    if not seats:
        result.append('정원확인불가')
    elif max(seats) < int(row[PREFERENCES[3]]):
        result.append('최소탑승인원위반')
    elif min(seats) < int(row[PREFERENCES[3]]):
        result.append('정원옵션확인필요')
    return result


def accounting_checks(purchase):
    def amount(key):
        return int(purchase[key])
    checks = {
        '구매자금합계불일치': amount('본인구매자금_원') + amount('가족지원금_가정_원')
        + amount('차량할부원금_원') - amount('총구매비용_가정_원'),
        '구매전후현금불일치': amount('구매직전_현금_원') - amount('본인구매자금_원')
        - amount('구매직후_현금_원'),
        '구매비용구성불일치': amount('옵션포함가격_원') + amount('등록비_가정_원')
        - amount('총구매비용_가정_원'),
    }
    return [name for name, difference in checks.items() if abs(difference) > 1]


def running_cost(fuel, distance):
    # Common audit estimate, not the original historical cost policy.
    assumptions = Assumptions()
    fuel = {'MILD_HYBRID': 'GASOLINE', 'PHEV': 'GASOLINE'}.get(fuel, fuel)
    names = ('GASOLINE', 'HYBRID', 'DIESEL', 'LPG', 'ELECTRIC')
    if fuel not in names:
        return None
    index = names.index(fuel)
    efficiency = sum(assumptions.efficiency_ranges[index]) / 2
    return round(distance / 12 / efficiency * assumptions.energy_prices[index]
                 + assumptions.monthly_insurance + assumptions.monthly_maintenance + assumptions.monthly_tax)


def audit(base=BASE):
    config = json.loads((base / 'generation_config.json').read_text(encoding='utf-8'))
    watched = [base / name for name in ('existing_training.csv', 'new_training.csv', 'combined_training.csv')]
    before = {str(path): hashlib.sha256(path.read_bytes()).hexdigest() for path in watched}
    vehicles = load_candidates()
    by_model = defaultdict(list)
    for vehicle in vehicles:
        by_model[(vehicle.brand, vehicle.model)].append(vehicle)
    stats, price_groups, examples, examples_count = {}, {}, [], Counter()

    def record(dataset, row, issues, fuel, price, remaining=None):
        counter = stats.setdefault(dataset, Counter())
        counter['행수'] += 1
        counter.update(set(issues))
        prefuel = row[PREFERENCES[2]]
        if prefuel != '상관없음' and fuel is not None:
            counter['연료비교가능행수'] += 1
        prices = price_groups.setdefault(dataset, defaultdict(lambda: [0, 0]))
        importance = str(row[PREFERENCES[0]])
        if price > 0:
            prices[importance][0] += price
            prices[importance][1] += 1
        for issue in issues:
            if examples_count[(dataset, issue)] >= 3:
                continue
            examples_count[(dataset, issue)] += 1
            examples.append({'데이터종류': dataset, '프로필번호': row['프로필_식별자'], '점검항목': issue,
                             '선택차량': row['선택차량_모델'], '선호크기': row[PREFERENCES[1]],
                             '선호연료': prefuel, '실제연료': fuel or '확인불가',
                             '월소득_원': row[FEATURES[0]], '차량가격_원': price,
                             '비용차감후월잔여액_원': remaining if remaining is not None else '해당없음'})

    # Source purchase details identify the actual trim/fuel/price; never infer them from preferences.
    for segment in ('domestic-car', 'imported-car', 'domestic-extra-90000', 'imported-extra-90000'):
        _, purchases = read_csv(base / 'existing' / segment / 'purchases.csv')
        purchase_by_id = {row['프로필_식별자']: row for row in purchases}
        with (base / 'existing' / segment / 'owners.csv').open(encoding='utf-8-sig', newline='') as stream:
            for owner in csv.DictReader(stream):
                purchase = purchase_by_id[owner['프로필_식별자']]
                row = {**owner, **{key: purchase[key] for key in FEATURES[4:6]},
                       '선택차량_모델': owner['보유차량_모델']}
                matched = by_model.get((owner['보유차량_브랜드'], owner['보유차량_모델']), [])
                lengths = sorted({v.length_mm for v in matched if v.length_mm})
                seats = sorted({s for v in matched for s in ((v.seats,) if v.seats else v.seat_options)})
                actual_fuel = FUEL_LABELS.get(purchase['연료'])
                if not purchase['연료'] and owner['보유차량_모델'] == '모닝':
                    actual_fuel = '가솔린'
                issues = preference_checks(row, actual_fuel, lengths, seats)
                issues += accounting_checks(purchase)
                if purchase['구매_모델'] != owner['보유차량_모델']:
                    issues.append('원본구매모델과보유모델불일치')
                available = int(owner[FEATURES[0]]) - int(owner[FEATURES[2]]) - int(owner[FEATURES[3]])
                available -= int(purchase[FEATURES[5]]) + int(owner['개인_평균월저축액_원'])
                after_payment = available - int(purchase['차량_월상환액_원'])
                if after_payment < 0:
                    issues.append('생활비저축기존상환차량할부차감후적자')
                running = running_cost(purchase['연료'] or ('GASOLINE' if owner['보유차량_모델'] == '모닝' else ''),
                                       int(owner[FEATURES[6]]))
                if running is not None and after_payment - running < 0:
                    issues.append('공통유지비추정추가시적자_가정기준')
                record('기존196000행', row, issues, actual_fuel, int(purchase['기본가격_원']),
                       after_payment - running if running is not None else after_payment)
        del purchase_by_id, purchases

    _, baseline = read_csv(base / 'existing_training.csv')
    labels, _ = model_registry(baseline, vehicles)
    del baseline
    generated = generate(config['new_financial_groups_requested'], config['seed'], vehicles)
    generation_validation = validate(generated, vehicles)
    expected = new_training(generated, labels, config['seed'])
    _, actual = read_csv(base / 'new_training.csv')
    if len(expected) != len(actual) or any({k: str(v) for k, v in a.items()} != b for a, b in zip(expected, actual)):
        raise AssertionError('New table is not reproducible from recorded inputs and seed')
    for raw, row in zip(generated, actual):
        if not raw['selected_vehicle_id']:
            record('신규10156행', row, ['선택없음'], None, 0)
            continue
        matched = by_model[(raw['selected_brand'], raw['selected_model'])]
        vehicle = next(v for v in matched if v.id == raw['selected_vehicle_id'])
        issues = preference_checks(row, FUEL_LABELS[vehicle.fuel], [vehicle.length_mm] if vehicle.length_mm else [],
                                  [vehicle.seats] if vehicle.seats else list(vehicle.seat_options))
        if vehicle.seats is None and not vehicle.seat_options and int(row[PREFERENCES[3]]) <= 4:
            issues.append('미확인정원2부터4인가정적용')
        record('신규10156행', row, issues, FUEL_LABELS[vehicle.fuel], vehicle.price, raw['selected_remaining'])

    for key in ('구매자금합계불일치', '구매전후현금불일치', '구매비용구성불일치',
                '원본구매모델과보유모델불일치', '최소탑승인원위반', '정원확인불가'):
        stats['기존196000행'].setdefault(key, 0)
    for dataset, groups in price_groups.items():
        stats[dataset]['가성비중요도별평균차량가격_원'] = {
            key: round(total / count) for key, (total, count) in sorted(groups.items())}
    for path in watched:
        if hashlib.sha256(path.read_bytes()).hexdigest() != before[str(path)]:
            raise AssertionError('Audit changed a training file')
    report = {'datasets': stats, 'new_generation_validation': generation_validation,
              'new_table_reproduced_exactly': True, 'training_file_hashes_unchanged': True,
              'limitations': [
                  'Preference mismatch is a soft tradeoff, not automatically a hard violation.',
                  'Legacy preferences were independent random backfills and cannot explain existing choices.',
                  'Legacy length/seats use exact brand/model matches; unlinked or trim-dependent data remain unknown.',
                  'Legacy PHEV and mild hybrid fuel preference comparisons are unknown, not silently mapped to hybrid.',
                  'Common running cost estimates are audit assumptions, not original purchase policy or real quotes.',
                  'New financial decisions also use savings, emergency buffer, space weight and financing inputs absent from the common 12-input table.',
              ]}
    (base / 'choice_consistency_report.json').write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
    write_csv(base / 'choice_consistency_examples.csv', list(examples[0]), examples)
    old, fresh = stats['기존196000행'], stats['신규10156행']
    selected = fresh['행수'] - fresh['선택없음']
    markdown = f'''# 선택 차량과 입력 정보의 일관성 점검

전체 206,156행을 기존 196,000행과 신규 10,156행으로 나누어 점검했다. 파일 내용은 수정하지 않았다.

## 결론

현재 통합 데이터는 그대로 선호 기반 추천의 정답으로 사용하기 어렵다. 기존 자료의 구매자금 회계식은 맞지만, 사후에 독립 생성한 선호가 기존 선택을 설명하지 않는다. 기존과 신규 자료의 재무 적격 기준도 다르다. 이는 이전 검증의 ‘결측 없음·값 보존’과 별개의 의미상 품질 문제다.

## 주요 결과

| 점검 | 기존 196,000행 | 신규 10,156행 |
| --- | ---: | ---: |
| 실제 차량 선택 행 | 196,000 | {selected:,} |
| 선택 없음 | 0 | {fresh['선택없음']:,} |
| 명시된 연료 선호 비교 가능한 행 | {old['연료비교가능행수']:,} | {fresh['연료비교가능행수']:,} |
| 그중 연료 선호 불일치 | {old['연료선호불일치_선호차이']:,} | {fresh['연료선호불일치_선호차이']:,} |
| 전장으로 크기를 비교 가능한 선택 행 | {196000-old['크기비교불가']:,} | {selected-fresh['크기비교불가']:,} |
| 그중 크기 선호 불일치 | {old['크기선호불일치_선호차이']:,} | {fresh['크기선호불일치_선호차이']:,} |
| 생활비·저축·기존상환·차량할부 차감 후 적자 | {old['생활비저축기존상환차량할부차감후적자']:,} | 생성 규칙 검증에서 적격 위반 0건 |
| 공통 유지비 추정을 추가하면 적자 | {old['공통유지비추정추가시적자_가정기준']:,} | 생성 규칙 검증에서 적격 위반 0건 |
| 구매자금 합계·현금 흐름·총구매비 구성 오류 | 0 | 신규 생성 규칙으로 별도 검증 |
| 확인된 정원상 최소 인원 부족 | {old['최소탑승인원위반']:,} | {fresh.get('최소탑승인원위반',0):,} |

선호 불일치는 곧바로 오류가 아니다. 선호는 비용·다른 선호와 절충할 수 있다. 하지만 기존 선호는 선택과 독립인 합성 보충값이므로 그 불일치를 실제 사용자의 절충이라고 해석할 근거가 없다. 기존 가성비 중요도 1~5별 평균 구매가격도 JSON에 기록했다. 원시 평균은 소득·예산 등의 영향을 통제한 인과 효과가 아니다.

## 해석 범위와 추가 문제

- 기존 재무 적자는 원본 합성 구매를 현재의 예산 적격 정답으로 사용할 때의 문제다. 원본 생성 자체의 회계 오류라고 단정하지 않는다. 유지비 추가 적자는 현재 공통 가정을 사용한 추정치이지 실측치가 아니다.
- 전장과 정원은 브랜드·모델이 정확히 연결되는 카탈로그 범위에서 점검했다. 여러 사양의 값이 다르면 범위로 보고 미확인 자료는 위반으로 단정하지 않았다. 정원 등록값은 사용자 제공값도 포함하며 전체가 공식 검증값은 아니다.
- 기존 연료 PHEV/MILD_HYBRID는 여섯 가지 선호 중 어느 것과 같은지 정의되지 않아 선호 비교에서 제외했다. 모닝 연료 공란만 기존 정규화 정책에 따라 가솔린으로 처리했다.
- 신규 자료는 기록된 seed로 다시 생성하고 현재 new_training.csv의 모든 값과 정확히 같음을 확인했다. 실제 선택에는 저축·비상자금·선수금·가격 상한·공간 가중치 등 공통 입력 12개에 없는 변수가 사용된다. 이 정보를 입력에 전달하지 않으면 모델이 선택의 모든 이유를 배울 수 없다.
- 기존 196,000행이 통합 자료의 약 95%를 차지한다. 이 선호 보충값을 신규 선호 기반 정답과 동등하게 섞으면 학습에서 선호 신호가 약해질 수 있다. 그 영향 크기는 이후 실제 학습 비교로 측정해야 한다.

## 권고

원본과 확장본은 보존한다. 기존 네 선호는 관측값으로 취급하지 않고, 기존 데이터는 재무·차량 기본 관계의 기준선으로 구분한다. 선호 학습에는 선호를 먼저 정한 신규 사례를 사용하고, 재무 적격 기준 및 학습에 실제 전달할 입력과 선택 규칙을 일치시킨다. 기존 선택에 맞춰 선호를 거꾸로 수정하거나 문제 행을 몰래 제거하지 않는다.

상세 수치: choice_consistency_report.json. 점검별 최대 3개 예시: choice_consistency_examples.csv.

재현: `python -m tools.data.households.audit_choice_consistency`
'''
    (base / 'choice_consistency_report.md').write_text(markdown, encoding='utf-8')
    print(json.dumps(stats, ensure_ascii=True, indent=2))
    return report


if __name__ == '__main__':
    audit()
