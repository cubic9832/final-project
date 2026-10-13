import { useState } from 'react';
import { useLocation } from 'react-router-dom';
import { applyProfilePreset, findProfilePreset } from '../preset/profilePresets';
import { VehicleContext } from './useVehicle';
import { defaultConditions } from './vehicleData';

function readSaved() {
  try { const value = JSON.parse(localStorage.getItem('vehicle-favorites') || '[]'); return Array.isArray(value) ? value.filter((id) => typeof id === 'string') : []; } catch { return []; }
}
export function VehicleProvider({ children }) {
  const location = useLocation();
  const presetId = location.pathname === '/vehicles/compare' ? new URLSearchParams(location.search).get('preset') : null;
  const [selection, setSelection] = useState({ presetId: null, conditions: defaultConditions, comparison: [] });
  if (selection.presetId !== presetId) {
    const preset = findProfilePreset(presetId);
    setSelection({ ...selection, ...(preset ? applyProfilePreset(preset) : {}), presetId });
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
  function toggleComparison(id) {
    setSelection((current) => ({ ...current, comparison: current.comparison.includes(id) ? current.comparison.filter((item) => item !== id) : current.comparison.length < 3 ? [...current.comparison, id] : current.comparison }));
  }
  return <VehicleContext.Provider value={{ conditions, setConditions, comparison, toggleComparison, favorites, toggleFavorite, storageError }}>{children}</VehicleContext.Provider>;
}
