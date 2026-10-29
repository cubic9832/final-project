"""Bind request preferences to the scenario model without shared mutable state."""
from dataclasses import asdict
from pathlib import Path

import numpy as np

from vehicle_matching.catalog import read_catalog
from vehicle_matching.finance import Assumptions, assess
from vehicle_matching.scenario_features import encode_scenario
from vehicle_matching.scenario_model import ScenarioRanker
from vehicle_matching.service import CandidateService

POLICY = 'required-eligibility-then-scenario-ml'


def scenario_user(profile, preferences):
    cost = profile.cost_importance/5
    weights = [cost,cost*min(1.5,max(.4,profile.annual_distance/15000)),profile.body_importance/5,
               profile.fuel_importance/5,profile.space_importance/5,
               0.,0.,
               .15 if profile.charging_available else .7]
    return {'profile':asdict(profile),'preferred_brands':[],
            'model_affinities':{},'channel_weights':weights}


class BoundScenarioRanker:
    def __init__(self, ranker, preferences):
        self.ranker,self.preferences = ranker,preferences
        self.assumptions = Assumptions()
        self.mean = ranker.mean

    def score_candidates(self, profile, vehicles):
        user = scenario_user(profile,self.preferences)
        scores = self.ranker.score_candidates(user,vehicles)
        if not vehicles:
            return [],[]
        features = np.stack([encode_scenario(user,profile,v,assess(profile,v)) for v in vehicles])
        outside = np.any((features<self.ranker.minimum-1e-5)|(features>self.ranker.maximum+1e-5),axis=1)
        return scores,outside.tolist()


class ScenarioService:
    policy = POLICY

    def __init__(self,ranker,vehicles,bundle):
        self.ranker,self.vehicles,self.model_bundle = ranker,vehicles,bundle
        self.catalog = vehicles
        self.brands = sorted({v.brand for v in vehicles})
        self.models = sorted({v.model for v in vehicles})
        self.ranker.assumptions = Assumptions()

    @classmethod
    def load(cls,directory):
        path = Path(directory)
        import json
        metadata = json.loads((path/'metadata.json').read_text(encoding='utf-8'))
        if metadata['training'].get('dataset_version')!='scenario-population-v3':
            raise ValueError('Broad-taste serving requires the v3 retrained model')
        return cls(ScenarioRanker.load(path),read_catalog(path/'catalog.json'),path.name)

    def recommend(self,profile,k=3,preferences=None):
        preferences = preferences or {}
        if preferences:
            raise ValueError('브랜드나 차량 모델을 지정하는 선호 입력은 받지 않습니다.')
        bound = BoundScenarioRanker(self.ranker,preferences)
        result = CandidateService(bound,self.vehicles,ml_only=True).recommend(profile,k)
        result.update(modelVersion='scenario-v1',modelBundle=self.model_bundle,scorePolicy=self.policy,
                      trainingCatalogCount=len(self.vehicles),appliedScenario=preferences)
        for key in ('recommendations','conditionalRecommendations'):
            for item in result[key]:
                item['rankingPolicy'] = self.policy
        return result
