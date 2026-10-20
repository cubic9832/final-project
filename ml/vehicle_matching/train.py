"""python -m vehicle_matching.train --output ml/experiments/candidate-v2"""
import argparse
import hashlib
import json
from dataclasses import replace
from pathlib import Path

from vehicle_matching.catalog import DEFAULT_CSV, catalog_fingerprint, load_csv, save_catalog
from vehicle_matching.dataset import pair_data, profiles
from vehicle_matching.evaluate import evaluate
from vehicle_matching.finance import Assumptions
from vehicle_matching.model import PairRanker, fit_pairs


def train(output, csv_path=DEFAULT_CSV, seed=42):
    output = Path(output)
    if (output / 'model.pt').exists():
        raise ValueError('Output already has a model; choose a new directory')
    vehicles, catalog_report = load_csv(csv_path)
    # Hold out whole brand/model identities, not merely trims of the same vehicle.
    keys = sorted({(v.brand, v.model) for v in vehicles})
    held_out = {key for i, key in enumerate(keys) if i % 5 == 0}
    seen = [v for v in vehicles if (v.brand, v.model) not in held_out]
    unseen = [v for v in vehicles if (v.brand, v.model) in held_out]
    train_people, valid_people, test_people = profiles(600, seed), profiles(150, seed + 1000), profiles(200, seed + 2000)
    features, targets, pairs = pair_data(train_people, seen, seed)
    choices = []
    for epochs in (30, 60):
        model, history = fit_pairs(features, targets, pairs, seed=seed, epochs=epochs)
        validation = evaluate(model, valid_people, seen)
        choices.append((model, history, validation, epochs))
    best, history, validation, epochs = max(choices, key=lambda item: item[2]['teacher_ndcg_at_3'] or 0)
    report = {'schema': 'candidate-v2', 'seed': seed, 'catalog': catalog_report,
              'source_code_sha256': hashlib.sha256(b''.join(p.read_text(encoding='utf-8').encode('utf-8') for p in sorted(Path(__file__).parent.glob('*.py')))).hexdigest(),
              'data': {'kind': 'independent-synthetic-profiles', 'training_profiles': len(train_people),
                       'validation_profiles': len(valid_people), 'test_profiles': len(test_people),
                       'training_pair_rows': len(features), 'training_preferences': len(pairs),
                       'profile_seeds': [seed, seed + 1000, seed + 2000],
                       'held_out_models': [list(key) for key in sorted(held_out)]},
              'objective': {'teacher': 'vehicle_matching.features.utility', 'preference_weight': 0.25,
                            'meaning': 'Cost buffer / running expense / fuel-preference utility under explicit assumptions',
                            'not_claimed': 'Observed satisfaction, real purchase probability, or loan eligibility'},
              'selection': {'selected_epochs': epochs,
                            'validation_candidates': [{'epochs': e, **v} for _, _, v, e in choices]},
              'validation': validation, 'test_seen_models': evaluate(best, test_people, seen),
              'test_unseen_models': evaluate(best, test_people, unseen),
              'test_all_models': evaluate(best, test_people, vehicles), 'history': history,
              'sensitivity': {}}
    for weight in (0.1, 0.5):
        report['sensitivity'][f'teacher_preference_weight_{weight}'] = evaluate(best, test_people, vehicles, weight)
    shifted = replace(Assumptions(), monthly_insurance=150000, stress_rate_addition=0.05,
                      energy_prices=tuple(value * 1.25 for value in Assumptions().energy_prices))
    shifted_model = PairRanker(best.net, best.mean, best.scale, best.minimum, best.maximum, shifted)
    report['sensitivity']['higher_energy_insurance_interest'] = evaluate(shifted_model, test_people, vehicles)
    for label, subset in [('income_below_3m', [p for p in test_people if p.monthly_income < 3000000]),
                          ('income_3m_to_6m', [p for p in test_people if 3000000 <= p.monthly_income < 6000000]),
                          ('income_above_6m', [p for p in test_people if p.monthly_income >= 6000000])]:
        report['sensitivity'][label] = evaluate(best, subset, vehicles)
    output.mkdir(parents=True, exist_ok=True)
    save_catalog(output / 'catalog.json', vehicles)
    report['catalog_sha256'] = catalog_fingerprint(output / 'catalog.json')
    best.save(output, {'seed': seed, 'epochs': epochs, 'catalog_sha256': report['catalog_sha256'],
                       'target': report['objective'], 'data': report['data']})
    (output / 'report.json').write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps({key: report[key] for key in ('catalog', 'test_all_models', 'test_unseen_models')}, ensure_ascii=True))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Train an experimental user–vehicle pairwise ranker')
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--catalog-csv', type=Path, default=DEFAULT_CSV)
    parser.add_argument('--seed', type=int, default=42)
    args = parser.parse_args()
    train(args.output, args.catalog_csv, args.seed)
