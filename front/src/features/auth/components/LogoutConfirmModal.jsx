// 로그아웃 확인 팝업 (보완 1 · 회의 결정 "공용 모달")
// 새 팝업 틀을 만들지 않고, 다른 팝업 7개가 함께 쓰는 공용 틀 AuthModal 에 내용만 넣는다.
import { useState } from 'react';
import AuthModal from './AuthModal';

export default function LogoutConfirmModal({ onConfirm, onClose }) {
  const [loggingOut, setLoggingOut] = useState(false); // 서버 로그아웃 요청 중 (버튼 비활성, 팝업 닫기 막기)

  async function handleConfirm() {
    setLoggingOut(true);
    await onConfirm(); // 서버 로그아웃 → 메인 이동 → 알림 (Header 가 처리)
  }

  return (
    <AuthModal title="로그아웃" onClose={onClose} busy={loggingOut} size="sm">
      {(requestClose) => (
        <>
          <p>로그아웃하시겠습니까?</p>
          <div className="auth-modal-actions">
            <button className="auth-modal-button" type="button" onClick={requestClose} disabled={loggingOut}>
              취소
            </button>
            <button
              className="auth-modal-button auth-modal-button-primary"
              type="button"
              onClick={handleConfirm}
              disabled={loggingOut}
              data-autofocus
            >
              {loggingOut ? '로그아웃 중…' : '로그아웃'}
            </button>
          </div>
        </>
      )}
    </AuthModal>
  );
}
