"""Report published catalog coverage without counting powertrain variants as models.

Usage: python tools/data/vehicles/build_catalog_distribution.py --before snapshot.json
       --after snapshot.json --aliases aliases.json --output report-directory
Price intervals include the lower bound and exclude the upper bound.
"""
import argparse
import csv
import json
from pathlib import Path

BODY_TYPES = ('SEDAN', 'SUV', 'HATCHBACK', 'WAGON', 'MPV', 'BOX', 'PICKUP')
BODY_LABELS = ('세단', 'SUV', '해치백', '왜건', 'MPV', '박스형', '픽업')
PRICE_BOUNDS = (20_000_000, 40_000_000, 60_000_000, 80_000_000, 100_000_000,
                150_000_000, 200_000_000)
PRICE_LABELS = ('2천만 미만', '2천–4천만', '4천–6천만', '6천–8천만', '8천만–1억',
                '1억–1.5억', '1.5억–2억', '2억 이상')


def price_bucket(price):
    import math
    if isinstance(price, bool) or not isinstance(price, (int, float)) or not math.isfinite(price) or price <= 0:
        raise ValueError('A finite positive vehicle price is required')
    return next((index for index, upper in enumerate(PRICE_BOUNDS) if price < upper), len(PRICE_BOUNDS))


def summarize(rows, aliases):
    ids = [row['id'] for row in rows]
    if len(ids) != len(set(ids)):
        raise ValueError('Duplicate catalog IDs')
    result = []
    for body, label in zip(BODY_TYPES, BODY_LABELS):
        subset = [row for row in rows if row['body_type'] == body]
        families = lambda items: {aliases.get(f"{r['brand']}|{r['model']}", f"{r['brand']} {r['model']}") for r in items}
        cells = []
        for index, price_label in enumerate(PRICE_LABELS):
            selected = [row for row in subset if price_bucket(row['price']) == index]
            cells.append({'price_band': price_label, 'configurations': len(selected),
                          'families': len(families(selected)), 'models': sorted(families(selected))})
        result.append({'body_type': body, 'label': label, 'configurations': len(subset),
                       'catalog_model_names': len({(r['brand'], r['model']) for r in subset}),
                       'families': len(families(subset)), 'bins': cells})
    if sum(row['configurations'] for row in result) != len(rows):
        raise ValueError('Unclassified body type in catalog')
    return result


def write_report(before, after, output, after_label='보충 후'):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from matplotlib.colors import LogNorm
    plt.rcParams.update({'font.family': 'Malgun Gothic', 'axes.unicode_minus': False})
    fig, axes = plt.subplots(1, 2, figsize=(18, 6), constrained_layout=True)
    vmax = max(cell['families'] for rows in (before, after) for row in rows for cell in row['bins'])
    for ax, rows, title in zip(axes, (before, after), ('보충 전', after_label)):
        matrix = [[cell['families'] for cell in row['bins']] for row in rows]
        plot = ax.imshow([[max(value, .5) for value in row] for row in matrix], cmap='Blues', norm=LogNorm(.5, max(1, vmax)), aspect='auto')
        ax.set_xticks(range(len(PRICE_LABELS)), PRICE_LABELS, rotation=25, ha='right')
        ax.set_yticks(range(7), [f"{row['label']} ({row['families']}개)" for row in rows])
        ax.set_title(f"{title} · {sum(row['configurations'] for row in rows)}개 사양", pad=15, fontsize=15)
        for y, row in enumerate(matrix):
            for x, value in enumerate(row):
                ax.text(x, y, str(value), ha='center', va='center', color='white' if value > vmax / 3 else '#172b44', fontsize=12)
    fig.suptitle('차체별 × 차량 가격대별 모델군 수', fontsize=19)
    fig.colorbar(plot, ax=axes, shrink=.8, label='모델군 수 (로그 색상 척도)')
    fig.savefig(output / 'distribution.png', dpi=160)
    plt.close(fig)
    with (output / 'distribution.csv').open('w', encoding='utf-8-sig', newline='') as stream:
        writer = csv.writer(stream)
        writer.writerow(['시점', '차체', '가격대', '모델군 수', '사양 수', '모델군 목록'])
        for stage, rows in [('before', before), ('after', after)]:
            for row in rows:
                for cell in row['bins']:
                    writer.writerow([stage, row['label'], cell['price_band'], cell['families'], cell['configurations'], '; '.join(cell['models'])])
    (output / 'distribution.json').write_text(json.dumps({'before': before, 'after': after}, ensure_ascii=False, indent=2), encoding='utf-8')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('before', 'after', 'aliases', 'output'):
        parser.add_argument('--' + name, type=Path, required=True)
    parser.add_argument('--after-label', default='보충 후')
    args = parser.parse_args()
    read = lambda path: json.loads(path.read_text(encoding='utf-8-sig'))
    aliases = read(args.aliases)
    args.output.mkdir(parents=True, exist_ok=True)
    before = summarize(read(args.before), aliases)
    after = summarize(read(args.after), aliases)
    write_report(before, after, args.output, args.after_label)
    for old, new in zip(before, after):
        print(f"{old['label']}: 모델군 {old['families']} → {new['families']}; 사양 {old['configurations']} → {new['configurations']}")


if __name__ == '__main__':
    main()
