import unittest
from pathlib import Path

try:
    from fastapi.testclient import TestClient
except (ImportError, RuntimeError):
    raise unittest.SkipTest('API 테스트에는 pip install -e ".[serve,test]"가 필요합니다.')

from legacy.recommender.api import create_app
from legacy.recommender.models.mlp import MlpConfig, MlpRanker
from legacy.recommender.preprocessing import Preprocessor
from legacy.recommender.service import ModelBundle, ModelRegistry
from legacy.tests.support import make_sample, profile_from_sample


class RecommendationApiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        samples = [make_sample(), make_sample(label='OWN002', model_name='K8')]
        preprocessor = Preprocessor()
        preprocessor.fit(samples)
        prepared = preprocessor.transform(samples)
        ranker = MlpRanker(MlpConfig(hidden=(8, 4), epochs=2, batch_size=2, dropout=0))
        ranker.fit(prepared, prepared)
        cls.registry = ModelRegistry({'all-cars': ModelBundle(Path('fixture-run'), preprocessor, ranker)})
        cls.profile = profile_from_sample(samples[0])

    def setUp(self):
        self.client = self.enterContext(TestClient(create_app(self.registry)))

    def test_options_and_prediction_use_the_loaded_model(self):
        options = self.client.get('/api/v1/recommendation-options').json()['data']['segments']
        self.assertTrue(options[0]['available'])
        response = self.client.post('/api/v1/recommendations', json={'segment': 'all-cars', 'profile': self.profile})
        self.assertEqual(response.status_code, 200)
        data = response.json()['data']
        self.assertEqual(data['modelVersion'], 'fixture-run')
        self.assertEqual({row['labelCode'] for row in data['recommendations']}, {'OWN001', 'OWN002'})
        self.assertAlmostEqual(sum(row['probability'] for row in data['recommendations']), 1, places=5)
        self.assertGreaterEqual(data['recommendations'][0]['probability'], data['recommendations'][1]['probability'])

    def test_invalid_and_unknown_profile_fields_produce_field_errors(self):
        for field, value in [('개인_평균월실수령소득_원', -1), ('차량_이용목적', '학습에 없는 목적')]:
            profile = {**self.profile, field: value}
            response = self.client.post('/api/v1/recommendations', json={'segment': 'all-cars', 'profile': profile})
            self.assertEqual(response.status_code, 400)
            self.assertTrue(response.headers['content-type'].startswith('application/problem+json'))
            self.assertEqual(response.json()['errors'][0]['field'], field)

    def test_unavailable_model_and_invalid_body_are_not_success_responses(self):
        with TestClient(create_app(ModelRegistry({}))) as empty_client:
            response = empty_client.post('/api/v1/recommendations', json={'segment': 'all-cars', 'profile': self.profile})
        self.assertEqual(response.status_code, 503)
        response = self.client.post('/api/v1/recommendations', json={'segment': 'other', 'profile': self.profile})
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()['status'], 400)

    def test_model_is_not_reloaded_for_each_request(self):
        from unittest.mock import patch
        with patch('legacy.recommender.service.load_bundle', side_effect=AssertionError('요청마다 모델을 읽으면 안 됩니다.')):
            for _ in range(2):
                response = self.client.post('/api/v1/recommendations', json={'segment': 'all-cars', 'profile': self.profile})
                self.assertEqual(response.status_code, 200)
