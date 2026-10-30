// 8단계: 채팅의 확인 팝업 (상담 종료 · 제한 · 제한 풀기)
// 브라우저 기본 확인창(window.confirm) 대신, 로그아웃 · 비밀번호 변경 팝업이 같이 쓰는 공용 틀 AuthModal 에 내용만 넣는다
import { useState } from 'react';
import AuthModal from '../../auth/components/AuthModal';

export default function ChatConfirmModal({ title, message, confirmLabel, danger = false, onConfirm, onClose }) {
  const [working, setWorking] = useState(false); // 처리 중 (버튼 비활성, 팝업 닫기 막기)

  async function handleConfirm() {
    setWorking(true);
    try {
      await onConfirm();
    } finally {
      setWorking(false);
      onClose();
    }
  }

  return (
    <AuthModal title={title} onClose={onClose} busy={working} size="sm">
      {(requestClose) => (
        <>
          <p>{message}</p>
          <div className="auth-modal-actions">
            <button className="auth-modal-button" type="button" onClick={requestClose} disabled={working}>
              취소
            </button>
            <button
              className={`auth-modal-button ${danger ? 'auth-modal-button-danger' : 'auth-modal-button-primary'}`}
              type="button"
              onClick={handleConfirm}
              disabled={working}
              data-autofocus
            >
              {working ? '처리 중…' : confirmLabel}
            </button>
          </div>
        </>
      )}
    </AuthModal>
  );
}
