import { useState } from 'react';
import { VehicleContext } from './useVehicle';
import { defaultConditions } from './vehicleData';

function readSaved() {
  try { const value = JSON.parse(localStorage.getItem('vehicle-favorites') || '[]'); return Array.isArray(value) ? value.filter((id) => typeof id === 'string') : []; } catch { return []; }
}
export function VehicleProvider({ children }) {
  const [conditions, setConditions] = useState(defaultConditions);
  const [comparison, setComparison] = useState([]);
  const [favorites, setFavorites] = useState(readSaved);
  const [storageError, setStorageError] = useState('');
  function toggleFavorite(id) {
    const next = favorites.includes(id) ? favorites.filter((item) => item !== id) : [...favorites, id];
    setFavorites(next);
    try { localStorage.setItem('vehicle-favorites', JSON.stringify(next)); setStorageError(''); } catch { setStorageError('브라우저 저장 공간을 사용할 수 없어 이번 방문 중에만 저장됩니다.'); }
  }
  function toggleComparison(id) {
    setComparison((current) => current.includes(id) ? current.filter((item) => item !== id) : current.length < 3 ? [...current, id] : current);
  }
  return <VehicleContext.Provider value={{ conditions, setConditions, comparison, toggleComparison, favorites, toggleFavorite, storageError }}>{children}</VehicleContext.Provider>;
}
