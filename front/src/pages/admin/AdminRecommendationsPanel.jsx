import { useState } from 'react';
import { Check, Image, PencilLine } from 'lucide-react';
import theme from '../../styles/theme';
import { recommendationExamples } from './adminExampleData';

export default function AdminRecommendationsPanel() {
  const [selectedId, setSelectedId] = useState(recommendationExamples[0].id);
  const [drafts, setDrafts] = useState({});
  const [previews, setPreviews] = useState({});
  const [notice, setNotice] = useState('');
  const selected = recommendationExamples.find(item => item.id === selectedId);
  const draft = drafts[selectedId] ?? selected.reason;
  const preview = previews[selectedId] ?? selected.reason;
  function previewReason(event) {
    event.preventDefault();
    if (!draft.trim()) { setNotice('추천 사유를 입력해 주세요.'); return; }
    setPreviews(current => ({ ...current, [selectedId]: draft.trim() }));
    setNotice(`${selected.model} 카드 미리보기에 반영했습니다. 실제 서비스에는 저장되지 않습니다.`);
  }
  return <div className="admin-panel-stack"><section className="admin-card"><div className="admin-card-heading"><div><h3>추천 카드 검수</h3><p>추천 라벨 20종 중 4종으로 구성한 UI 예시입니다.</p></div><span className="admin-count-badge">이미지 · 주요 정보 · 추천 사유</span></div><div className="admin-recommendation-picker" aria-label="미리볼 차량 선택">{recommendationExamples.map(vehicle => <button type="button" key={vehicle.id} aria-pressed={selectedId === vehicle.id} onClick={() => { setSelectedId(vehicle.id); setNotice(''); }}><img src={vehicle.image} alt="" /><span>{vehicle.model}</span><small>{vehicle.labelCode}</small></button>)}</div></section>
    <div className="admin-grid-2"><section className="admin-card"><div className="admin-card-heading"><div><h3>사용자 카드 미리보기</h3><p>{selected.labelCode} · {selected.purpose}</p></div><span className="admin-status is-ok">미리보기</span></div><article className="admin-recommendation-preview"><div className="admin-preview-image"><img src={selected.image} alt={`${selected.model} 추천 예시`} /><span className="admin-image-label"><Image size={theme.iconSize.sm} aria-hidden="true" />배경 제거 이미지</span></div><div className="admin-preview-body"><p>{selected.brand} · {selected.body} · {selected.grade}</p><h3>{selected.model}</h3><div className="admin-preview-reason"><strong>추천 사유</strong><p>{preview}</p></div><small>차체·이용목적 기준의 참고 설명입니다.</small></div></article></section>
      <section className="admin-card"><div className="admin-card-heading"><div><h3>추천 사유 구성</h3><p>차량별 문구의 길이와 표현을 검토하세요.</p></div><PencilLine size={theme.iconSize.md} aria-hidden="true" /></div><form className="admin-editor" onSubmit={previewReason}><dl className="admin-detail-list"><div><dt>차량 라벨</dt><dd>{selected.labelCode}</dd></div><div><dt>주 이용목적</dt><dd>{selected.purpose}</dd></div><div><dt>설명 구분</dt><dd>규칙 기반 참고 설명</dd></div></dl><label htmlFor="admin-reason">추천 사유<textarea id="admin-reason" maxLength={300} rows={5} value={draft} onChange={event => { setDrafts(current => ({ ...current, [selectedId]: event.target.value })); setNotice(''); }} /></label><span className="admin-character-count">{draft.length} / 300자</span><div className="admin-inline-note"><Check size={theme.iconSize.sm} aria-hidden="true" /><span>구매 가능 여부나 모델의 개별 판단 근거로 단정하지 않습니다.</span></div><button type="submit" className="admin-primary-button">카드에 미리보기</button><p className="admin-feedback" role="status">{notice || '미리보기는 이 탭 안에서만 유지됩니다.'}</p></form></section></div>
  </div>;
}
