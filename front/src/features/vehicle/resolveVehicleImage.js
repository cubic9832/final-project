import { candidateModelImages } from './candidateModelImages.js';

const modelAliases = {
  '현대::아반떼 하이브리드': '현대::디 올 뉴 아반떼',
};

export function resolveVehicleImage({ brand, model, name }) {
  const key = `${brand}::${model ?? name}`;
  return candidateModelImages[key] ?? candidateModelImages[modelAliases[key]];
}
