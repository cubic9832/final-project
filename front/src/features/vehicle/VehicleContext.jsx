import { useEffect, useState } from 'react';
import { useLocation } from 'react-router-dom';
import { applyProfilePreset, findProfilePreset } from '../preset/profilePresets';
import { VehicleContext } from './useVehicle';
import { defaultConditions } from './vehicleData';
import { getVehicles, selectPresetVehicles } from './vehicleApi';

function readSaved() {
  try { const value = JSON.parse(localStorage.getItem('vehicle-favorites') || '[]'); return Array.isArray(value) ? value.filter((id) => typeof id === 'string') : []; } catch { return []; }
}
export function VehicleProvider({ children }) {
  const location = useLocation();
  const [catalog, setCatalog] = useState({ status: 'loading', vehicles: [], error: '' });
  const [attempt, setAttempt] = useState(0);
  useEffect(() => {
    const controller = new AbortController();
    getVehicles(controller.signal).then((vehicles) => {
      if (!controller.signal.aborted) setCatalog({ status: 'ready', vehicles, error: '' });
    }).catch((error) => {
      if (!controller.signal.aborted) setCatalog({ status: 'error', vehicles: [], error: error.response?.data?.detail ?? '차량 목록을 불러오지 못했습니다. 서버 연결을 확인해 주세요.' });
    });
    return () => controller.abort();
  }, [attempt]);
  const { vehicles } = catalog;
  const presetId = location.pathname === '/vehicles/compare' ? new URLSearchParams(location.search).get('preset') : null;
  const [selection, setSelection] = useState({ presetId: null, conditions: defaultConditions, comparison: [] });
  if (selection.presetId !== presetId || (presetId && catalog.status === 'ready' && !selection.presetResolved)) {
    const preset = findProfilePreset(presetId);
    setSelection({ ...selection, ...(preset ? { ...applyProfilePreset(preset), comparison: selectPresetVehicles(preset.vehicleIds, vehicles) } : {}), presetId, presetResolved: catalog.status === 'ready' });
  }
  const { conditions, comparison } = selection;
  function setConditions(next) {
    setSelection((current) => ({ ...current, conditions: typeof next === 'function' ? next(current.conditions) : next }));
  }
  const [favorites, setFavorites] = useState(readSaved);
  const [storageError, setStorageError] = useState('');
  function toggleFavorite(id) {
    const next = favorites.includes(id) ? favorites.filter((item) => item !== id) : [...favorites, id];
    setFavorites(next);
    try { localStorage.setItem('vehicle-favorites', JSON.stringify(next)); setStorageError(''); } catch { setStorageError('브라우저 저장 공간을 사용할 수 없어 이번 방문 중에만 저장됩니다.'); }
  }
  // 회원 탈퇴 때 이 브라우저의 관심차량 목록도 지운다 (개인정보 · 계정 관리 화면의 탈퇴에서 호출)
  function clearFavorites() {
    setFavorites([]);
    try { localStorage.removeItem('vehicle-favorites'); } catch { /* 저장 공간을 못 쓰면 지울 것도 없다 */ }
  }
  function toggleComparison(id) {
    setSelection((current) => ({ ...current, comparison: current.comparison.includes(id) ? current.comparison.filter((item) => item !== id) : current.comparison.length < 3 ? [...current.comparison, id] : current.comparison }));
  }
  return <VehicleContext.Provider value={{ vehicles, catalogStatus: catalog.status, catalogError: catalog.error, retryCatalog: () => { setCatalog({ status: 'loading', vehicles: [], error: '' }); setAttempt((value) => value + 1); }, conditions, setConditions, comparison, toggleComparison, favorites, toggleFavorite, clearFavorites, storageError }}>{children}</VehicleContext.Provider>;
}
