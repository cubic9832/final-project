import { useEffect, useRef, useState } from 'react';
import { Link } from 'react-router-dom';
import useAuthStore from '../../stores/useAuthStore.js';
import { Car, ChevronLeft, ChevronRight, Copy, Pencil, Plus, RotateCcw, Search } from 'lucide-react';
import theme from '../../styles/theme';
import VehicleEditor from './vehicles/VehicleEditor.jsx';
import { vehicleFuels, vehicleStatuses } from './vehicles/vehicleManagementExamples.js';
import { listAdminVehicles, saveAdminVehicle, adminVehicleError, changeVehicleDeleted } from './vehicles/adminVehicleApi.js';
import './vehicles/VehicleManagement.css';

export default function AdminVehiclesPanel() {
  const [trash, setTrash] = useState(false);
  const [deletion, setDeletion] = useState(null);
  const [actionError, setActionError] = useState('');
  const [busy, setBusy] = useState(false);
  const actionPending = useRef(false);
  const [vehicles, setVehicles] = useState([]);
  const member = useAuthStore(state => state.member);
  const initialized = useAuthStore(state => state.initialized);
  const [loading, setLoading] = useState(true);
  const [loadError, setLoadError] = useState('');
  const [reload, setReload] = useState(0);
  const [saving, setSaving] = useState(false);
  const [saveError, setSaveError] = useState('');
  const [fieldErrors, setFieldErrors] = useState({});
  const pendingSave = useRef(false);
  useEffect(() => {
    if (!['ADMIN', 'SUPER_ADMIN'].includes(member?.role)) return;
    const controller = new AbortController();
    setLoading(true); setLoadError('');
    listAdminVehicles(controller.signal).then(rows => { if (!controller.signal.aborted) setVehicles(rows); })
      .catch(error => { if (!controller.signal.aborted) setLoadError(adminVehicleError(error)); })
      .finally(() => { if (!controller.signal.aborted) setLoading(false); });
    return () => controller.abort();
  }, [member?.role, reload]);
  const [page, setPage] = useState(1);
  const [filters, setFilters] = useState({ keyword: '', brand: '', fuel: '', status: '' });
  const [editor, setEditor] = useState(null);
  const [notice, setNotice] = useState('');
  const addButton = useRef(null);
  const brands = [...new Set(vehicles.map(vehicle => vehicle.brand))].sort();
  const rows = vehicles.filter(vehicle => (trash ? vehicle.status === '삭제됨' : vehicle.status !== '삭제됨')).filter(vehicle => `${vehicle.brand} ${vehicle.model} ${vehicle.trim}`.toLowerCase().includes(filters.keyword.trim().toLowerCase())
    && (!filters.brand || vehicle.brand === filters.brand) && (!filters.fuel || vehicle.fuel === filters.fuel) && (!filters.status || vehicle.status === filters.status));
  const pageCount = Math.max(1, Math.ceil(rows.length / 10));
  const currentPage = Math.min(page, pageCount);
  const visibleRows = rows.slice((currentPage - 1) * 10, currentPage * 10);
  const pageStart = Math.max(1, Math.min(currentPage - 2, pageCount - 4));
  const pages = Array.from({ length: Math.min(5, pageCount) }, (_, index) => pageStart + index);
  const updateFilter = (key, value) => { setFilters(current => ({ ...current, [key]: value })); setPage(1); };
  const resetFilters = () => { setFilters({ keyword: '', brand: '', fuel: '', status: '' }); setPage(1); };
  function openEditor(vehicle = null, duplicate = false) {
    setNotice(''); setSaveError(''); setFieldErrors({});
    setEditor({ vehicle: duplicate ? { ...vehicle, id: '', trim: `${vehicle.trim} 사본`, status: '작성 중' } : vehicle });
  }
  function closeEditor() {
    setEditor(null);
    requestAnimationFrame(() => addButton.current?.focus());
  }
  async function saveVehicle(vehicle) {
    if (pendingSave.current) return;
    pendingSave.current = true; setSaving(true); setSaveError(''); setFieldErrors({});
    try {
      const next = await saveAdminVehicle(vehicle);
      setVehicles(current => [next, ...current.filter(item => item.id !== next.id)]);
      resetFilters(); closeEditor(); setNotice(`${next.model} 정보를 저장했어요.${next.status === '공개' ? ' 다음 추천 요청부터 반영됩니다.' : ' 공개 전까지 추천에 포함되지 않습니다.'}`);
    } catch (error) {
      setSaveError(adminVehicleError(error));
      const names = { priceWon: 'price', bodyType: 'body', lengthMm: 'length', imageUrl: 'image', sourceName: 'source' };
      setFieldErrors(Object.fromEntries((error.response?.data?.errors || []).map(item => [names[item.field] || item.field, item.message])));
    } finally { pendingSave.current = false; setSaving(false); }
  }
  async function updateDeletion(vehicle, deleted) {
    if (actionPending.current) return;
    actionPending.current = true; setBusy(true); setActionError('');
    try {
      const next = await changeVehicleDeleted(vehicle, deleted);
      setVehicles(current => current.map(item => item.id === next.id ? next : item));
      setDeletion(null); setNotice(deleted ? '차량을 휴지통으로 이동했습니다. 추천에서 제외되며 복구할 수 있습니다.' : '작성 중 상태로 복구했습니다. 검수 후 공개해 주세요.');
    } catch (error) { setActionError(adminVehicleError(error)); }
    finally { actionPending.current = false; setBusy(false); }
  }
  if (!initialized) return <p role="status">로그인 정보를 확인하고 있어요.</p>;
  if (!['ADMIN', 'SUPER_ADMIN'].includes(member?.role)) return <section className="admin-card"><h3>관리자 전용 기능입니다.</h3><p>차량 정보를 관리하려면 관리자 권한이 있는 계정으로 로그인해 주세요.</p>{!member && <Link to="/login">로그인</Link>}</section>;
  if (editor) return <VehicleEditor vehicle={editor.vehicle} onCancel={closeEditor} onSave={saveVehicle} saving={saving} saveError={saveError} fieldErrors={fieldErrors} />;
  if (loading) return <p role="status">차량 목록을 불러오고 있어요.</p>;
  if (loadError) return <section className="admin-card"><p role="alert">{loadError}</p><button type="button" className="admin-outline-button" onClick={() => setReload(value => value + 1)}>다시 불러오기</button></section>;
  return <div className="admin-panel-stack vehicle-management">
    <div className="vehicle-management-row-actions"><button type="button" className="admin-outline-button" aria-pressed={!trash} onClick={() => { setTrash(false); setPage(1); setDeletion(null); }}>차량 목록</button><button type="button" className="admin-outline-button" aria-pressed={trash} onClick={() => { setTrash(true); resetFilters(); setDeletion(null); }}>휴지통 ({vehicles.filter(v => v.status === '삭제됨').length})</button></div>
    {actionError && <p role="alert">{actionError}</p>}
    {deletion && <section className="admin-card" aria-label="차량 삭제 확인"><h3>{deletion.model} {deletion.trim} 차량을 삭제할까요?</h3><p>휴지통으로 이동하며 추천에서 제외됩니다. 나중에 작성 중 상태로 복구할 수 있습니다.</p><button type="button" className="admin-outline-button" disabled={busy} onClick={() => setDeletion(null)}>취소</button><button type="button" className="admin-primary-button" disabled={busy} onClick={() => updateDeletion(deletion, true)}>{busy ? '처리 중' : '휴지통으로 이동'}</button></section>}

    <div className="vehicle-management-toolbar"><div><span className="admin-eyebrow">VEHICLE CATALOG</span><h3>차량 데이터를 한곳에서</h3><p>모델과 트림별 정보를 확인하고 관리하세요.</p></div><button ref={addButton} type="button" className="vehicle-management-cta" onClick={() => openEditor()}><Plus size={theme.iconSize.sm} aria-hidden="true" />차량 등록</button></div>
    <div className="admin-summary" aria-label="전체 차량 카탈로그 현황">{[
      ['등록 차량', vehicles.length, '트림·사양 기준'], ['차량 모델', new Set(vehicles.map(v => `${v.brand}::${v.model}`)).size, '브랜드·모델 기준'],
      ['국산 차량', vehicles.filter(v => v.origin === '국산').length, '트림·사양 기준'], ['수입 차량', vehicles.filter(v => v.origin === '수입').length, '트림·사양 기준'],
    ].map(([label, value, note]) => <div className="admin-stat" key={label}><span>{label}</span><strong>{value}<small> 건</small></strong><small>{note}</small></div>)}</div>
    <section className="admin-card"><div className="admin-card-heading"><div><h3>차량 목록</h3><p>같은 모델도 연료와 트림이 다르면 각각 관리합니다. 공개 상태인 차량만 추천에 반영됩니다.</p></div><button type="button" className="admin-outline-button" onClick={() => setReload(value => value + 1)}>목록 새로고침</button></div>
      <div className="vehicle-management-filters"><label className="admin-search-field"><Search size={theme.iconSize.sm} aria-hidden="true" /><input type="search" aria-label="브랜드, 모델 또는 트림 검색" placeholder="브랜드, 모델, 트림 검색" value={filters.keyword} onChange={event => updateFilter('keyword', event.target.value)} /></label>
        {[
          ['brand', '브랜드', brands], ['fuel', '연료', vehicleFuels], ['status', '관리 상태', vehicleStatuses],
        ].map(([key, label, options]) => <label key={key} className="vehicle-management-filter"><span>{label}</span><select value={filters[key]} onChange={event => updateFilter(key, event.target.value)}><option value="">전체</option>{options.map(option => <option key={option}>{option}</option>)}</select></label>)}
        <button type="button" className="admin-icon-button" aria-label="검색 조건 초기화" title="검색 조건 초기화" onClick={resetFilters}><RotateCcw size={theme.iconSize.sm} aria-hidden="true" /></button>
      </div>
      <div className="admin-table-wrap"><table className="admin-table vehicle-management-table"><caption className="admin-sr-only">전체 차량 카탈로그 목록</caption><thead><tr><th scope="col">차량·트림</th><th scope="col">연료</th><th scope="col">판매 가격</th><th scope="col">관리 상태</th><th scope="col">작업</th></tr></thead><tbody>{visibleRows.map(vehicle => <tr key={vehicle.id}>
        <td><div className="vehicle-management-identity">{vehicle.image ? <img src={vehicle.image} alt="" loading="lazy" /> : <Car size={theme.iconSize.lg} aria-hidden="true" />}<div><small>{vehicle.brand} · {vehicle.year ? `${vehicle.year}년형` : '연식 미입력'}</small><strong>{vehicle.model}</strong><span>{vehicle.trim}</span></div></div></td>
        <td>{vehicle.fuel}</td><td className="vehicle-management-price">{Number(vehicle.price).toLocaleString('ko-KR')}만 원</td><td><span className={`admin-status ${vehicle.status === '공개' ? 'is-ok' : vehicle.status === '검수 대기' ? 'is-check' : 'is-neutral'}`}>{vehicle.status}</span><small>{vehicle.updatedAt}</small></td>
        <td><div className="vehicle-management-row-actions">{vehicle.status !== '삭제됨' && <><button className="admin-text-button" type="button" onClick={() => openEditor(vehicle)} aria-label={`${vehicle.model} ${vehicle.trim} 수정`}><Pencil size={theme.iconSize.sm} aria-hidden="true" />수정</button><button className="admin-icon-button" type="button" onClick={() => openEditor(vehicle, true)} aria-label={`${vehicle.model} ${vehicle.trim} 복제해서 등록`} title="복제해서 등록"><Copy size={theme.iconSize.sm} aria-hidden="true" /></button><button type="button" className="admin-text-button" disabled={busy} onClick={() => { setDeletion(vehicle); setActionError(''); }}>삭제</button></>}{vehicle.status === '삭제됨' && <button type="button" className="admin-text-button" disabled={busy} onClick={() => updateDeletion(vehicle, false)}>복구</button>}</div></td>
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
