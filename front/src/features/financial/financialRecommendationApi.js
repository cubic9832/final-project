import client from '../../shared/api/client.js';

export async function getFinancialRecommendations(request, signal) {
  const response = await client.post('/recommendations', { ...request, k: 3 }, { signal });
  return response.data.data;
}
