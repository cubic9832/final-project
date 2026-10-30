import { initialLifestylePreferences } from './lifestylePreferences.js';

export function createVehiclePreferences(saved = {}) {
  const value = {
    ...initialLifestylePreferences, purpose: '출퇴근', fuel: '상관없음',
    preferredSize: 'any', minimumSeats: '0',
    costImportance: '3', assetRetentionImportance: '3', runningCostImportance: '3', spaceImportance: '3',
    fuelImportance: '3', seatingImportance: '3', purposeImportance: '1',
    ...saved, exteriorSportiness: 'any', preferredBodyType: 'any', bodyImportance: '3',
  };
  for (const name of ['costImportance', 'assetRetentionImportance', 'runningCostImportance', 'spaceImportance', 'fuelImportance',
    'designImportance', 'performanceImportance', 'lifestylePurposeImportance']) {
    const importance = Number(value[name] ?? 3);
    value[name] = String(importance <= 2 ? 1 : importance >= 4 ? 5 : 3);
  }
  return value;
}
