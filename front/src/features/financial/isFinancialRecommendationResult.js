const supportedVersions = ['candidate-v2', 'scenario-v1'];

export function isFinancialRecommendationResult(result) {
  return supportedVersions.includes(result?.modelVersion) && Array.isArray(result?.recommendations);
}
