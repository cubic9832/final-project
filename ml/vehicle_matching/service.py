"""Hard financial eligibility precedes ML. No eligible candidates is a valid result."""
from collections import Counter
from dataclasses import asdict, replace

from vehicle_matching.explanations import candidate_evidence, evaluation_summary, ranking_comparison
from vehicle_matching.finance import assess
from vehicle_matching.preferences import assumes_standard_seating, exclusions, integrated_score
from vehicle_matching.budget import recommendation_budget, budget_order, apply_budget_preference


class CandidateService:
    def __init__(self, ranker, vehicles):
        self.ranker = ranker
        self.vehicles = vehicles

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
        candidates = eligible
        band = recommendation_budget(profile,eligible,costs)
        candidates = [v for v in candidates if v.price<=band['upper']]
        scores, outside = self.ranker.predict(profile, candidates)
        combined = {v.id: apply_budget_preference(integrated_score(profile, v, costs[v.id], score), v, band)
                    for v, score in zip(candidates, scores)}
        ordered = sorted(zip(candidates, scores, outside), key=lambda row: budget_order(row[0],combined[row[0].id]['total'],band))
        chosen, models = [], set()
        # One configuration per model; never fill remaining slots with infeasible vehicles.
        for vehicle, score, out_of_range in ordered:
            key = (vehicle.brand, vehicle.model)
            if key in models:
                continue
            models.add(key)
            cost = costs[vehicle.id]
            reasons = [f"차량 비용 지출 후 월 잔여 자금 {cost['remaining_monthly']:,.0f}원",
                       f"예상 월 유지비 {cost['monthly_running_cost']:,.0f}원 (보험·세금·정비·에너지비 포함)"]
            affordability=combined[vehicle.id]['monthlyAffordability']
            reasons.append(f"최소 여유자금을 남긴 월 가용자금 중 유지비 비중 {affordability['runningCostRatio']*100:.1f}%")
            reasons.append('구매·유지 가능 조건 안에서 비용 부담과 선택한 선호를 함께 평가한 후보')
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
            target.append({'vehicle': vehicle_data, 'rankingScore': round(score, 6), 'cost': public_cost,
                           'integratedScore': combined[vehicle.id],
                           'decisionEvidence': candidate_evidence(profile, vehicle, cost, combined[vehicle.id]),
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
        return {'modelVersion': 'candidate-v2', 'objective': 'financial-eligibility-and-weighted-preferences',
                'scorePolicy': 'cash-preference-weighted-v9',
                'evaluationSummary': evaluation_summary(profile, self.vehicles, eligible, costs, combined),
                'appliedPreferences': {name: getattr(profile, name) for name in ('preferred_body_type', 'body_importance', 'preferred_fuel', 'preferred_size', 'minimum_seats', 'cost_importance', 'space_importance', 'fuel_importance', 'seating_importance')},
                'budgetPolicy': band,
                'catalogCount': len(self.vehicles), 'eligibleCount': len(eligible),
                'excludedReasons': dict(excluded), 'recommendations': chosen,
                'conditionalRecommendations': [],
                'seatingUnverifiedCount': sum('seats-unverified' in exclusions(profile,v) or
                                             bool(profile.minimum_seats and v.seats is None and not v.seat_options) for v in eligible),
                'financialEligibleModelCount': len({(v.brand,v.model) for v in eligible}),
                'status': 'recommended' if chosen else 'no-financially-eligible-vehicle',
                'assumptions': {**self.ranker.assumptions.to_dict(), 'recommendation_financing':'cash-only',
                                'recommendation_months':0,'recommendation_annual_rate':0},
                'limitations': ['가정 기반 합성 효용을 학습한 실험 점수이며 만족도·구매 확률이 아닙니다.',
                                '가격은 수집 시점의 자동 추출 스냅샷이며 현재 판매·최종 견적 확인이 필요합니다.',
                                '연비 미확인 후보는 명시한 연료별 범위로 비용을 추정합니다.',
                                '크기는 전장 기준의 선호 일치도이며 실내 공간·안전 평가는 아닙니다.',
                                '통합 점수는 사용자 가중치와 기존 ML 점수를 합친 정책 점수이며 확률이 아닙니다.']}
