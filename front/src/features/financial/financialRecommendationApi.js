import client from '../../shared/api/client.js';

export async function getFinancialRecommendations(segment, profile, signal) {
  const response = await client.post('/recommendations', { segment, profile, k: 3 }, { signal });
  return response.data.data;
}
