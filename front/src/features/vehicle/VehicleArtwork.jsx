import { useState } from 'react';

export default function VehicleArtwork({ vehicle, photo = false }) {
  const [failedUrl, setFailedUrl] = useState(null);
  if (vehicle.imageUrl && failedUrl !== vehicle.imageUrl) {
    return <img className="vehicle-photo" src={vehicle.imageUrl} alt={`${vehicle.name} 대표 이미지`} loading={photo ? 'eager' : 'lazy'} decoding="async" onError={() => setFailedUrl(vehicle.imageUrl)} />;
  }
  return <div className="vehicle-art" role="img" aria-label={`${vehicle.name} 차량 일러스트`} style={{ '--vehicle-color': vehicle.color }}><div className="vehicle-body"><span className="vehicle-window" /><span className="vehicle-wheel first" /><span className="vehicle-wheel second" /></div></div>;
}
