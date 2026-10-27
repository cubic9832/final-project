// 이메일 알림 설정 팝업 (Figma에는 없음. 마이페이지 "이메일 알림 → 설정" 버튼용으로 추가)
// 보완 9: [저장] 하면 onSave 가 서버에 저장한다 (PUT /members/me/notifications). 실패하면 팝업 안에 오류
import { useState } from 'react';
import AuthModal from '../../features/auth/components/AuthModal';
import { NOTIFICATION_OPTIONS } from './notificationOptions';
import './EmailNotificationModal.css';

export default function EmailNotificationModal({ currentValue, onSave, onClose }) {
  const [value, setValue] = useState(currentValue);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');

  async function handleSubmit(event) {
    event.preventDefault();
    setSaving(true);
    setError('');
    try {
      await onSave(value); // 성공하면 부모가 팝업을 닫는다
    } catch (err) {
      setError(err.response?.data?.error?.message ?? '알림 설정을 저장하지 못했습니다. 잠시 후 다시 시도해 주세요.');
      setSaving(false);
    }
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

          {error && <p className="notification-error" role="alert">{error}</p>}
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
