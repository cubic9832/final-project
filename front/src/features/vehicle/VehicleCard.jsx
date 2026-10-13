import { Link } from 'react-router-dom';
import { ArrowRight } from 'lucide-react';
import theme from '../../styles/theme';
import VehicleArtwork from './VehicleArtwork';
import { calculateCosts, formatAmount } from './vehicleData';
import { useVehicle } from './useVehicle';

export default function VehicleCard({ vehicle }) {
  const { conditions, comparison, toggleComparison } = useVehicle();
  const selected = comparison.includes(vehicle.id);
  return <article className="vehicle-card panel">
    <Link to={`/vehicles/${vehicle.id}`}><VehicleArtwork vehicle={vehicle} /><span className="vehicle-badge">추천 적합 {calculateCosts(vehicle, conditions).score}%</span><h3>{vehicle.name}</h3><p className="muted">{vehicle.type} · {vehicle.condition}</p><div className="vehicle-metrics"><div><small>예상 차량가</small><strong>{formatAmount(vehicle.price)}</strong></div><div><small>복합연비</small><strong>{vehicle.efficiency}km/L</strong></div></div><span className="vehicle-detail-link">차량 상세 보기 <ArrowRight size={theme.iconSize.sm} aria-hidden="true" /></span></Link>
    <label className="compare-check"><input type="checkbox" checked={selected} disabled={!selected && comparison.length >= 3} onChange={() => toggleComparison(vehicle.id)} />비교에 추가</label>
  </article>;
}
