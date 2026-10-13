import avanteImage from '../../assets/vehicles/vehicle-0.jpg';

export default function VehicleArtwork({ vehicle, photo = false }) {
  if (photo && vehicle.id === 'avante') return <img className="vehicle-photo" src={avanteImage} alt="현대 아반떼 하이브리드" />;
  return <div className="vehicle-art" role="img" aria-label={`${vehicle.name} 차량 일러스트`} style={{ '--vehicle-color': vehicle.color }}><div className="vehicle-body"><span className="vehicle-window" /><span className="vehicle-wheel first" /><span className="vehicle-wheel second" /></div></div>;
}
