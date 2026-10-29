import { candidateModelImages } from './candidateModelImages.js';
import { newVehicleImages } from './newVehicleImages.js';

const modelAliases = {
  '현대::아반떼 하이브리드': '현대::디 올 뉴 아반떼',
};

export function resolveVehicleImage({ brand, model, name, image_url, image_removed }) {
  if (image_removed) return undefined;
  if (image_url?.startsWith('/api/v1/vehicles/images/')) return { src: image_url, alt: `${model ?? name} 차량 이미지` };
  const key = `${brand}::${model ?? name}`;
  return newVehicleImages[key] ?? candidateModelImages[key] ?? candidateModelImages[modelAliases[key]];
}
