"""Measure teacher agreement separately from deterministic constraint compliance."""
import math

import numpy as np

from vehicle_matching.features import utility
from vehicle_matching.finance import assess


def evaluate(ranker, people, vehicles, preference_weight=0.25):
    model_ndcg, cost_ndcg, regrets = [], [], []
    recommended_models, available_models = set(), {(v.brand, v.model) for v in vehicles}
    eligible_people = 0
    for person in people:
        eligible = [v for v in vehicles if assess(person, v, ranker.assumptions)['eligible']]
        if not eligible:
            continue
        eligible_people += 1
        scores, _ = ranker.predict(person, eligible)
        targets = [utility(person, v, ranker.assumptions, preference_weight) for v in eligible]

        def distinct_order(values):
            seen, result = set(), []
            for i in sorted(range(len(eligible)), key=lambda i: (-values[i], eligible[i].id)):
                key = (eligible[i].brand, eligible[i].model)
                if key not in seen:
                    result.append(i)
                    seen.add(key)
                if len(result) == 3:
                    break
            return result

        ideal = distinct_order(targets)
        predicted = distinct_order(scores)
        costs = [-assess(person, v, ranker.assumptions)['monthly_total'] for v in eligible]
        baseline = distinct_order(costs)

        def dcg(order):
            return sum((2 ** targets[i] - 1) / math.log2(position + 2) for position, i in enumerate(order))

        denominator = dcg(ideal)
        model_ndcg.append(dcg(predicted) / denominator if denominator else 1)
        cost_ndcg.append(dcg(baseline) / denominator if denominator else 1)
        regrets.append(float(np.mean([targets[i] for i in ideal]) - np.mean([targets[i] for i in predicted])))
        recommended_models.update((eligible[i].brand, eligible[i].model) for i in predicted)
    return {'profiles': len(people), 'profiles_with_eligible_candidates': eligible_people,
            'profiles_without_candidates': len(people) - eligible_people,
            'teacher_ndcg_at_3': float(np.mean(model_ndcg)) if model_ndcg else None,
            'teacher_rule_baseline_ndcg_at_3': 1.0 if model_ndcg else None,
            'cost_only_baseline_ndcg_at_3': float(np.mean(cost_ndcg)) if cost_ndcg else None,
            'mean_teacher_utility_regret_at_3': float(np.mean(regrets)) if regrets else None,
            'recommended_model_names': len(recommended_models), 'available_model_names': len(available_models),
            'meaning': 'Agreement with a declared synthetic utility; not real-world relevance or satisfaction.'}
