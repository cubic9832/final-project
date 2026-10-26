import { useEffect, useRef, useState } from 'react';
import { ArrowLeft, Car, Check, ImagePlus, Save, X } from 'lucide-react';
import theme from '../../../styles/theme';
import { emptyVehicle, vehicleFuels, vehicleStatuses } from './vehicleManagementExamples.js';

function VehicleField({ name, label, value, onChange, options, suffix, required, ...props }) {
  const id = `vehicle-editor-${name}`;
  return <div className="vehicle-editor-field"><label htmlFor={id}>{label}{required && <span className="vehicle-editor-required"> *</span>}</label><div className="vehicle-editor-input-wrap">
    {options ? <select id={id} value={value} onChange={event => onChange(name, event.target.value)} {...props}>{options.map(option => <option key={option}>{option}</option>)}</select>
      : <input id={id} value={value} onChange={event => onChange(name, event.target.value)} required={required} {...props} />}{suffix && <span>{suffix}</span>}
  </div></div>;
}

export default function VehicleEditor({ vehicle, onCancel, onSave }) {
  const initial = { ...emptyVehicle, ...vehicle };
  const [draft, setDraft] = useState(initial);
  const [discard, setDiscard] = useState(false);
  const [imageError, setImageError] = useState('');
  const [readingImage, setReadingImage] = useState(false);
  const heading = useRef(null);
  const picker = useRef(null);
  const reader = useRef(null);
  const editing = Boolean(vehicle?.id);
  const dirty = JSON.stringify(draft) !== JSON.stringify(initial);
  useEffect(() => {
    heading.current?.focus();
    return () => reader.current?.abort();
  }, []);
  const change = (name, value) => { setDraft(current => ({ ...current, [name]: value })); setDiscard(false); };
  const close = () => { if (dirty) setDiscard(true); else onCancel(); };
  const field = (name, label, props = {}) => <VehicleField name={name} label={label} value={draft[name]} onChange={change} {...props} />;
  function upload(event) {
    const file = event.target.files?.[0];
    if (!file) return;
    if (!['image/webp', 'image/png', 'image/jpeg'].includes(file.type) || file.size > 5 * 1024 * 1024) {
      setImageError('5MB 이하의 WebP, PNG, JPG 이미지를 선택해 주세요.'); return;
    }
    reader.current?.abort();
    const next = new FileReader(); reader.current = next;
    setReadingImage(true); setImageError('');
    next.onload = () => { change('image', next.result); setReadingImage(false); };
    next.onerror = () => { setImageError('이미지를 읽지 못했어요. 다른 파일을 선택해 주세요.'); setReadingImage(false); };
    next.readAsDataURL(file);
  }
  function save(event) {
    event.preventDefault();
    if (!readingImage) onSave(draft);
  }
  return <form className="vehicle-management vehicle-editor" onSubmit={save}>
    <button type="button" className="admin-text-button vehicle-editor-back" onClick={close}><ArrowLeft size={theme.iconSize.sm} aria-hidden="true" />차량 목록</button>
    <div className="vehicle-management-toolbar"><div><h3 ref={heading} tabIndex={-1}>{editing ? '차량 정보 수정' : '새 차량 등록'}</h3><p>가격과 제원이 같은 트림·사양을 가리키도록 입력해 주세요.</p></div><span className="admin-count-badge">{editing ? '정보 편집' : '신규 등록'}</span></div>
    <div className="vehicle-editor-layout"><div className="admin-panel-stack">
      <section className="admin-card"><div className="admin-card-heading"><div><h3>기본 정보</h3><p><span className="vehicle-editor-required">*</span> 표시는 미리보기 저장에 필요한 항목입니다.</p></div></div><div className="vehicle-editor-fields">
        {field('brand', '브랜드', { required: true, placeholder: '예: 현대, 기아, BMW', maxLength: 40 })}
        {field('model', '모델명', { required: true, placeholder: '예: 쏘나타, 스포티지', maxLength: 80 })}
        {field('year', '연식', { placeholder: '예: 2026', inputMode: 'numeric', pattern: '[0-9]{4}', maxLength: 4, suffix: '년형' })}
        {field('trim', '트림명', { required: true, placeholder: '예: 프레스티지', maxLength: 100 })}
        {field('origin', '구분', { options: ['국산', '수입'] })}
        {field('body', '차체 종류', { options: ['미확인', '경차', '세단', 'SUV', '해치백', '왜건', '승합', '픽업트럭'] })}
      </div></section>
      <section className="admin-card"><div className="admin-card-heading"><div><h3>가격과 차량 사양</h3><p>선택 옵션을 제외한 해당 구성의 가격과 기본 사양입니다.</p></div></div><div className="vehicle-editor-fields">
        {field('price', '판매 가격', { required: true, placeholder: '예: 2892', inputMode: 'decimal', pattern: '[0-9]+([.][0-9]{1,2})?', suffix: '만 원' })}
        {field('fuel', '연료', { options: vehicleFuels })}
        {field('efficiency', draft.fuel === '전기' ? '복합 전비' : '복합 연비', { inputMode: 'decimal', pattern: '[0-9]+([.][0-9]{1,2})?', placeholder: '예: 12.6', suffix: draft.fuel === '전기' ? 'km/kWh' : 'km/L' })}
        {field('drive', '구동 방식', { options: ['2WD', '4WD', 'AWD', '미확인'] })}
        {field('seats', '기본 승차 정원', { placeholder: '예: 5', inputMode: 'numeric', pattern: '[0-9]{1,2}', suffix: '명' })}
        {field('length', '전장', { placeholder: '예: 4905', inputMode: 'numeric', pattern: '[0-9]{4}', suffix: 'mm' })}
      </div></section>
      <section className="admin-card"><div className="admin-card-heading"><div><h3>자료 출처</h3><p>가격과 제원을 확인한 자료를 연결해 주세요.</p></div></div><div className="vehicle-editor-fields">
        {field('source', '자료명', { placeholder: '예: 제조사 공식 가격표', maxLength: 100 })}
        {field('checkedOn', '확인일', { type: 'date' })}
        <div className="vehicle-editor-wide">{field('sourceUrl', '출처 URL', { type: 'url', placeholder: 'https://', maxLength: 2000 })}</div>
        <div className="vehicle-editor-wide vehicle-editor-field"><label htmlFor="vehicle-editor-memo">관리 메모</label><textarea id="vehicle-editor-memo" rows={3} value={draft.memo} maxLength={500} onChange={event => change('memo', event.target.value)} placeholder="확인할 사항이나 변경 이유를 남겨 주세요." /></div>
      </div></section>
    </div><aside className="vehicle-editor-aside">
      <section className="admin-card vehicle-editor-preview"><div className="admin-card-heading"><div><h3>차량 이미지</h3><p>사용자 화면에 표시할 이미지입니다.</p></div></div><div className="vehicle-editor-image">{draft.image ? <img src={draft.image} alt={`${draft.brand} ${draft.model} 미리보기`} /> : <div><Car size={theme.iconSize.lg} aria-hidden="true" /><span>차량 이미지를 추가해 주세요.</span></div>}</div>
        <input ref={picker} type="file" accept="image/webp,image/png,image/jpeg" className="admin-sr-only" aria-label="차량 이미지 파일" onChange={upload} />
        <button type="button" className="admin-outline-button" disabled={readingImage} onClick={() => picker.current?.click()}><ImagePlus size={theme.iconSize.sm} aria-hidden="true" />{readingImage ? '이미지 읽는 중' : draft.image ? '이미지 변경' : '이미지 선택'}</button><p className="vehicle-editor-hint">WebP, PNG, JPG · 최대 5MB<br />배경 없는 전면 사선 이미지를 권장해요.</p>{imageError && <p className="vehicle-editor-error" role="alert">{imageError}</p>}
        <div className="vehicle-editor-preview-info"><small>{draft.brand || '브랜드'} · {draft.fuel}</small><h4>{draft.model || '모델명'}</h4><p>{draft.trim || '트림명'}</p><strong>{draft.price ? `${Number(draft.price).toLocaleString('ko-KR')}만 원` : '가격 미입력'}</strong></div>
      </section>
      <section className="admin-card"><div className="admin-card-heading"><div><h3>관리 상태</h3><p>목록에 표시할 상태를 선택하세요.</p></div></div>{field('status', '상태', { options: vehicleStatuses })}<p className="vehicle-editor-hint">현재는 화면 검토용으로만 적용됩니다.</p></section>
    </aside></div>
    <footer className="admin-card vehicle-editor-footer">{discard ? <div className="vehicle-editor-discard" role="alert"><div><strong>작성한 내용을 저장하지 않고 닫을까요?</strong><p>편집 중인 내용은 사라집니다.</p></div><button type="button" className="admin-outline-button" onClick={() => setDiscard(false)}>계속 작성</button><button type="button" className="admin-primary-button" onClick={onCancel}>저장하지 않고 닫기</button></div>
      : <><p><Check size={theme.iconSize.sm} aria-hidden="true" />이 화면에만 임시 저장되며 실제 서비스에는 반영되지 않습니다.</p><div><button type="button" className="admin-outline-button" onClick={close}><X size={theme.iconSize.sm} aria-hidden="true" />취소</button><button type="submit" className="vehicle-management-cta" disabled={readingImage}><Save size={theme.iconSize.sm} aria-hidden="true" />미리보기 저장</button></div></>}
    </footer>
  </form>;
}
