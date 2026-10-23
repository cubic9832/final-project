import AuthModal from '../../../auth/components/AuthModal';

export default function TasteSaveModal({ previous, next, types, onClose, onSave, error, busy }) {
  return (
    <AuthModal title="현재 취향을 바꿀까요?" subtitle="현재 취향은 하나만 저장돼요. 테스트는 언제든 다시 할 수 있어요." onClose={onClose} size="lg" busy={busy}>
      <div className="taste-save-comparison"><section><p>지금 저장된 취향</p><h3>{types[previous]?.name ?? previous}</h3></section><section><p>새로 저장할 취향</p><h3>{types[next].name}</h3></section></div>
      <p className="taste-muted">저장하면 회원님의 기존 취향이 새 결과로 대체됩니다.</p>
      {error && <p className="taste-error" role="alert">{error}</p>}
      <div className="taste-actions"><button type="button" className="taste-button taste-button-outline" onClick={onClose} disabled={busy} data-autofocus>취소</button><button type="button" className="taste-button taste-button-cta" onClick={onSave} disabled={busy}>{busy ? '저장 중…' : error ? '다시 저장하기' : '이 취향으로 변경'}</button></div>
    </AuthModal>
  );
}
