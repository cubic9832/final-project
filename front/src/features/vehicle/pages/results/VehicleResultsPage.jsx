import { useState } from 'react';
import { Link } from 'react-router-dom';
import VehicleCard from '../../components/VehicleCard';
import { useVehicle } from '../../useVehicle';
import { calculateCosts } from '../../vehicleData';
import '../../styles/VehiclePages.css';

export function VehicleResultsPage() {
  const { vehicles, conditions, comparison } = useVehicle();
  const [onlyFavorites, setOnlyFavorites] = useState(false);
  const { favorites } = useVehicle();
  const results = vehicles.filter((vehicle) => (conditions.condition === '상관없음' || vehicle.condition === conditions.condition) && (!onlyFavorites || favorites.includes(vehicle.id))).sort((a, b) => calculateCosts(b, conditions).score - calculateCosts(a, conditions).score);
  return <div className="vehicle-page"><div className="vehicle-heading split"><div><h1>추천 차량</h1><p>재무상태와 차량 이용 목적을 바탕으로 고른 추천 차량입니다.</p></div><span className="vehicle-badge">총 {results.length}대 추천</span></div><div className="vehicle-toolbar"><Link className="vehicle-button" to="/search">검색 조건 변경</Link><label><input type="checkbox" checked={onlyFavorites} onChange={(event) => setOnlyFavorites(event.target.checked)} /> 관심차량만 보기</label><Link className="vehicle-button primary" to="/vehicles/compare">차량 비교 ({comparison.length}/3)</Link></div>{results.length ? <div className="vehicle-grid">{results.map((vehicle) => <VehicleCard key={vehicle.id} vehicle={vehicle} />)}</div> : <div className="panel vehicle-empty"><h2>조건에 맞는 차량이 없습니다.</h2><p>검색 조건이나 관심차량 필터를 변경해 주세요.</p><button className="vehicle-button" onClick={() => setOnlyFavorites(false)}>전체 차량 보기</button></div>}<div className="vehicle-note warning"><strong>안내</strong><p>차량 가격과 연비, 적합도는 화면 구성 검토를 위한 예시이며 실제 구매 전 확인이 필요합니다.</p></div></div>;
}
