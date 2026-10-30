"""Compare catalog coverage using the unchanged financial and recommendation policy.

Run with --before, --after, --aliases, --model and --output paths.
The body preference is soft: report exact-body candidates separately from fallback results.
"""
import argparse
import csv
from dataclasses import fields
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / 'ml'))
from build_catalog_distribution import BODY_TYPES, BODY_LABELS
from vehicle_matching.api import load_service
from vehicle_matching.budget import recommendation_budget
from vehicle_matching.catalog import Vehicle
from vehicle_matching.finance import Profile, assess
from vehicle_matching.service import CandidateService

ASSET_LEVELS = (30_000_000, 50_000_000, 100_000_000, 150_000_000, 200_000_000, 300_000_000)
IMPORTANCES = ((1, '낮음 · 하한 80%'), (3, '보통 · 하한 70%'), (5, '높음 · 하한 60%'))


def read_vehicles(path):
    allowed = {field.name for field in fields(Vehicle)}
    rows = json.loads(path.read_text(encoding='utf-8-sig'))
    vehicles = [Vehicle(**{key: value for key, value in row.items() if key in allowed}) for row in rows]
    if len({vehicle.id for vehicle in vehicles}) != len(vehicles):
        raise ValueError('Duplicate vehicle IDs')
    return vehicles


def profile_for(assets, importance, body):
    return Profile(monthly_income=3_600_000, monthly_expenses=1_800_000,
                   existing_monthly_payment=0, liquid_assets=assets, down_payment=0,
                   emergency_reserve=0, monthly_savings=300_000, annual_distance=15_000,
                   months=0, annual_rate=0, minimum_buffer=300_000,
                   cost_importance=importance, preferred_body_type=body, body_importance=3,
                   charging_available=True, minimum_seats=0, financing_mode='recommendation')


def evaluate(vehicles, ranker, aliases, stage):
    service = CandidateService(ranker, vehicles)
    def families(items):
        return sorted({aliases.get(f'{v.brand}|{v.model}', f'{v.brand} {v.model}') for v in items})
    rows = []
    for assets in ASSET_LEVELS:
        for importance, _ in IMPORTANCES:
            for body in BODY_TYPES:
                profile = profile_for(assets, importance, body)
                result = service.recommend(profile)
                band = recommendation_budget(profile, [], {})
                same_body = [v for v in vehicles if v.body_type == body]
                price_matches = [v for v in same_body if band['lower'] <= v.price <= band['upper']]
                eligible = [v for v in price_matches if assess(profile, v, ranker.assumptions)['eligible']]
                selected = result['recommendations']
                if any(not band['lower'] <= item['vehicle']['price'] <= band['upper'] for item in selected):
                    raise AssertionError('Recommendation violates the unchanged price band')
                rows.append({'stage': stage, 'assets': assets, 'cost_importance': importance,
                             'body_type': body, 'lower': band['lower'], 'upper': band['upper'],
                             'catalog_families': len(families(same_body)),
                             'price_match_families': len(families(price_matches)),
                             'eligible_families': len(families(eligible)),
                             'eligible_model_names': families(eligible),
                             'known_seating_families': len(families([v for v in eligible if v.seats is not None])),
                             'same_body_in_top3': sum(v['vehicle']['body_type'] == body for v in selected),
                             'returned': [v['vehicle']['brand'] + ' ' + v['vehicle']['model'] for v in selected],
                             'outside_training_range_in_top3': sum(bool(v['outsideTrainingRange']) for v in selected),
                             'status': result['status'],
                             'gap_reason': 'catalog-price-gap' if not price_matches else
                                           'monthly-affordability' if not eligible else 'available'})
    return rows


def write_plot(rows, output):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from matplotlib.colors import LogNorm
    plt.rcParams.update({'font.family': 'Malgun Gothic', 'axes.unicode_minus': False})
    fig, axes = plt.subplots(1, 3, figsize=(16, 5.5), constrained_layout=True)
    vmax = max(1, max(row['eligible_families'] for row in rows))
    for ax, (importance, label) in zip(axes, IMPORTANCES):
        lookup = {(row['body_type'], row['assets']): row['eligible_families'] for row in rows
                  if row['cost_importance'] == importance}
        matrix = [[lookup[body, assets] for assets in ASSET_LEVELS] for body in BODY_TYPES]
        plot = ax.imshow([[max(.5, value) for value in line] for line in matrix],
                         cmap='Blues', norm=LogNorm(.5, vmax), aspect='auto')
        ax.set_xticks(range(len(ASSET_LEVELS)), ['3천만', '5천만', '1억', '1.5억', '2억', '3억'], rotation=25)
        ax.set_yticks(range(len(BODY_TYPES)), BODY_LABELS)
        ax.set_title('가성비 중요도 ' + label)
        ax.set_xlabel('보유 자금 (원)')
        for y, line in enumerate(matrix):
            for x, value in enumerate(line):
                ax.text(x, y, str(value), ha='center', va='center',
                        color='white' if value > vmax / 3 else '#172b44')
    fig.suptitle('보충 후 · 가격대와 유지비 조건을 충족하는 동일 차체 모델군 수', fontsize=17)
    fig.colorbar(plot, ax=axes, shrink=.8, label='모델군 수 (로그 색상 척도)')
    fig.savefig(output / 'funding-coverage.png', dpi=160)
    plt.close(fig)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('before', 'after', 'aliases', 'model', 'output'):
        parser.add_argument('--' + name, type=Path, required=True)
    args = parser.parse_args()
    aliases = json.loads(args.aliases.read_text(encoding='utf-8-sig'))
    service = load_service(args.model)
    before = evaluate(read_vehicles(args.before), service.ranker, aliases, 'before')
    after = evaluate(read_vehicles(args.after), service.ranker, aliases, 'after')
    args.output.mkdir(parents=True, exist_ok=True)
    summary = {'scenario_count_per_stage': len(before),
               'empty_exact_body_before': sum(row['eligible_families'] == 0 for row in before),
               'empty_exact_body_after': sum(row['eligible_families'] == 0 for row in after),
               'empty_gaps_filled': sum(old['eligible_families'] == 0 < new['eligible_families']
                                        for old, new in zip(before, after)),
               'scenarios_with_more_families': sum(new['eligible_families'] > old['eligible_families']
                                                   for old, new in zip(before, after))}
    report = {'assumptions': {'monthly_income': 3600000, 'monthly_expenses': 1800000,
                             'monthly_savings': 300000, 'minimum_buffer': 300000,
                             'annual_distance': 15000, 'charging_available': True,
                             'minimum_seats': 0, 'body_importance': 3},
              'model_path': str(args.model), 'summary': summary, 'cases': before + after}
    (args.output / 'funding-coverage.json').write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
    with (args.output / 'funding-coverage.csv').open('w', encoding='utf-8-sig', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=list(before[0]))
        writer.writeheader()
        for row in before + after:
            writer.writerow({key: '; '.join(value) if isinstance(value, list) else value for key, value in row.items()})
    write_plot(after, args.output)
    print(json.dumps(summary, ensure_ascii=False))


if __name__ == '__main__':
    main()
