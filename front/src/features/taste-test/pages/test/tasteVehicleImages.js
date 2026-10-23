// 알려진 대표 모델은 로컬 사진을 우선해 외부 서버 장애와 DB의 NULL 주소에 영향받지 않는다.
const modelImages = [
  ['모닝', '/images/recommendations/cutouts/morning.png'],
  ['레이', '/images/recommendations/cutouts/ray.png'],
  ['아반떼', '/images/recommendations/cutouts/avante.png'],
  ['K5', '/images/recommendations/cutouts/k5.png'],
  ['스포티지', '/images/recommendations/cutouts/sportage.png'],
  ['쏘렌토', '/images/taste-test/sorento.png'],
  ['카니발', '/images/taste-test/carnival.png'],
  ['EV3', '/images/taste-test/ev3.png'],
];

export function getTasteVehicleImages(vehicle) {
  const name = (vehicle.name ?? '').replace(/^(현대|기아)\s*/, '').trim();
  const local = modelImages.find(([model]) => name.toUpperCase() === model.toUpperCase()
    || name.toUpperCase().startsWith(`${model.toUpperCase()} `))?.[1];
  const original = typeof vehicle.image === 'string' ? vehicle.image.trim() : '';
  return [...new Set([local, original].filter(Boolean))];
}
