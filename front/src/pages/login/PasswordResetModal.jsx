// 비밀번호 찾기 팝업 (Figma: AUTH 01-1 · 비밀번호 찾기 팝업)
// 비밀번호 재설정 API는 아직 없다. 지금은 이메일 형식만 검사하고 요청 완료 화면까지 보여 준다.
import { useState } from 'react';
import AuthModal from '../../features/auth/components/AuthModal';
import './PasswordResetModal.css';

const EMAIL_PATTERN = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

export default function PasswordResetModal({ initialEmail = '', onClose }) {
  const [email, setEmail] = useState(initialEmail);
  const [error, setError] = useState('');
  // 진행 단계: 'input'(이메일 입력) → 'sending'(요청 중) → 'done'(요청 완료)
  const [step, setStep] = useState('input');

  function handleSubmit(event) {
    event.preventDefault();
    const trimmed = email.trim();

    if (!trimmed) {
      setError('이메일을 입력해 주세요.');
      return;
    }
    if (!EMAIL_PATTERN.test(trimmed)) {
      setError('이메일 형식이 올바르지 않습니다.');
      return;
    }

    // 요청 중 상태를 보여 주기 위한 임시 지연. API 연결 시 서버 요청으로 바꾼다
    setStep('sending');
    setTimeout(() => setStep('done'), 400);
  }

  if (step === 'done') {
    return (
      <AuthModal title="안내를 요청했어요" onClose={onClose} size="sm">
        <p className="password-reset-done">
          등록된 이메일이 확인되면 <strong>{email.trim()}</strong> 으로 재설정 안내가 발송됩니다.
        </p>
        <p className="auth-modal-hint">서버 연결 전이라 실제 메일은 발송되지 않습니다.</p>
        <div className="auth-modal-actions auth-modal-actions-single">
          <button className="auth-modal-button auth-modal-button-primary" type="button" onClick={onClose}>
            확인
          </button>
        </div>
      </AuthModal>
    );
  }

  const sending = step === 'sending';

  return (
    <AuthModal
      title="비밀번호 찾기"
      subtitle="가입할 때 사용한 이메일을 입력하면 비밀번호를 다시 설정할 수 있는 안내를 보내드립니다."
      onClose={onClose}
      busy={sending}
      size="sm"
    >
      <form onSubmit={handleSubmit} noValidate>
        <div className="auth-modal-field">
          <label htmlFor="reset-email">이메일</label>
          <input
            id="reset-email"
            type="email"
            placeholder="name@example.com"
            autoComplete="email"
            value={email}
            onChange={(event) => {
              setEmail(event.target.value);
              setError('');
            }}
            disabled={sending}
            data-autofocus
            className={error ? 'has-error' : undefined}
            aria-invalid={Boolean(error)}
            aria-describedby={error ? 'reset-email-error' : 'reset-email-hint'}
          />
          {error ? (
            <p className="auth-modal-error" id="reset-email-error">
              {error}
            </p>
          ) : (
            <p className="auth-modal-hint" id="reset-email-hint">
              등록된 이메일이 확인되면 재설정 안내가 발송됩니다.
            </p>
          )}
        </div>

        <div className="auth-modal-actions">
          <button className="auth-modal-button" type="button" onClick={onClose} disabled={sending}>
            취소
          </button>
          <button className="auth-modal-button auth-modal-button-primary" type="submit" disabled={sending}>
            {sending ? '요청 중…' : '재설정 링크 받기'}
          </button>
        </div>
      </form>
    </AuthModal>
  );
}
