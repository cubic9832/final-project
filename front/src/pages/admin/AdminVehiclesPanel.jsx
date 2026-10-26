import { useRef, useState } from 'react';
import { Car, ChevronLeft, ChevronRight, Copy, Pencil, Plus, RotateCcw, Search } from 'lucide-react';
import theme from '../../styles/theme';
import VehicleEditor from './vehicles/VehicleEditor.jsx';
import { vehicleFuels, vehicleStatuses } from './vehicles/vehicleManagementExamples.js';
import { catalogVehicles } from './vehicles/vehicleManagementCatalog.js';
import './vehicles/VehicleManagement.css';

export default function AdminVehiclesPanel() {
  const [vehicles, setVehicles] = useState(catalogVehicles);
  const [page, setPage] = useState(1);
  const [filters, setFilters] = useState({ keyword: '', brand: '', fuel: '', status: '' });
  const [editor, setEditor] = useState(null);
  const [notice, setNotice] = useState('');
  const addButton = useRef(null);
  const brands = [...new Set(vehicles.map(vehicle => vehicle.brand))].sort();
  const rows = vehicles.filter(vehicle => `${vehicle.brand} ${vehicle.model} ${vehicle.trim}`.toLowerCase().includes(filters.keyword.trim().toLowerCase())
    && (!filters.brand || vehicle.brand === filters.brand) && (!filters.fuel || vehicle.fuel === filters.fuel) && (!filters.status || vehicle.status === filters.status));
  const pageCount = Math.max(1, Math.ceil(rows.length / 10));
  const currentPage = Math.min(page, pageCount);
  const visibleRows = rows.slice((currentPage - 1) * 10, currentPage * 10);
  const pageStart = Math.max(1, Math.min(currentPage - 2, pageCount - 4));
  const pages = Array.from({ length: Math.min(5, pageCount) }, (_, index) => pageStart + index);
  const updateFilter = (key, value) => { setFilters(current => ({ ...current, [key]: value })); setPage(1); };
  const resetFilters = () => { setFilters({ keyword: '', brand: '', fuel: '', status: '' }); setPage(1); };
  function openEditor(vehicle = null, duplicate = false) {
    setNotice('');
    setEditor({ vehicle: duplicate ? { ...vehicle, id: '', trim: `${vehicle.trim} 사본`, status: '작성 중' } : vehicle });
  }
  function closeEditor() {
    setEditor(null);
    requestAnimationFrame(() => addButton.current?.focus());
  }
  function savePreview(vehicle) {
    const next = { ...vehicle, id: vehicle.id || `preview-${crypto.randomUUID()}`, updatedAt: '방금 수정' };
    setVehicles(current => current.some(item => item.id === next.id) ? current.map(item => item.id === next.id ? next : item) : [next, ...current]);
    resetFilters(); closeEditor();
    setNotice(`${next.model} 정보를 이 화면에 임시 저장했어요. 새로고침하면 원래 카탈로그로 돌아갑니다.`);
  }
  if (editor) return <VehicleEditor vehicle={editor.vehicle} onCancel={closeEditor} onSave={savePreview} />;
  return <div className="admin-panel-stack vehicle-management">
    <div className="vehicle-management-toolbar"><div><span className="admin-eyebrow">VEHICLE CATALOG</span><h3>차량 데이터를 한곳에서</h3><p>모델과 트림별 정보를 확인하고 관리하세요.</p></div><button ref={addButton} type="button" className="vehicle-management-cta" onClick={() => openEditor()}><Plus size={theme.iconSize.sm} aria-hidden="true" />차량 등록</button></div>
    <div className="admin-summary" aria-label="전체 차량 카탈로그 현황">{[
      ['등록 차량', vehicles.length, '트림·사양 기준'], ['차량 모델', new Set(vehicles.map(v => `${v.brand}::${v.model}`)).size, '브랜드·모델 기준'],
      ['국산 차량', vehicles.filter(v => v.origin === '국산').length, '트림·사양 기준'], ['수입 차량', vehicles.filter(v => v.origin === '수입').length, '트림·사양 기준'],
    ].map(([label, value, note]) => <div className="admin-stat" key={label}><span>{label}</span><strong>{value}<small> 건</small></strong><small>{note}</small></div>)}</div>
    <section className="admin-card"><div className="admin-card-heading"><div><h3>차량 목록</h3><p>현재 추천 카탈로그 전체입니다. 같은 모델도 연료와 트림이 다르면 각각 관리합니다.</p></div><span className="admin-count-badge">카탈로그 미리보기</span></div>
      <div className="vehicle-management-filters"><label className="admin-search-field"><Search size={theme.iconSize.sm} aria-hidden="true" /><input type="search" aria-label="브랜드, 모델 또는 트림 검색" placeholder="브랜드, 모델, 트림 검색" value={filters.keyword} onChange={event => updateFilter('keyword', event.target.value)} /></label>
        {[
          ['brand', '브랜드', brands], ['fuel', '연료', vehicleFuels], ['status', '관리 상태', vehicleStatuses],
        ].map(([key, label, options]) => <label key={key} className="vehicle-management-filter"><span>{label}</span><select value={filters[key]} onChange={event => updateFilter(key, event.target.value)}><option value="">전체</option>{options.map(option => <option key={option}>{option}</option>)}</select></label>)}
        <button type="button" className="admin-icon-button" aria-label="검색 조건 초기화" title="검색 조건 초기화" onClick={resetFilters}><RotateCcw size={theme.iconSize.sm} aria-hidden="true" /></button>
      </div>
      <div className="admin-table-wrap"><table className="admin-table vehicle-management-table"><caption className="admin-sr-only">전체 차량 카탈로그 목록</caption><thead><tr><th scope="col">차량·트림</th><th scope="col">연료</th><th scope="col">판매 가격</th><th scope="col">관리 상태</th><th scope="col">작업</th></tr></thead><tbody>{visibleRows.map(vehicle => <tr key={vehicle.id}>
        <td><div className="vehicle-management-identity"><img src={vehicle.image} alt="" loading="lazy" /><div><small>{vehicle.brand} · {vehicle.year ? `${vehicle.year}년형` : '연식 미입력'}</small><strong>{vehicle.model}</strong><span>{vehicle.trim}</span></div></div></td>
        <td>{vehicle.fuel}</td><td className="vehicle-management-price">{Number(vehicle.price).toLocaleString('ko-KR')}만 원</td><td><span className={`admin-status ${vehicle.status === '공개' ? 'is-ok' : vehicle.status === '검수 대기' ? 'is-check' : 'is-neutral'}`}>{vehicle.status}</span><small>{vehicle.updatedAt}</small></td>
        <td><div className="vehicle-management-row-actions"><button className="admin-text-button" type="button" onClick={() => openEditor(vehicle)} aria-label={`${vehicle.model} ${vehicle.trim} 수정`}><Pencil size={theme.iconSize.sm} aria-hidden="true" />수정</button><button className="admin-icon-button" type="button" onClick={() => openEditor(vehicle, true)} aria-label={`${vehicle.model} ${vehicle.trim} 복제해서 등록`} title="복제해서 등록"><Copy size={theme.iconSize.sm} aria-hidden="true" /></button></div></td>
      </tr>)}</tbody></table></div>
      {!rows.length && <div className="admin-empty"><Car size={theme.iconSize.lg} aria-hidden="true" /><strong>조건에 맞는 차량이 없어요.</strong><p>검색어나 필터를 변경해 주세요.</p><button type="button" className="admin-outline-button" onClick={resetFilters}>검색 조건 초기화</button></div>}
      <div className="vehicle-management-list-footer"><p aria-live="polite">전체 {vehicles.length}건 · 검색 결과 <strong>{rows.length}건</strong>{rows.length > 0 && ` · ${(currentPage - 1) * 10 + 1}–${Math.min(currentPage * 10, rows.length)}건 표시`}</p>
        {rows.length > 10 && <nav className="vehicle-management-pagination" aria-label="차량 목록 페이지">
          <button type="button" onClick={() => setPage(1)} disabled={currentPage === 1} aria-label="첫 페이지">처음</button>
          <button type="button" onClick={() => setPage(currentPage - 1)} disabled={currentPage === 1} aria-label="이전 페이지"><ChevronLeft size={theme.iconSize.sm} aria-hidden="true" /></button>
          {pages.map(number => <button key={number} type="button" aria-label={`${number}페이지`} aria-current={number === currentPage ? 'page' : undefined} onClick={() => setPage(number)}>{number}</button>)}
          <button type="button" onClick={() => setPage(currentPage + 1)} disabled={currentPage === pageCount} aria-label="다음 페이지"><ChevronRight size={theme.iconSize.sm} aria-hidden="true" /></button>
          <button type="button" onClick={() => setPage(pageCount)} disabled={currentPage === pageCount} aria-label="마지막 페이지">끝</button>
          <span>{currentPage} / {pageCount}</span>
        </nav>}
      </div>
    </section>{notice && <p className="vehicle-management-notice" role="status">{notice}</p>}
  </div>;
}
