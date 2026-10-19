import client from '../../shared/api/client.js';

export async function getRecommendationOptions(signal) {
  const response = await client.get('/recommendation-options', { signal });
  return response.data.data.segments;
}

export async function getRecommendations(segment, profile, signal) {
  const response = await client.post('/recommendations', { segment, profile, k: 3 }, { signal });
  return response.data.data;
}
