import AuthModal from '../auth/AuthModal';
import { tasteTypes } from './tasteQuestions';

export default function TasteSaveModal({ previous, next, onClose, onSave, error }) {
  return (
    <AuthModal title="현재 취향을 바꿀까요?" subtitle="현재 취향은 하나만 저장돼요. 테스트는 언제든 다시 할 수 있어요." onClose={onClose} size="lg">
      <div className="taste-save-comparison"><section><p>지금 저장된 취향</p><h3>{tasteTypes[previous].name}</h3></section><section><p>새로 저장할 취향</p><h3>{tasteTypes[next].name}</h3></section></div>
      <p className="taste-muted">변경하면 이 브라우저에 저장된 기존 취향이 새 결과로 대체됩니다.</p>
      {error && <p className="taste-error" role="alert">{error}</p>}
      <div className="taste-actions"><button type="button" className="taste-button taste-button-outline" onClick={onClose} data-autofocus>취소</button><button type="button" className="taste-button taste-button-cta" onClick={onSave}>{error ? '다시 저장하기' : '이 취향으로 변경'}</button></div>
    </AuthModal>
  );
}
