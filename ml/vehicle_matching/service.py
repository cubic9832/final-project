"""Hard financial eligibility precedes ML. No eligible candidates is a valid result."""
from collections import Counter
from dataclasses import asdict, replace
import math

from vehicle_matching.explanations import candidate_evidence, evaluation_summary, ranking_comparison
from vehicle_matching.finance import assess
from vehicle_matching.preferences import assumes_standard_seating, exclusions, preference_assessment
from vehicle_matching.budget import recommendation_budget
from vehicle_matching.recommendation_policy import POLICY, seating_status, ranking_key, preference_penalties


class CandidateService:
    def __init__(self, ranker, vehicles, *, ml_only=False):
        self.ranker = ranker
        self.vehicles = vehicles
        self.ml_only = ml_only
        self.policy = 'required-eligibility-then-ml-only-experimental' if ml_only else POLICY

    def ranking_key(self, profile, vehicle, score):
        return (-score, vehicle.id) if self.ml_only else ranking_key(profile, vehicle, score)

    def recommend(self, profile, k=3):
        if not 1 <= k <= 20:
            raise ValueError('k must be between 1 and 20')
        # The existing trained feature layout requires a purpose value. Use one
        # fixed baseline for everyone; old user purpose must not affect ranking.
        profile = replace(profile, down_payment=0, months=0, annual_rate=0, financing_mode='recommendation', purpose='commute', purpose_importance=1)
        eligible, costs, excluded = [], {}, Counter()
        for vehicle in self.vehicles:
            cost = assess(profile, vehicle, self.ranker.assumptions)
            if cost['eligible']:
                eligible.append(vehicle)
                costs[vehicle.id] = cost
            else:
                excluded.update(cost['exclusions'])
        seating_unknown = [v for v in eligible if seating_status(profile,v) == 'unknown']
        seating_rejected = [v for v in eligible if seating_status(profile,v) == 'insufficient']
        candidates = [v for v in eligible if seating_status(profile,v) == 'match']
        band = recommendation_budget(profile,eligible,costs)
        candidates = [v for v in candidates if v.price<=band['upper']]
        scores, outside = self.ranker.score_candidates(profile, candidates)
        if len(scores) != len(candidates) or len(outside) != len(candidates) or not all(math.isfinite(s) for s in scores):
            raise ValueError('Invalid ML ranking scores')
        assessments = {v.id: preference_assessment(profile, v, costs[v.id]) for v in eligible}
        ordered = sorted(zip(candidates, scores, outside), key=lambda row: self.ranking_key(profile,row[0],row[1]))
        chosen, models = [], set()
        # One configuration per model; never fill remaining slots with infeasible vehicles.
        for vehicle, score, out_of_range in ordered:
            if len(chosen) >= k: break
            key = (vehicle.brand, vehicle.model)
            if key in models:
                continue
            models.add(key)
            cost = costs[vehicle.id]
            reasons = [f"차량 비용 지출 후 월 잔여 자금 {cost['remaining_monthly']:,.0f}원",
                       f"예상 월 유지비 {cost['monthly_running_cost']:,.0f}원 (보험·세금·정비·에너지비 포함)"]
            affordability=assessments[vehicle.id]['monthlyAffordability']
            reasons.append(f"최소 여유자금을 남긴 월 가용자금 중 유지비 비중 {affordability['runningCostRatio']*100:.1f}%")
            reasons.append('구매·유지비와 최소 인원을 충족한 후보 중 학습한 모델 점수순으로 추천' if self.ml_only else
                           '구매·유지비와 최소 인원을 충족한 후보 중 중요한 선호 조건을 우선하고, 같은 조건에서는 모델 점수순으로 추천')
            if profile.preferred_fuel == vehicle.fuel:
                reasons.append('선택한 선호 연료와 일치')
            if vehicle.efficiency_reference_only:
                reasons.append('기본 사양의 정확한 연비 확인이 필요해 공개 인증 사양의 연비를 참조했습니다.')
            gaps = exclusions(profile, vehicle)
            if profile.minimum_seats and vehicle.seats is None and not vehicle.seat_options and 'seats-unverified' not in gaps:
                gaps.append('seats-unverified')
            reasons.extend({'insufficient-seats':'선호 탑승 인원보다 좌석이 적은 절충 후보',
                            'seats-unverified':'좌석 사양 확인 필요', 'length-unverified':'전장 제원 확인 필요'}[gap] for gap in gaps)
            target = chosen
            if len(target) >= k:
                continue
            vehicle_data = asdict(vehicle)
            vehicle_data['assumed_seat_range'] = [2, 4] if assumes_standard_seating(vehicle) else None
            public_cost = {key: value for key, value in cost.items() if not key.startswith('stress_') and key not in ('principal', 'monthly_payment')}
            target.append({'vehicle': vehicle_data, 'rankingScore': score, 'cost': public_cost,
                           'rankingScoreType': 'ml-raw',
                           'rankingPolicy': self.policy,
                           'preferencePriority': [{'key':key,'importance':weight,'penalty':penalty} for key,weight,penalty in preference_penalties(profile,vehicle)],
                           'preferenceCompromise': any(p > 0 for _,_,p in preference_penalties(profile,vehicle)),
                           'preferenceAssessment': assessments[vehicle.id],
                           'decisionEvidence': candidate_evidence(profile, vehicle, cost, assessments[vehicle.id]),
                           'seatingVerificationRequired': 'seats-unverified' in gaps,
                           'lengthVerificationRequired': 'length-unverified' in gaps,
                           'preferenceGaps': gaps,
                           'budgetTier': 'within-financial-ceiling',
                           'reasons': reasons, 'outsideTrainingRange': out_of_range})
        for index, item in enumerate(chosen):
            if len(chosen) > 1:
                higher, lower = (item, chosen[index + 1]) if index < len(chosen) - 1 else (chosen[index - 1], item)
                item['rankingComparison'] = ranking_comparison(higher, lower)
            else:
                item['rankingComparison'] = {'status': 'only-candidate'}
        conditional = []
        unknown_scores, unknown_outside = self.ranker.score_candidates(profile,seating_unknown)
        if len(unknown_scores) != len(seating_unknown) or len(unknown_outside) != len(seating_unknown) or not all(math.isfinite(s) for s in unknown_scores):
            raise ValueError('Invalid conditional ML ranking scores')
        unknown_rows = sorted(zip(seating_unknown,unknown_scores,unknown_outside), key=lambda row: self.ranking_key(profile,row[0],row[1]))
        seen_unknown = set()
        for v, score, outside in unknown_rows:
            model = (v.brand,v.model)
            if model in seen_unknown or model in models or len(conditional) >= k: continue
            seen_unknown.add(model)
            assessment = preference_assessment(profile,v,costs[v.id])
            for component in assessment['components']:
                if component['key'] == 'seating': component['verified'] = False
            evidence = candidate_evidence(profile,v,costs[v.id],assessment)
            for item in evidence['preferences']:
                if item['key'] == 'seating': item['status'] = 'unknown'
            conditional.append({'vehicle':asdict(v),'rankingScore':score,'rankingScoreType':'ml-raw','rankingPolicy':self.policy,
                'cost':{key:value for key,value in costs[v.id].items() if not key.startswith('stress_') and key not in ('principal','monthly_payment')},
                'preferenceAssessment':assessment,'decisionEvidence':evidence,'seatingVerificationRequired':True,
                'lengthVerificationRequired':v.length_mm is None,'preferenceGaps':['seats-unverified'],
                'reasons':['기본 정원 또는 사양 충돌을 확인하기 전에는 최소 인원 충족을 보장할 수 없습니다.'],
                'outsideTrainingRange':bool(outside),'rankingComparison':{'status':'only-candidate'}})
        return {'modelVersion' : 'candidate-v2', 'objective': 'financial-eligibility-and-ml-ranking',
                'scorePolicy': self.policy,
                'evaluationSummary': evaluation_summary(profile, self.vehicles, eligible, costs, assessments),
                'appliedPreferences': {name: getattr(profile, name) for name in ('preferred_body_type', 'body_importance', 'preferred_fuel', 'preferred_size', 'minimum_seats', 'cost_importance', 'space_importance', 'fuel_importance', 'seating_importance')},
                'budgetPolicy': band,
                'catalogCount': len(self.vehicles), 'eligibleCount': len(eligible),
                'excludedReasons': dict(excluded), 'recommendations': chosen,
                'conditionalRecommendations': conditional,
                'seatingUnverifiedCount': sum('seats-unverified' in exclusions(profile,v) or
                                             bool(profile.minimum_seats and v.seats is None and not v.seat_options) for v in eligible),
                'financialEligibleModelCount': len({(v.brand,v.model) for v in eligible}),
                'seatingExcludedCount': len(seating_rejected), 'seatingUnverifiedCandidatesCount': len(seating_unknown),
                'status': 'recommended' if chosen else 'no-required-seating-match' if eligible else 'no-financially-eligible-vehicle',
                'assumptions': {**self.ranker.assumptions.to_dict(), 'recommendation_financing':'cash-only',
                                'recommendation_months':0,'recommendation_annual_rate':0},
                'limitations': ['가정 기반 합성 효용을 학습한 실험 점수이며 만족도·구매 확률이 아닙니다.',
                                '가격은 수집 시점의 자동 추출 스냅샷이며 현재 판매·최종 견적 확인이 필요합니다.',
                                '연비 미확인 후보는 명시한 연료별 범위로 비용을 추정합니다.',
                                '크기는 전장 기준의 선호 일치도이며 실내 공간·안전 평가는 아닙니다.',
                                '최소 정원은 필수 조건입니다. 선호 간 절충은 학습된 모델 점수에 반영됩니다.' if self.ml_only else
                                '최소 정원은 필수 조건입니다. 선호는 중요도순으로 비교하며 같은 중요도에서는 불일치 정도를 합산하고 동률일 때 ML 원본 점수로 정렬합니다.']}
