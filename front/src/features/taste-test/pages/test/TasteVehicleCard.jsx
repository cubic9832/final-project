import { useState } from 'react';
import { CarFront } from 'lucide-react';
import theme from '../../../../styles/theme';
import { getTasteVehicleImages } from './tasteVehicleImages';

function VehicleImage({ name, sources }) {
  const [sourceIndex, setSourceIndex] = useState(0);
  const source = sources[sourceIndex];

  if (!source) return <div className="taste-vehicle-image-error" role="img" aria-label={`${name} 사진 대신 표시한 기본 차량 이미지`}>
    <CarFront size={theme.iconSize.lg} aria-hidden="true" />
    <p>차량 대표 이미지</p>
    {sources.length > 0 && <button type="button" className="taste-button taste-button-outline" onClick={() => setSourceIndex(0)}>사진 다시 불러오기</button>}
  </div>;

  return <img key={source} src={source} alt={`${name} 대표 외관 이미지`} loading="lazy"
    onError={() => setSourceIndex((index) => index + 1)} />;
}

export default function TasteVehicleCard({ vehicle }) {
  const sources = getTasteVehicleImages(vehicle);
  return (
    <li className="taste-vehicle-card">
      <div className="taste-vehicle-image">
        <VehicleImage key={`${vehicle.name}:${sources.join('|')}`} name={vehicle.name} sources={sources} />
      </div>
      <div className="taste-vehicle-info"><p className="taste-caption">{vehicle.category}</p><h3>{vehicle.name}</h3></div>
    </li>
  );
}
