import { useEffect, useRef, useState } from 'react';
import './ProfileEditModal.css';

const NICKNAME_MAX_LENGTH = 50; // users.nick_name VARCHAR(50)

// 예: firstcar@example.com → fi***@example.com
function maskEmail(email) {
  const [id, domain] = email.split('@');
  return `${id.slice(0, 2)}***@${domain}`;
}

// 프로필 정보 수정 팝업 (Figma FLOW 05-3).
// 지금은 화면 안에서만 저장한다. API 연결 시 handleSubmit 에서 서버 요청으로 바꾼다.
export default function ProfileEditModal({ nickname, email, onSave, onClose }) {
  const [value, setValue] = useState(nickname);
  const [error, setError] = useState('');
  const [saving, setSaving] = useState(false);
  const [confirmingDiscard, setConfirmingDiscard] = useState(false);
  const [notice, setNotice] = useState('');
  const dialogRef = useRef(null);
  const inputRef = useRef(null);

  const isDirty = value.trim() !== nickname;

  // 팝업이 열리면 입력칸으로 포커스를 옮긴다
  useEffect(() => {
    inputRef.current?.focus();
  }, []);

  // 닫기 요청: 저장 중이면 무시하고, 수정한 내용이 있으면 먼저 폐기 여부를 묻는다
  function requestClose() {
    if (saving) return;
    if (isDirty) setConfirmingDiscard(true);
    else onClose();
  }

  // Esc 로 닫기, Tab 키 포커스를 팝업 안에서만 돌게 한다
  function handleKeyDown(event) {
    if (event.key === 'Escape') {
      event.stopPropagation();
      requestClose();
      return;
    }
    if (event.key !== 'Tab') return;

    const focusable = dialogRef.current.querySelectorAll('button:not(:disabled), input:not(:disabled)');
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

  function handleChange(event) {
    setValue(event.target.value);
    setError('');
    setConfirmingDiscard(false);
  }

  function handleSubmit(event) {
    event.preventDefault();
    const trimmed = value.trim();

    if (!trimmed) {
      setError('표시 이름을 입력해 주세요.');
      return;
    }
    if (trimmed.length > NICKNAME_MAX_LENGTH) {
      setError(`표시 이름은 ${NICKNAME_MAX_LENGTH}자 이하로 입력해 주세요.`);
      return;
    }

    // 저장 중 상태를 보여 주기 위한 임시 지연. API 연결 시 서버 요청으로 바꾼다
    setSaving(true);
    setTimeout(() => onSave(trimmed), 400);
  }

  return (
    <div
      className="profile-modal-backdrop"
      onMouseDown={(event) => {
        if (event.target === event.currentTarget) requestClose(); // 바깥(어두운 배경) 클릭
      }}
    >
      <div
        ref={dialogRef}
        className="profile-modal"
        role="dialog"
        aria-modal="true"
        aria-labelledby="profile-modal-title"
        onKeyDown={handleKeyDown}
      >
        <div className="profile-modal-header">
          <h2 id="profile-modal-title">프로필 정보 수정</h2>
          <button className="profile-modal-close" type="button" aria-label="닫기" onClick={requestClose}>
            ×
          </button>
        </div>
        <p className="profile-modal-subtitle">기본 정보를 수정하고 저장하세요.</p>
        <p className="profile-modal-example">예시 데이터 · 실제 개인정보를 사용하지 않습니다.</p>

        <form onSubmit={handleSubmit} noValidate>
          <div className="profile-modal-field">
            <label htmlFor="profile-nickname">표시 이름</label>
            <input
              ref={inputRef}
              id="profile-nickname"
              type="text"
              value={value}
              onChange={handleChange}
              disabled={saving}
              className={error ? 'has-error' : undefined}
              aria-invalid={Boolean(error)}
              aria-describedby={error ? 'profile-nickname-error' : undefined}
            />
            {error && (
              <p className="profile-modal-error" id="profile-nickname-error">
                {error}
              </p>
            )}
          </div>

          <div className="profile-modal-field">
            <label htmlFor="profile-email">이메일</label>
            <input id="profile-email" type="text" value={maskEmail(email)} readOnly disabled />
            <p className="profile-modal-hint">이메일 변경 정책과 본인 확인 방식은 미정입니다.</p>
          </div>

          <div className="profile-modal-section">
            <h3>재무·차량 입력정보</h3>
            <div className="profile-modal-info">
              <strong>소득·지출, 자산·부채, 신용정보, 차량 이용조건</strong>
              <p>변경하려면 해당 입력 단계로 이동해 다시 분석하세요.</p>
              <button
                className="profile-modal-link"
                type="button"
                onClick={() => setNotice('입력정보 수정 화면은 준비 중입니다.')}
              >
                입력정보 수정으로 이동 →
              </button>
            </div>
            <p className="profile-modal-hint">프로필 저장은 기존 분석 결과를 다시 계산하지 않습니다.</p>
          </div>

          <p className="profile-modal-notice" role="status">
            {notice}
          </p>

          {confirmingDiscard ? (
            <div className="profile-modal-discard" role="alert">
              <p>수정한 내용을 저장하지 않고 닫을까요?</p>
              <div className="profile-modal-actions">
                <button className="profile-modal-cancel" type="button" onClick={() => setConfirmingDiscard(false)}>
                  계속 수정
                </button>
                <button className="profile-modal-save" type="button" onClick={onClose}>
                  저장하지 않고 닫기
                </button>
              </div>
            </div>
          ) : (
            <div className="profile-modal-actions">
              <button className="profile-modal-cancel" type="button" onClick={requestClose} disabled={saving}>
                취소
              </button>
              <button className="profile-modal-save" type="submit" disabled={saving}>
                {saving ? '저장 중…' : '변경사항 저장'}
              </button>
            </div>
          )}
        </form>
      </div>
    </div>
  );
}
