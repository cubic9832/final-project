import { useState } from 'react';
import { Link } from 'react-router-dom';
import { Search } from 'lucide-react';
import VehicleCard from '../../components/VehicleCard';
import { useVehicle } from '../../useVehicle';
import { calculateCosts } from '../../vehicleData';
import theme from '../../../../styles/theme';
import { useVehicleSearch } from './useVehicleSearch';
import '../../styles/VehiclePages.css';

export function VehicleResultsPage() {
  const { vehicles, conditions, comparison } = useVehicle();
  const [onlyFavorites, setOnlyFavorites] = useState(false);
  const [keyword, setKeyword] = useState('');
  const { favorites } = useVehicle();
  const search = useVehicleSearch(keyword);
  const matched = vehicles.filter((vehicle) => (conditions.condition === '상관없음' || vehicle.condition === conditions.condition) && (!onlyFavorites || favorites.includes(vehicle.id)));
  // 검색은 조건 결과 안에서 거르기만 하고, 순서는 추천 적합도 순을 유지한다
  const searchIds = search.ids && new Set(search.ids);
  const results = matched.filter((vehicle) => !searchIds || searchIds.has(vehicle.id)).sort((a, b) => calculateCosts(b, conditions).score - calculateCosts(a, conditions).score);
  const searchStatus = search.failed ? '검색 서버에 연결할 수 없어 전체 추천 차량을 보여 드립니다.' : search.loading ? '검색 중입니다.' : '';
  function resetFilters() { setOnlyFavorites(false); setKeyword(''); }
  return <div className="vehicle-page"><div className="vehicle-heading split"><div><h1>추천 차량</h1><p>재무상태와 차량 이용 목적을 바탕으로 고른 추천 차량입니다.</p></div><span className="vehicle-badge">총 {results.length}대 추천</span></div><div className="vehicle-toolbar"><label className="vehicle-keyword"><Search size={theme.iconSize.md} aria-hidden="true" /><span className="sr-only">차량 검색</span><input type="search" value={keyword} onChange={(event) => setKeyword(event.target.value)} placeholder="차명·브랜드·차종 검색" aria-describedby="vehicle-search-status" maxLength={50} /></label><Link className="vehicle-button" to="/search">검색 조건 변경</Link><label><input type="checkbox" checked={onlyFavorites} onChange={(event) => setOnlyFavorites(event.target.checked)} /> 관심차량만 보기</label><Link className="vehicle-button primary" to="/vehicles/compare">차량 비교 ({comparison.length}/3)</Link></div><p id="vehicle-search-status" className={search.failed ? 'vehicle-search-status vehicle-error' : 'vehicle-search-status'} role="status">{searchStatus}</p>{results.length ? <div className="vehicle-grid">{results.map((vehicle) => <VehicleCard key={vehicle.id} vehicle={vehicle} />)}</div> : <div className="panel vehicle-empty"><h2>조건에 맞는 차량이 없습니다.</h2><p>검색어, 검색 조건이나 관심차량 필터를 변경해 주세요.</p><button className="vehicle-button" onClick={resetFilters}>전체 차량 보기</button></div>}<div className="vehicle-note warning"><strong>안내</strong><p>차량 가격과 연비, 적합도는 화면 구성 검토를 위한 예시이며 실제 구매 전 확인이 필요합니다.</p></div></div>;
}
