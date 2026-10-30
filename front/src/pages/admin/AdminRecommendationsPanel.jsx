import { useEffect, useMemo, useState } from 'react';
import { ExternalLink, Image, Search } from 'lucide-react';
import theme from '../../styles/theme';
import { getRecommendationCandidates } from '../../features/admin/adminApi';
import { candidateModelImages } from '../../features/vehicle/candidateModelImages';

// 7단계 추천 관리 — 추천 서버가 실제로 쓰는 후보 차량 목록 검수 (10-27: 고정 예시 4대 → 실제 후보 전체)
// 목록 = 학습 결과 폴더의 catalog.json 을 서버가 읽은 것 (GET /admin/recommendation-candidates, 읽기만)
// 고칠 곳이 보이면 조원(ML) 데이터 파일에서 고친다 — 이 화면은 출처 · 확인일 · 승차 정원 상태를 검수하는 용도
const FUEL_LABELS = { GASOLINE: '가솔린', HYBRID: '하이브리드', DIESEL: '디젤', LPG: 'LPG', ELECTRIC: '전기' };
const PAGE_SIZE = 10;
const manwon = (won) => (won == null ? '-' : `${Math.round(won / 10000).toLocaleString('ko-KR')}만 원`);
const imageOf = (car) => candidateModelImages[`${car.brand}::${car.model}`] ?? null;
// catalog.json 의 상태 코드 → 화면 설명
const SEAT_STATUS = {
  'user-provided': '제조사 확인 전 (제공 목록 기준)',
  'official-reference-conflict': '제조사 자료와 다름',
  'official-reference': '제조사 자료 기준',
  'official-source-verified': '제조사 출처 확인',
  'official-body-reference': '제조사 차체 자료 기준',
};
const QUALITY = {
  'automatically-extracted-snapshot': '가격표에서 자동 추출',
  'legacy-price-snapshot': '예전 가격 자료',
  'official-source-checked-supplement': '제조사 출처 확인 후 보충',
};
// 승차 정원이 제조사 자료로 확인되지 않았거나 자료와 다른 후보
const needsSeatCheck = (car) => !car.seatsStatus?.startsWith('official-') || car.seatsStatus === 'official-reference-conflict';

export default function AdminRecommendationsPanel() {
  const [candidates, setCandidates] = useState(); // undefined 불러오는 중 · null 실패
  const [query, setQuery] = useState({ keyword: '', fuel: '', check: '', page: 1 });
  const [selectedId, setSelectedId] = useState(null);

  useEffect(() => {
    const controller = new AbortController();
    getRecommendationCandidates(controller.signal)
      .then(setCandidates)
      .catch(() => !controller.signal.aborted && setCandidates(null));
    return () => controller.abort();
  }, []);

  // 검색 · 연료 · 검수 필요 거르기 (전체가 300건 안쪽이라 화면에서 거른다)
  const filtered = useMemo(() => (candidates ?? []).filter((car) => {
    const text = `${car.brand} ${car.model} ${car.trim}`.toLowerCase();
    return (!query.keyword || text.includes(query.keyword.trim().toLowerCase()))
      && (!query.fuel || car.fuel === query.fuel)
      && (!query.check || (query.check === 'seats' ? needsSeatCheck(car) : !imageOf(car)));
  }), [candidates, query]);

  if (candidates === undefined) return <p className="admin-empty" role="status">추천 후보 차량을 불러오는 중…</p>;
  if (candidates === null) return <p className="admin-empty" role="alert">추천 후보 차량을 불러오지 못했습니다.</p>;

  const totalPages = Math.max(1, Math.ceil(filtered.length / PAGE_SIZE));
  const page = Math.min(query.page, totalPages);
  const rows = filtered.slice((page - 1) * PAGE_SIZE, page * PAGE_SIZE);
  const selected = candidates.find((car) => car.id === selectedId) ?? rows[0] ?? null;
  const modelCount = new Set(candidates.map((car) => `${car.brand}::${car.model}`)).size;
  const noImage = new Set(candidates.filter((car) => !imageOf(car)).map((car) => `${car.brand}::${car.model}`)).size;
  const seatCheck = candidates.filter(needsSeatCheck).length;
  const change = (next) => setQuery((prev) => ({ ...prev, ...next, page: next.page ?? 1 }));
  const image = selected && imageOf(selected);

  return <div className="admin-panel-stack">
    <section className="admin-card"><div className="admin-card-heading"><div><h3>추천 후보 차량 검수</h3><p>추천 서버가 실제로 고르는 후보 차량입니다. 가격 출처 · 확인일 · 승차 정원 상태를 검수하세요.</p></div>
      <span className="admin-count-badge">전체 {candidates.length}건 · 차종 {modelCount}개 · 이미지 없는 차종 {noImage}개 · 승차 정원 확인 필요 {seatCheck}건</span></div>
      <div className="admin-filters">
        <label className="admin-search-field"><Search size={theme.iconSize.sm} aria-hidden="true" /><input type="search" placeholder="브랜드 · 모델 · 트림" value={query.keyword} onChange={(event) => change({ keyword: event.target.value })} aria-label="후보 차량 검색" /></label>
        <label className="admin-filter-field">연료<select value={query.fuel} onChange={(event) => change({ fuel: event.target.value })}><option value="">전체</option>{Object.entries(FUEL_LABELS).map(([value, label]) => <option key={value} value={value}>{label}</option>)}</select></label>
        <label className="admin-filter-field">검수<select value={query.check} onChange={(event) => change({ check: event.target.value })}><option value="">전체</option><option value="seats">승차 정원 확인 필요</option><option value="image">이미지 없음</option></select></label>
      </div>
      {rows.length === 0 ? <p className="admin-empty" role="status">조건에 맞는 후보 차량이 없습니다.</p> : <div className="admin-table-wrap"><table className="admin-table"><caption className="admin-sr-only">추천 후보 차량</caption>
        <thead><tr><th scope="col">차량</th><th scope="col">연식</th><th scope="col">가격</th><th scope="col">연료 · 연비</th><th scope="col">승차 정원</th><th scope="col">확인일</th><th scope="col">상세</th></tr></thead>
        <tbody>{rows.map(car => <tr key={car.id} className={selected?.id === car.id ? 'is-selected' : undefined}>
          <td><strong>{car.brand} {car.model}</strong><small>{car.trim}</small></td><td>{car.year ?? '-'}</td><td>{manwon(car.price)}</td>
          <td>{FUEL_LABELS[car.fuel] ?? car.fuel ?? '-'}{car.efficiency != null ? ` · ${car.efficiency}` : ''}</td>
          <td>{car.seatsLabel ?? '-'}{needsSeatCheck(car) && <small>확인 필요</small>}</td><td>{car.checkedOn ?? '-'}</td>
          <td><button type="button" className="admin-text-button" onClick={() => setSelectedId(car.id)}>보기</button></td></tr>)}</tbody></table></div>}
      <p className="admin-result-count" aria-live="polite">검색 결과 {filtered.length}건</p>
      {totalPages > 1 && <nav className="admin-member-pagination" aria-label="후보 차량 페이지">
        <button type="button" disabled={page <= 1} onClick={() => change({ page: page - 1 })}>이전</button><span>{page} / {totalPages}</span>
        <button type="button" disabled={page >= totalPages} onClick={() => change({ page: page + 1 })}>다음</button></nav>}
    </section>
    {selected && <div className="admin-grid-2">
      <section className="admin-card"><div className="admin-card-heading"><div><h3>사용자 카드 미리보기</h3><p>{selected.brand} · {FUEL_LABELS[selected.fuel] ?? selected.fuel}</p></div></div>
        <article className="admin-recommendation-preview"><div className="admin-preview-image">
          {image ? <img src={image.src} alt={image.alt ?? `${selected.model} 대표 이미지`} /> : <p className="admin-empty">이 차종은 대표 이미지가 없습니다.</p>}
          <span className="admin-image-label"><Image size={theme.iconSize.sm} aria-hidden="true" />차종 대표 이미지 (색상 · 트림은 다를 수 있음)</span></div>
          <div className="admin-preview-body"><p>{selected.year ?? ''} · {selected.trim}</p><h3>{selected.brand} {selected.model}</h3>
            <div className="admin-preview-reason"><strong>{manwon(selected.price)}</strong><p>{FUEL_LABELS[selected.fuel] ?? selected.fuel}{selected.efficiency != null ? ` · 연비 ${selected.efficiency}` : ''}{selected.lengthMm ? ` · 전장 ${selected.lengthMm.toLocaleString('ko-KR')}mm` : ''}{selected.seatsLabel ? ` · ${selected.seatsLabel}` : ''}</p></div></div>
        </article>
      </section>
      <section className="admin-card"><div className="admin-card-heading"><div><h3>검수 정보</h3><p>데이터 출처와 확인 상태</p></div></div>
        <dl className="admin-detail-list">
          <div><dt>후보 번호</dt><dd>{selected.id}</dd></div>
          <div><dt>가격 출처</dt><dd>{selected.sourceUrl ? <a className="admin-text-button" href={selected.sourceUrl} target="_blank" rel="noreferrer">제조사 가격표 열기<ExternalLink size={theme.iconSize.sm} aria-hidden="true" /></a> : '없음'}</dd></div>
          <div><dt>출처 확인일</dt><dd>{selected.checkedOn ?? '-'}</dd></div>
          <div><dt>수집 방식</dt><dd>{QUALITY[selected.quality] ?? selected.quality ?? '-'}</dd></div>
          <div><dt>승차 정원 상태</dt><dd>{SEAT_STATUS[selected.seatsStatus] ?? selected.seatsStatus ?? '-'}{selected.seatsNote ? ` — ${selected.seatsNote}` : ''}</dd></div>
        </dl>
      </section>
    </div>}
  </div>;
}
