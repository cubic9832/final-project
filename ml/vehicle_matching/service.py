"""Hard financial eligibility precedes ML. No eligible candidates is a valid result."""
from collections import Counter
from dataclasses import asdict

from vehicle_matching.finance import assess
from vehicle_matching.preferences import exclusions, integrated_score


class CandidateService:
    def __init__(self, ranker, vehicles):
        self.ranker = ranker
        self.vehicles = vehicles

    def recommend(self, profile, k=3):
        if not 1 <= k <= 20:
            raise ValueError('k must be between 1 and 20')
        eligible, costs, excluded = [], {}, Counter()
        for vehicle in self.vehicles:
            cost = assess(profile, vehicle, self.ranker.assumptions)
            preference_errors = exclusions(profile, vehicle)
            cost['exclusions'].extend(preference_errors)
            cost['eligible'] = not cost['exclusions']
            if cost['eligible']:
                eligible.append(vehicle)
                costs[vehicle.id] = cost
            else:
                excluded.update(cost['exclusions'])
        scores, outside = self.ranker.predict(profile, eligible)
        combined = {v.id: integrated_score(profile, v, costs[v.id], score) for v, score in zip(eligible, scores)}
        ordered = sorted(zip(eligible, scores, outside), key=lambda row: (-combined[row[0].id]['total'], row[0].id))
        chosen, models = [], set()
        # One configuration per model; never fill remaining slots with infeasible vehicles.
        for vehicle, score, out_of_range in ordered:
            key = (vehicle.brand, vehicle.model)
            if key in models:
                continue
            models.add(key)
            cost = costs[vehicle.id]
            reasons = [f"스트레스 비용 반영 후 월 잔여 자금 {cost['stress_remaining_monthly']:,.0f}원",
                       f"월 차량 비용 {cost['monthly_total']:,.0f}원 (보험·세금·유지비 가정 포함)"]
            if profile.preferred_fuel == vehicle.fuel:
                reasons.append('선택한 선호 연료와 일치')
            chosen.append({'vehicle': asdict(vehicle), 'rankingScore': round(score, 6), 'cost': cost,
                           'integratedScore': combined[vehicle.id],
                           'reasons': reasons, 'outsideTrainingRange': out_of_range})
            if len(chosen) == k:
                break
        return {'modelVersion': 'candidate-v2', 'objective': 'financial-eligibility-and-weighted-preferences',
                'scorePolicy': 'weighted-preferences-v1',
                'catalogCount': len(self.vehicles), 'eligibleCount': len(eligible),
                'excludedReasons': dict(excluded), 'recommendations': chosen,
                'assumptions': self.ranker.assumptions.to_dict(),
                'limitations': ['가정 기반 합성 효용을 학습한 실험 점수이며 만족도·구매 확률이 아닙니다.',
                                '가격은 수집 시점의 자동 추출 스냅샷이며 현재 판매·최종 견적 확인이 필요합니다.',
                                '연비 미확인 후보는 명시한 연료별 범위로 비용을 추정합니다.',
                                '크기는 전장 기준의 선호 일치도이며 실내 공간·안전 평가는 아닙니다.',
                                '통합 점수는 사용자 가중치와 기존 ML 점수를 합친 정책 점수이며 확률이 아닙니다.']}
