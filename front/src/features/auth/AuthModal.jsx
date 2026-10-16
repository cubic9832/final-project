// 로그인·회원가입·마이페이지 팝업이 함께 쓰는 틀
// 어두운 배경, 제목·닫기 버튼, Esc·바깥 클릭 닫기, 포커스 이동, 변경 폐기 확인을 맡는다.
// 각 팝업은 이 틀 안에 내용(children)만 넣는다.
// children 을 함수로 넘기면 requestClose 를 받아 "취소" 버튼에도 같은 닫기 규칙을 쓸 수 있다.
import { useEffect, useId, useRef, useState } from 'react';
import { X } from 'lucide-react';
import theme from '../../styles/theme';
import './AuthModal.css';

const FOCUSABLE = 'button:not(:disabled), input:not(:disabled), a[href], [tabindex]:not([tabindex="-1"])';

export default function AuthModal({
  title,
  subtitle,
  onClose,
  children,
  dismissible = true, // false: 위험한 작업이라 바깥 클릭·Esc로 닫지 않고 버튼으로만 닫는다
  isDirty = false, // true: 저장하지 않은 변경이 있어 닫기 전에 폐기 여부를 묻는다
  busy = false, // true: 저장 중이라 닫지 않는다
  size = 'md',
}) {
  const titleId = useId();
  const dialogRef = useRef(null);
  const [confirmingDiscard, setConfirmingDiscard] = useState(false);

  // 열릴 때: 팝업 안 첫 입력·버튼으로 포커스, 뒤 화면 스크롤 막기
  // 닫힐 때: 스크롤을 되돌리고, 팝업을 열었던 버튼으로 포커스를 돌려준다
  useEffect(() => {
    const opener = document.activeElement;
    const firstField = dialogRef.current.querySelector('[data-autofocus]')
      ?? dialogRef.current.querySelector(FOCUSABLE);
    firstField?.focus();

    const previousOverflow = document.body.style.overflow;
    document.body.style.overflow = 'hidden';

    return () => {
      document.body.style.overflow = previousOverflow;
      if (opener instanceof HTMLElement && opener.isConnected) opener.focus();
    };
  }, []);

  // 닫기 요청: 저장 중이면 무시하고, 변경이 있으면 팝업 안에서 폐기 여부를 먼저 묻는다
  function requestClose() {
    if (busy) return;
    if (isDirty) setConfirmingDiscard(true);
    else onClose();
  }

  // Esc 닫기, Tab 키 포커스가 팝업 밖으로 나가지 않게 한다
  function handleKeyDown(event) {
    if (event.key === 'Escape') {
      event.stopPropagation();
      if (dismissible) requestClose();
      return;
    }
    if (event.key !== 'Tab') return;

    const focusable = dialogRef.current.querySelectorAll(FOCUSABLE);
    if (focusable.length === 0) return;
    const first = focusable[0];
    const last = focusable[focusable.length - 1];
    if (event.shiftKey && document.activeElement === first) {
      event.preventDefault();
      last.focus();
    } else if (!event.shiftKey && document.activeElement === last) {
      event.preventDefault();
      first.focus();
    }
  }

  return (
    <div
      className="auth-modal-backdrop"
      onMouseDown={(event) => {
        // 어두운 배경을 직접 눌렀을 때만 닫는다 (팝업 안 클릭은 제외)
        if (dismissible && event.target === event.currentTarget) requestClose();
      }}
    >
      <div
        ref={dialogRef}
        className={`auth-modal auth-modal-${size}`}
        role={dismissible ? 'dialog' : 'alertdialog'}
        aria-modal="true"
        aria-labelledby={titleId}
        onKeyDown={handleKeyDown}
      >
        <div className="auth-modal-header">
          <h2 id={titleId}>{title}</h2>
          <button className="auth-modal-close" type="button" aria-label="닫기" onClick={requestClose}>
            <X size={theme.iconSize.md} strokeWidth={2} />
          </button>
        </div>
        {subtitle && <p className="auth-modal-subtitle">{subtitle}</p>}

        <div className="auth-modal-body">
          {typeof children === 'function' ? children(requestClose) : children}
        </div>

        {confirmingDiscard && (
          <div className="auth-modal-discard" role="alert">
            <p>수정한 내용을 저장하지 않고 닫을까요?</p>
            <div className="auth-modal-actions">
              <button className="auth-modal-button" type="button" onClick={() => setConfirmingDiscard(false)}>
                계속 수정
              </button>
              <button className="auth-modal-button auth-modal-button-primary" type="button" onClick={onClose}>
                저장하지 않고 닫기
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
