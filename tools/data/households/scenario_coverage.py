"""Coverage-aware candidate sampling without changing users or forcing winners."""
from collections import Counter


def model_key(vehicle):
    return f'{vehicle.brand}::{vehicle.model}'


def select_candidates(pool, rng, model_counts, spec_counts, model_minimum, spec_minimum, pool_size, pair_count):
    families = list(pool)
    rng.shuffle(families)
    # Low-exposure eligible models are considered first; eligibility was already checked.
    deficits = [f for f in families if model_counts[model_key(pool[f][0][1])] < model_minimum
                or any(spec_counts[v.id] < spec_minimum for _,v,_ in pool[f])]
    deficits.sort(key=lambda f:model_counts[model_key(pool[f][0][1])])
    selected = deficits[:min(pool_size, 2*pair_count)]
    remaining = [f for f in families if f not in selected]
    selected += remaining[:max(0,pool_size-len(selected))]
    candidates, required = [], []
    for family in selected:
        entries = pool[family]
        missing = [row for row in entries if spec_counts[row[1].id] < spec_minimum]
        candidate = rng.choice(missing or entries)
        if len(required)<2*pair_count and (model_counts[model_key(candidate[1])] < model_minimum
                                          or spec_counts[candidate[1].id] < spec_minimum):
            required.append(len(candidates))
        candidates.append(candidate)
    return candidates, required


def coverage_report(catalog, model_counts, spec_counts, model_minima, spec_minimum):
    models = sorted({model_key(v) for v in catalog})
    missing = {role:{name:model_counts[role][name] for name in models if model_counts[role][name] < minimum}
               for role,minimum in model_minima.items()}
    missing_specs = {v.id:spec_counts[v.id] for v in catalog if spec_counts[v.id] < spec_minimum}
    return {'status':'passed' if not any(missing.values()) and not missing_specs else 'failed',
            'catalog_models':len(models),'catalog_specifications':len(catalog),
            'minimum_model_comparisons':model_minima,'minimum_spec_comparisons':spec_minimum,
            'models_by_split':{r:{name:counts[name] for name in models} for r,counts in model_counts.items()},
            'specifications':{v.id:spec_counts[v.id] for v in catalog},
            'missing_models_by_split':missing,'missing_specifications':missing_specs}
