import { Link } from 'react-router-dom';
import { useVehicle } from './useVehicle';
import './VehiclePages.css';

export default function VehicleCatalogGate({ children }) {
  const { vehicles, catalogStatus, catalogError, retryCatalog } = useVehicle();
  if (catalogStatus === 'loading') return <section className="vehicle-page panel" role="status">차량 정보를 불러오는 중입니다.</section>;
  if (catalogStatus === 'error') return <section className="vehicle-page panel"><p role="alert">{catalogError}</p><button className="vehicle-button" onClick={retryCatalog}>다시 시도</button></section>;
  if (!vehicles.length) return <section className="vehicle-page panel"><h1>조회 가능한 차량이 없습니다.</h1><p>차량 데이터가 등록되면 여기에서 확인할 수 있습니다.</p><Link to="/">홈으로</Link></section>;
  return children;
}
