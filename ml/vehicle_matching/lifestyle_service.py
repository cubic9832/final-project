"""Request-local pair inference after hard financial and seating constraints."""
from dataclasses import asdict, fields
import json
from pathlib import Path

import numpy as np

from vehicle_matching.catalog import Vehicle
from vehicle_matching.finance import assess
from vehicle_matching.lifestyle_features import DIMENSIONS, FEATURE_NAMES, encode, comparison_mask, effective_weights
from vehicle_matching.lifestyle_model import LifestyleRanker, digest
from vehicle_matching.service import CandidateService
from vehicle_matching.sales_evidence import load_sales_evidence, sales_display_specifications

POLICY = 'required-eligibility-then-evidence-lifestyle-ml'


def user_taste(profile, preferences):
    targets = dict.fromkeys(DIMENSIONS)
    targets.update(exterior_sportiness=preferences.get('sportiness'),
                   exterior_angularity=preferences.get('angularity'),
                   acceleration_performance=preferences.get('acceleration'))
    taste = {'targets': targets, 'purpose': preferences.get('purpose'),
             'brand': preferences.get('brand'), 'body_type': profile.preferred_body_type,
             'fuel': profile.preferred_fuel, 'size': profile.preferred_size}
    design, performance = preferences.get('design_importance', 3) * .3, preferences.get('performance_importance', 3) * .3
    importance = [design, design, 0, 0, performance, 0, 0,
                  preferences.get('purpose_importance', 3) * .3, profile.body_importance * .3,
                  profile.fuel_importance * .3, profile.space_importance * .3,
                  preferences.get('brand_importance', 3) * .3, profile.cost_importance * .1]
    return taste, importance


class RequestRanker:
    """Avoid storing per-user preferences on the shared application model."""
    def __init__(self, ranker, traits, taste, importance):
        self.ranker, self.traits, self.taste, self.importance = ranker, traits, taste, importance
        self.assumptions = ranker.assumptions
        self.mean = ranker.mean

    def score_candidates(self, profile, vehicles):
        if len(vehicles) < 2:
            return [0.] * len(vehicles), [False] * len(vehicles)
        cars = [asdict(vehicle) for vehicle in vehicles]
        costs = [assess(profile, vehicle, self.assumptions) for vehicle in vehicles]
        funds = max(1, profile.liquid_assets - profile.emergency_reserve)
        retention = [max(0, min(1, (funds - cost['total_purchase_cost']) / funds)) for cost in costs]
        rows_a, rows_b, all_weights, all_masks, pairs, fallback = [], [], [], [], [], []
        for i in range(len(cars)):
            for j in range(i + 1, len(cars)):
                a, b = (self.traits[cars[index]['id']] for index in (i, j))
                masks = comparison_mask(self.taste, a, b, all(costs[index]['eligible'] for index in (i, j)), cars[i], cars[j])
                weights = effective_weights(self.importance, masks)
                if hasattr(self.ranker, 'supported_features'):
                    weights = [weight if index in self.ranker.supported_features else 0 for index,weight in enumerate(weights)]
                # No supported preferences: report a cost-only fallback, not a learned taste claim.
                if not sum(weights):
                    fallback.append((i, j, retention[i] - retention[j]))
                    continue
                values = [encode(self.taste, traits, cars[index], retention[index]) for index, traits in ((i, a), (j, b))]
                rows_a.append(values[0]); rows_b.append(values[1])
                all_weights.append(weights); all_masks.append(masks); pairs.append((i, j))
        scores = np.zeros(len(cars), dtype=np.float64)
        if pairs:
            logits = self.ranker.pair_logits(rows_a, rows_b, all_weights, all_masks)
            for (i, j), difference in zip(pairs, logits):
                scores[i] += difference; scores[j] -= difference
        for i, j, difference in fallback:
            scores[i] += difference; scores[j] -= difference
        return (scores / (len(cars) - 1)).tolist(), [False] * len(cars)


class LifestyleService:
    policy = POLICY

    def __init__(self, ranker, catalog, traits, bundle='lifestyle-million'):
        self.ranker, self.traits, self.model_bundle = ranker, traits, bundle
        self.catalog = catalog
        self.sales_evidence = load_sales_evidence(catalog)
        if ranker.schema == 'controlled-cohort-ranker-v1':
            self.policy = 'controlled-cohort-ml-with-explicit-match-rules'
        allowed = {field.name for field in fields(Vehicle)}
        self.vehicles = [Vehicle(**{key: value for key, value in row.items() if key in allowed})
                         for row in catalog if row['provenance']['kind'] == 'existing-snapshot']
        self.brands = sorted({row['brand'] for row in catalog})

    @classmethod
    def load(cls, directory):
        directory = Path(directory)
        metadata = json.loads((directory / 'metadata.json').read_text(encoding='utf-8'))
        for name, key in (('catalog.json', 'catalog_sha256'), ('vehicle_traits.json', 'traits_sha256')):
            if digest(directory / name) != metadata['training'][key]:
                raise ValueError('Lifestyle catalog/evidence checksum mismatch')
        catalog = json.loads((directory / 'catalog.json').read_text(encoding='utf-8'))
        traits = json.loads((directory / 'vehicle_traits.json').read_text(encoding='utf-8'))['vehicles']
        if metadata['schema'] == 'controlled-cohort-ranker-v1':
            from vehicle_matching.cohort_model import CohortRanker
            return cls(CohortRanker.load(directory), catalog, traits, directory.name)
        return cls(LifestyleRanker.load(directory), catalog, traits, directory.name)

    def recommend(self, profile, k=3, lifestyle=None):
        preferences = lifestyle or {}
        cohort = self.ranker.schema == 'controlled-cohort-ranker-v1'
        if cohort and preferences.get('brand'):
            raise ValueError('새 비교군 모델은 브랜드 선호를 학습하지 않았습니다.')
        if preferences.get('brand') is not None and preferences['brand'] not in self.brands:
            raise ValueError('지원하지 않는 선호 브랜드입니다.')
        taste, importance = user_taste(profile, preferences)
        bound = RequestRanker(self.ranker, self.traits, taste, importance)
        result = CandidateService(bound, self.vehicles, ml_only=True).recommend(profile, k)
        result.update(scorePolicy=POLICY, modelBundle=self.model_bundle, trainingCatalogCount=len(self.catalog),
                      researchOnlyCount=len(self.catalog) - len(self.vehicles), appliedLifestyle=preferences)
        if cohort:
            result['scorePolicy'] = 'controlled-cohort-ml-with-explicit-match-rules'
            result['trainingScope'] = 'controlled-synthetic-policy'
            result['traitCoverage'] = {name:sum(row['values'][name] is not None for row in self.traits.values()) for name in DIMENSIONS}
            result['researchSuggestions'] = self.research_suggestions(taste,importance,min(k,6))
        for key in ('recommendations', 'conditionalRecommendations'):
            for item in result[key]:
                traits = self.traits[item['vehicle']['id']]
                item['rankingPolicy'] = self.policy
                item['lifestyleEvidence'] = {'values': traits['values'], 'evidence': traits['evidence'],
                    'specifications': traits.get('specifications'),
                    'unknownDimensions': [name for name in DIMENSIONS if traits['values'][name] is None]}
                item['reasons'].append('확인된 차량 특성과 선택하신 디자인·가속·용도 선호를 비교했습니다. 미확인 항목은 비교에서 제외합니다.' if cohort else '확인된 차량 특성과 선택하신 디자인·용도·브랜드 선호를 비교했습니다. 미확인 항목은 비교에서 제외합니다.')
        result['limitations'].extend(['디자인은 대표 모델 사진의 주관적 서열 평가입니다. 실내·승차감은 미확인입니다.',
            '가속 정보에는 합성 데이터용 추정값이 포함될 수 있습니다. estimated-acceleration은 검증된 실측 성능이 아니며 개별 근거에서 구분합니다.',
            '고급 차량 조사 후보는 구매 적격 추천에서 제외됩니다.',
            '선택한 취향에 대해 비교할 근거가 전혀 없으면 구매 후 자금 보존을 보조 기준으로 사용합니다.'])
        return result

    def research_suggestions(self,taste,importance,k):
        """Taste-only research results; never assess/claim purchase eligibility."""
        cars = [car for car in self.catalog if car['provenance']['kind']!='existing-snapshot']
        requested = [name for name,value in taste['targets'].items() if value is not None]
        # The cohort's axis pool excludes unknown observations for every target.
        # Research suggestions follow that same rule rather than letting an
        # unknown-acceleration car win neutral pair comparisons by accident.
        cars = [car for car in cars if all(self.traits[car['id']]['values'][name] is not None for name in requested)]
        scores = np.zeros(len(cars))
        a_rows,b_rows,weights_rows,masks_rows,pairs = [],[],[],[],[]
        for i,a in enumerate(cars):
            for j in range(i+1,len(cars)):
                b = cars[j]
                ta,tb = self.traits[a['id']],self.traits[b['id']]
                masks = comparison_mask(taste,ta,tb,False,a,b)
                weights = [w if n in self.ranker.supported_features else 0 for n,w in enumerate(effective_weights(importance,masks))]
                if not sum(weights):
                    continue
                a_rows.append(encode(taste,ta,a,0));b_rows.append(encode(taste,tb,b,0))
                weights_rows.append(weights);masks_rows.append(masks);pairs.append((i,j))
        if not pairs:
            return []
        if pairs:
            for (i,j),value in zip(pairs,self.ranker.pair_logits(a_rows,b_rows,weights_rows,masks_rows)):
                scores[i]+=value;scores[j]-=value
        selected,seen = [],set()
        for index in sorted(range(len(cars)),key=lambda i:(-scores[i],cars[i]['id'])):
            car = cars[index]
            if (car['brand'],car['model']) in seen:
                continue
            seen.add((car['brand'],car['model']))
            selected.append({'vehicle':car,'rankingScore':float(scores[index]/max(1,len(cars)-1)),
                'financialEligible':None,'comparisonScope':'taste-only',
                'evidence':self.traits[car['id']]['evidence'],
                'salesVerification':self.sales_evidence.get(car['id']),
                'specifications':sales_display_specifications(
                    self.traits[car['id']].get('specifications'), self.sales_evidence.get(car['id']))})
            if len(selected)>=k:
                break
        return selected
