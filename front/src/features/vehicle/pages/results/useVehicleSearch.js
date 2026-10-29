import { useEffect, useState } from 'react';
import { searchVehicleIds } from '../../vehicleApi';

const SEARCH_DELAY_MS = 300;

// 입력이 멈추면 검색하고, 새 입력이 오면 이전 요청을 취소한다. 검색 중에는 직전 결과를 유지한다.
export function useVehicleSearch(keyword) {
  const [search, setSearch] = useState({ keyword: '', ids: null, failed: false });
  const trimmed = keyword.trim();

  useEffect(() => {
    if (!trimmed) return undefined;
    const controller = new AbortController();
    const timer = setTimeout(() => {
      searchVehicleIds(trimmed, controller.signal)
        .then((ids) => setSearch({ keyword: trimmed, ids, failed: false }))
        .catch(() => { if (!controller.signal.aborted) setSearch({ keyword: trimmed, ids: null, failed: true }); });
    }, SEARCH_DELAY_MS);
    return () => { clearTimeout(timer); controller.abort(); };
  }, [trimmed]);

  if (!trimmed) return { ids: null, loading: false, failed: false };
  const settled = search.keyword === trimmed;
  return { ids: search.ids, loading: !settled, failed: settled && search.failed };
}
