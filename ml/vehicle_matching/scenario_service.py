"""Bind request preferences to the scenario model without shared mutable state."""
from dataclasses import asdict
from pathlib import Path

import numpy as np

from vehicle_matching.catalog import read_catalog
from vehicle_matching.finance import Assumptions, assess
from vehicle_matching.scenario_features import encode_scenario
from vehicle_matching.scenario_model import ScenarioRanker
from vehicle_matching.scenario_traits import ScenarioCandidateService, load_traits, taste_matches

POLICY = 'required-eligibility-then-scenario-ml'


def scenario_user(profile, preferences):
    cost = profile.cost_importance/5
    weights = [cost,cost*min(1.5,max(.4,profile.annual_distance/15000)),profile.body_importance/5,
               profile.fuel_importance/5,profile.space_importance/5,
               0.,0.,
               .15 if profile.charging_available else .7]
    if preferences.get('asset_retention_importance') is not None:
        weights[0] = preferences['asset_retention_importance'] / 5
    if preferences.get('running_cost_importance') is not None:
        weights[1] = preferences['running_cost_importance'] / 5 * min(1.5,max(.4,profile.annual_distance/15000))
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
        self.traits = load_traits(vehicles)

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
        allowed = {'sportiness', 'angularity', 'acceleration', 'design_importance', 'performance_importance',
                   'asset_retention_importance', 'running_cost_importance'}
        if set(preferences) - allowed:
            raise ValueError('지원하지 않는 성향 입력입니다.')
        bound = BoundScenarioRanker(self.ranker,preferences)
        result = ScenarioCandidateService(bound,self.vehicles,self.traits,preferences).recommend(profile,k)
        explicit = any(preferences.get(key) is not None for key in ('sportiness', 'angularity', 'acceleration'))
        policy = 'explicit-trait-match-then-scenario-ml' if explicit else self.policy
        result.update(modelVersion='scenario-v1',modelBundle=self.model_bundle,scorePolicy=self.policy,
                      trainingCatalogCount=len(self.vehicles),appliedScenario=preferences, rankingPolicy=policy,
                      traitCoverage={key: len(self.vehicles) for key in ('exterior_sportiness', 'exterior_angularity', 'acceleration_performance')})
        for key in ('recommendations','conditionalRecommendations'):
            for item in result[key]:
                item['rankingPolicy'] = policy
                traits = self.traits[item['vehicle']['id']]
                item['lifestyleEvidence'] = {'values': traits['values'], 'evidence': traits['evidence']}
                item['tasteMatches'] = taste_matches(preferences, traits)
                if explicit:
                    item['rankingComparison'] = {'status': 'explicit-trait-match'}
                    item['reasons'] = [reason for reason in item['reasons'] if '학습한 모델 점수순' not in reason]
                    item['reasons'].append('외관·윤곽·가속 성향의 중요도별 일치도를 먼저 비교하고 동률이면 학습 모델 점수로 정렬했습니다.')
        for item in result['conditionalRecommendations']:
            item.update(rankingScore=None, rankingScoreType='not-scored',
                        rankingPolicy='seating-verification-required', rankingComparison={'status': 'unavailable'})
            item['reasons'].append('필수 좌석 사양을 확인해야 하므로 학습 모델 점수는 계산하지 않았습니다.')
        result['limitations'].append('외관·윤곽은 주관적 평가 또는 차체별 자체 기준값이며 가속은 공식 수치와 미검증 추정값을 구분합니다.')
        if explicit:
            result['limitations'] = [text for text in result['limitations'] if '선호 간 절충은 학습된 모델 점수' not in text]
            result['limitations'].append('외관·윤곽·가속 선호는 기존 모델이 학습하지 않은 명시적 일치도 정렬입니다. rankingScore는 이 항목들을 학습한 점수가 아닙니다.')
        return result
