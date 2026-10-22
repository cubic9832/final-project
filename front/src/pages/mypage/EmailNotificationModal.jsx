// 이메일 알림 설정 팝업 (Figma에는 없음. 마이페이지 "이메일 알림 → 설정" 버튼용으로 추가)
// 지금은 화면 안에서만 저장한다. API 연결 시 handleSubmit 에서 서버 요청으로 바꾼다.
import { useState } from 'react';
import AuthModal from '../../features/auth/components/AuthModal';
import { NOTIFICATION_OPTIONS } from './notificationOptions';
import './EmailNotificationModal.css';

export default function EmailNotificationModal({ currentValue, onSave, onClose }) {
  const [value, setValue] = useState(currentValue);
  const [saving, setSaving] = useState(false);

  function handleSubmit(event) {
    event.preventDefault();
    // 저장 중 상태를 보여 주기 위한 임시 지연. API 연결 시 서버 요청으로 바꾼다
    setSaving(true);
    setTimeout(() => onSave(value), 400);
  }

  return (
    <AuthModal
      title="이메일 알림 설정"
      subtitle="받을 이메일 알림의 범위를 선택하세요."
      onClose={onClose}
      isDirty={value !== currentValue}
      busy={saving}
    >
      {(requestClose) => (
        <form onSubmit={handleSubmit}>
          <fieldset className="notification-options" disabled={saving}>
            <legend className="notification-legend">이메일 알림 범위</legend>
            {NOTIFICATION_OPTIONS.map((option) => (
              <label
                className={value === option.value ? 'notification-option is-selected' : 'notification-option'}
                key={option.value}
              >
                <input
                  type="radio"
                  name="email-notification"
                  value={option.value}
                  checked={value === option.value}
                  onChange={() => setValue(option.value)}
                  data-autofocus={value === option.value ? true : undefined}
                />
                <span>
                  <strong>{option.label}</strong>
                  <small>{option.description}</small>
                </span>
              </label>
            ))}
          </fieldset>

          <div className="auth-modal-actions">
            <button className="auth-modal-button" type="button" onClick={requestClose} disabled={saving}>
              취소
            </button>
            <button className="auth-modal-button auth-modal-button-primary" type="submit" disabled={saving}>
              {saving ? '저장 중…' : '저장'}
            </button>
          </div>
        </form>
      )}
    </AuthModal>
  );
}
