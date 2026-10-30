"""Explicit taste matching alongside, and separate from, saved model scores."""
import json

from vehicle_matching.catalog import ROOT
from vehicle_matching.service import CandidateService

TRAIT_FIELDS = {'sportiness': 'exterior_sportiness', 'angularity': 'exterior_angularity',
                'acceleration': 'acceleration_performance'}
LABELS = {'sportiness': '외관 스타일', 'angularity': '차체 윤곽', 'acceleration': '가속 성능'}


def load_traits(vehicles):
    path = ROOT / 'data/vehicles/scenario-traits-20261030/vehicle_traits.json'
    rows = json.loads(path.read_text(encoding='utf-8'))['vehicles']
    for vehicle in vehicles:
        row = rows.get(vehicle.id)
        if row is None or any(row['values'].get(key) is None for key in TRAIT_FIELDS.values()):
            raise ValueError(f'Incomplete scenario traits: {vehicle.id}')
    return rows


def taste_matches(preferences, row):
    matches = []
    for name, dimension in TRAIT_FIELDS.items():
        target = preferences.get(name)
        if target is None:
            continue
        weight = preferences.get('performance_importance' if name == 'acceleration' else 'design_importance', 3)
        actual = row['values'][dimension]
        matches.append({'key': name, 'label': LABELS[name], 'requested': target, 'actual': actual,
                        'weight': weight, 'match': 1 - abs(target - actual),
                        'evidenceKind': row['evidence'][dimension]['kind']})
    return matches


class ScenarioCandidateService(CandidateService):
    def __init__(self, ranker, vehicles, traits, preferences):
        super().__init__(ranker, vehicles, ml_only=True)
        self.traits, self.preferences = traits, preferences

    def score_conditional_candidates(self, profile, vehicles):
        # Unverified/optional seating cannot enter the strict trained ranker.
        # Neutral internal sort keys preserve a separate configuration-review list.
        return [0.] * len(vehicles), [False] * len(vehicles)

    def ranking_key(self, profile, vehicle, score):
        matches = taste_matches(self.preferences, self.traits[vehicle.id])
        if not matches:
            return super().ranking_key(profile, vehicle, score)
        matching = sum(item['weight'] * item['match'] for item in matches) / sum(item['weight'] for item in matches)
        # Explicit preferences order all eligible configurations before top-k/model deduplication.
        # The saved model score remains unchanged and is the secondary criterion.
        return (-matching, -score, vehicle.id)
