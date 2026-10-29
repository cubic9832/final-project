import { useState } from 'react';
import { Car } from 'lucide-react';
import { resolveVehicleImage } from '../../vehicle/resolveVehicleImage';
import theme from '../../../styles/theme';
import './DreamCarPreview.css';

const fuels = { GASOLINE: '가솔린', HYBRID: '하이브리드', ELECTRIC: '전기', DIESEL: '디젤', LPG: 'LPG' };

export default function DreamCarPreview({ vehicle }) {
  const [failedImage, setFailedImage] = useState('');
  const image = resolveVehicleImage(vehicle)?.src;
  return <div className="dream-car-preview">
    <div className="dream-car-preview-art">{image && failedImage !== image ? <img src={image} alt={`${vehicle.brand} ${vehicle.model} 목표 차량`} onError={() => setFailedImage(image)} /> : <Car size={theme.iconSize.lg} aria-label="차량 이미지 없음" />}</div>
    <div className="dream-car-preview-info"><small>{vehicle.brand}{vehicle.year ? ` · ${vehicle.year}년형` : ''}</small>
    <h3>{vehicle.model}</h3>
    <p>{vehicle.trim} · {fuels[vehicle.fuel] || vehicle.fuel}</p>
    <strong>{Math.round(vehicle.price / 10000).toLocaleString('ko-KR')}만 원</strong></div>
  </div>;
}
