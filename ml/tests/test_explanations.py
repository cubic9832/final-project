import unittest
from dataclasses import replace

from test_preferences import FixedRanker
from test_vehicle_matching import person, vehicle
from vehicle_matching.budget import apply_budget_preference, budget_order, recommendation_budget
from vehicle_matching.explanations import ranking_comparison
from vehicle_matching.finance import assess
from vehicle_matching.preferences import integrated_score
from vehicle_matching.service import CandidateService


class ExplanationTests(unittest.TestCase):
    def test_nine_candidates_preserve_top_three_unique_models_and_financial_limits(self):
        cars = [vehicle(id=f'car-{i}', model=f'Model {i}', price=20000000 + i * 100000,
                        length_mm=4400, seats=5) for i in range(14)]
        cars += [replace(cars[0], id='other-trim'), vehicle(id='unaffordable', model='Too expensive', price=90000000)]
        service = CandidateService(FixedRanker(), cars)
        profile = person(financing_mode='recommendation')
        first = service.recommend(profile, k=3)['recommendations']
        expanded = service.recommend(profile, k=9)['recommendations']
        self.assertEqual(len(expanded), 9)
        self.assertEqual([row['vehicle']['id'] for row in first], [row['vehicle']['id'] for row in expanded[:3]])
        self.assertEqual(len({(row['vehicle']['brand'], row['vehicle']['model']) for row in expanded}), 9)
        self.assertTrue(all(row['cost']['eligible'] for row in expanded))
        self.assertNotIn('unaffordable', [row['vehicle']['id'] for row in expanded])

    def test_full_catalog_match_is_counted_even_when_not_in_top_three(self):
        cars = [vehicle(id=f'small-{i}', model=f'Small {i}', fuel='ELECTRIC', length_mm=3800, seats=4, price=20000000 + i * 1000) for i in range(3)]
        cars.append(vehicle(id='matching', model='Matching', fuel='ELECTRIC', length_mm=4900, seats=5, price=50000000))
        profile = person(preferred_fuel='ELECTRIC', preferred_size='large', minimum_seats=2,
                         cost_importance=5, space_importance=1, liquid_assets=60000000)
        result = CandidateService(FixedRanker(), cars).recommend(profile, k=1)
        self.assertTrue(result['evaluationSummary']['complete'])
        self.assertEqual(result['evaluationSummary']['confirmedMatchingConfigurations'], 1)
        self.assertEqual(result['evaluationSummary']['preferenceEvaluatedConfigurations'], 4)

    def test_unknown_specifications_are_not_counted_as_proven_matches(self):
        cars = [vehicle(fuel='ELECTRIC', length_mm=None, seats=None)]
        result = CandidateService(FixedRanker(), cars).recommend(person(preferred_fuel='ELECTRIC', preferred_size='large', minimum_seats=2))
        summary = result['evaluationSummary']
        self.assertEqual(summary['confirmedMatchingConfigurations'], 0)
        self.assertEqual(summary['unresolvedConfigurations'], 1)
        items = result['recommendations'][0]['decisionEvidence']['preferences']
        self.assertEqual(next(item for item in items if item['key'] == 'space')['status'], 'unknown')
        self.assertEqual(next(item for item in items if item['key'] == 'seating')['status'], 'unknown')

    def test_metadata_does_not_change_original_scores_or_order(self):
        cars = [vehicle(id='small', model='Small', fuel='ELECTRIC', length_mm=3800, seats=4, price=20000000),
                vehicle(id='large', model='Large', fuel='LPG', length_mm=4900, seats=5, price=28000000)]
        p = replace(person(preferred_fuel='ELECTRIC', preferred_size='large', minimum_seats=2),
                    down_payment=0, months=0, annual_rate=0, financing_mode='recommendation')
        ranker = FixedRanker()
        costs = {car.id: assess(p, car, ranker.assumptions) for car in cars}
        band = recommendation_budget(p, cars, costs)
        scores = {car.id: apply_budget_preference(integrated_score(p, car, costs[car.id], .5), car, band) for car in cars}
        expected = sorted(cars, key=lambda car: budget_order(car, scores[car.id]['total'], band))
        result = CandidateService(ranker, cars).recommend(p)
        self.assertEqual([item['vehicle']['id'] for item in result['recommendations']], [car.id for car in expected])
        for item in result['recommendations']:
            self.assertEqual(item['integratedScore'], scores[item['vehicle']['id']])
            self.assertTrue(item['decisionEvidence']['financial']['eligible'])
        comparison = result['recommendations'][0]['rankingComparison']
        self.assertAlmostEqual(sum(item['difference'] for item in comparison['contributionDifferences']), comparison['scoreDifference'])

    def test_ranking_missing_evidence_and_near_ties_are_not_invented(self):
        def item(identity, value):
            return {'vehicle': {'id': identity}, 'integratedScore': {'total': value, 'components': [{'key': 'cost', 'weight': 3, 'contribution': value}]}}
        self.assertEqual(ranking_comparison(item('a', 60), item('b', 59.5))['status'], 'near-tie')
        broken = item('b', 20)
        broken['integratedScore']['components'][0].pop('contribution')
        self.assertEqual(ranking_comparison(item('a', 60), broken)['status'], 'unavailable')

    def test_unaffordable_vehicles_are_excluded_from_financial_match_count(self):
        cars = [vehicle(id='too-expensive', fuel='ELECTRIC', length_mm=4900, seats=5, price=80000000),
                vehicle(id='small', fuel='ELECTRIC', length_mm=3800, seats=4, price=20000000)]
        result = CandidateService(FixedRanker(), cars).recommend(person(preferred_fuel='ELECTRIC', preferred_size='large'))
        self.assertEqual(result['evaluationSummary']['catalogFinanciallyChecked'], 2)
        self.assertEqual(result['evaluationSummary']['financiallyEligibleConfigurations'], 1)
        self.assertEqual(result['evaluationSummary']['confirmedMatchingConfigurations'], 0)


if __name__ == '__main__':
    unittest.main()
