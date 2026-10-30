"""Hard eligibility followed only by the retrained UI model's score."""
from dataclasses import asdict
import json
from pathlib import Path
import numpy as np
from vehicle_matching.catalog import read_catalog
from vehicle_matching.finance import assess
from vehicle_matching.service import CandidateService
from vehicle_matching.scenario_traits import taste_matches
from vehicle_matching.ui_scenario_model import UiScenarioRanker
from vehicle_matching.ui_scenario_features import FEATURE_NAMES, encode_ui_scenario

POLICY = 'required-eligibility-then-ui-scenario-ml'


class BoundUiRanker:
    def __init__(self, ranker, preferences):
        self.ranker,self.preferences=ranker,preferences
        self.mean,self.assumptions=ranker.mean,ranker.assumptions

    def score_candidates(self, profile, vehicles):
        user={'profile':asdict(profile),'preferences':self.preferences}
        scores=self.ranker.score_candidates(user,vehicles)
        if not vehicles:return [],[]
        rows=np.stack([encode_ui_scenario(user,vehicle,self.ranker.traits[vehicle.id],assess(profile,vehicle)) for vehicle in vehicles])
        outside=np.any((rows<self.ranker.minimum-1e-5)|(rows>self.ranker.maximum+1e-5),axis=1)
        return scores,outside.tolist()


class UiCandidateService(CandidateService):
    def score_conditional_candidates(self, profile, vehicles):
        return [0.] * len(vehicles), [False] * len(vehicles)


class UiScenarioService:
    policy=POLICY

    def __init__(self,ranker,vehicles,bundle):
        self.ranker,self.vehicles,self.model_bundle=ranker,vehicles,bundle
        self.catalog=vehicles;self.traits=ranker.traits
        self.brands=sorted({vehicle.brand for vehicle in vehicles})

    @classmethod
    def load(cls,directory):
        path=Path(directory)
        meta=json.loads((path/'metadata.json').read_text(encoding='utf-8'))
        if meta['training']['dataset_version']!='ui-scenario-population-v1':raise ValueError('UI dataset version mismatch')
        return cls(UiScenarioRanker.load(path),read_catalog(path/'catalog.json'),path.name)

    def recommend(self,profile,k=3,preferences=None):
        preferences=preferences or {}
        bound=BoundUiRanker(self.ranker,preferences)
        result=UiCandidateService(bound,self.vehicles,ml_only=True).recommend(profile,k)
        result.update(modelVersion='scenario-v1',modelBundle=self.model_bundle,scorePolicy=POLICY,rankingPolicy=POLICY,
                      featureCount=len(FEATURE_NAMES),trainingCatalogCount=len(self.vehicles),appliedScenario=preferences,
                      traitCoverage={name:len(self.vehicles) for name in ('exterior_angularity','acceleration_performance')})
        for key in ('recommendations','conditionalRecommendations'):
            for item in result[key]:
                traits=self.traits[item['vehicle']['id']]
                item['lifestyleEvidence']={'values':traits['values'],'evidence':traits['evidence']}
                item['tasteMatches']=taste_matches(preferences,traits)
                item['rankingPolicy']=POLICY
                if key=='conditionalRecommendations':
                    item.update(rankingScore=None,rankingScoreType='not-scored',rankingPolicy='seating-verification-required',rankingComparison={'status':'unavailable'})
        return result
