// 비밀번호 찾기 팝업 (Figma: AUTH 01-1 · 비밀번호 찾기 팝업)
// 보완 7 추가(10-20): 회원가입 이메일 인증과 같은 방식으로 본인 확인 후 새 비밀번호로 바꾼다
// 단계: 'email'(이메일 → 인증 코드 받기) → 'code'(코드 확인) → 'password'(새 비밀번호) → 'done'(완료)
// 이전에는 이메일 형식만 보고 "요청 완료" 화면만 보여 줬다 (실제 메일 · 변경 없음)
import { useEffect, useState } from 'react';
import AuthModal from '../../features/auth/components/AuthModal';
import PasswordInput from '../../features/auth/components/PasswordInput';
import { confirmPasswordResetCode, resetPassword, sendPasswordResetCode } from '../../features/auth/authApi';
import { getPasswordRules, PASSWORD_MAX, validatePassword } from '../../features/auth/passwordPolicy';
import './PasswordResetModal.css';

const EMAIL_PATTERN = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

// 서버 실패 봉투 { error: { message } } 에서 문구 꺼내기
const messageOf = (error, fallback) => error.response?.data?.error?.message ?? fallback;

export default function PasswordResetModal({ initialEmail = '', onClose }) {
  const [step, setStep] = useState('email');
  const [email, setEmail] = useState(initialEmail);
  const [code, setCode] = useState('');
  const [password, setPassword] = useState('');
  const [passwordConfirm, setPasswordConfirm] = useState('');
  const [error, setError] = useState('');
  const [notice, setNotice] = useState('');
  const [busy, setBusy] = useState(false); // 서버 요청 중
  const [timer, setTimer] = useState(null); // 코드를 보낸 상태 { expiresAt, resendAt } (ms)
  const [now, setNow] = useState(() => Date.now());

  // 코드를 보낸 동안 1초마다 남은 시간 · 다시 받기 대기 시간을 다시 그린다
  useEffect(() => {
    if (!timer) return undefined;
    const id = setInterval(() => setNow(Date.now()), 1000);
    return () => clearInterval(id);
  }, [timer]);

  const codeLeft = timer ? Math.max(0, Math.ceil((timer.expiresAt - now) / 1000)) : 0;
  const resendWait = timer ? Math.max(0, Math.ceil((timer.resendAt - now) / 1000)) : 0;
  const passwordRules = getPasswordRules(password, email);

  // ① 인증 코드 받기 (다시 받기도 같은 함수)
  async function handleSendCode(event) {
    event?.preventDefault();
    const trimmed = email.trim();
    if (!trimmed) return setError('이메일을 입력해 주세요.');
    if (!EMAIL_PATTERN.test(trimmed)) return setError('이메일 형식이 올바르지 않습니다.');

    setBusy(true);
    setError('');
    try {
      const result = await sendPasswordResetCode(trimmed);
      if (result.alreadyVerified) {
        // 30분 안에 이미 인증을 마쳤으면 바로 새 비밀번호 단계로
        setStep('password');
        setNotice('');
        return;
      }
      const sentAt = Date.now();
      setTimer({ expiresAt: sentAt + result.expiresInSeconds * 1000, resendAt: sentAt + result.resendAfterSeconds * 1000 });
      setNow(sentAt);
      setCode('');
      setStep('code');
      setNotice(
        result.mailEnabled
          ? '인증 코드를 보냈습니다. 메일이 보이지 않으면 스팸함도 확인해 주세요.'
          : '개발 모드: 메일 대신 서버 로그에 인증 코드가 표시됩니다.',
      );
    } catch (err) {
      // 가입 안 한 이메일 · 구글 전용 계정 · 너무 자주 요청 등
      setError(messageOf(err, '인증 코드를 보내지 못했습니다. 잠시 후 다시 시도해 주세요.'));
    } finally {
      setBusy(false);
    }
  }

  // ② 코드 확인
  async function handleConfirmCode(event) {
    event.preventDefault();
    if (!/^\d{6}$/.test(code)) return setError('인증 코드 6자리를 입력해 주세요.');
    setBusy(true);
    setError('');
    try {
      await confirmPasswordResetCode(email.trim(), code);
      setStep('password');
      setNotice('');
    } catch (err) {
      setError(messageOf(err, '인증에 실패했습니다. 잠시 후 다시 시도해 주세요.'));
    } finally {
      setBusy(false);
    }
  }

  // ③ 새 비밀번호로 바꾸기 (회원가입과 같은 비밀번호 규칙)
  async function handleReset(event) {
    event.preventDefault();
    const ruleError = validatePassword(password, email.trim());
    if (ruleError) return setError(ruleError);
    if (password !== passwordConfirm) return setError('비밀번호가 일치하지 않습니다.');
    setBusy(true);
    setError('');
    try {
      await resetPassword(email.trim(), password);
      setStep('done');
    } catch (err) {
      setError(messageOf(err, '비밀번호를 바꾸지 못했습니다. 잠시 후 다시 시도해 주세요.'));
    } finally {
      setBusy(false);
    }
  }

  if (step === 'done') {
    return (
      <AuthModal title="비밀번호를 바꿨어요" onClose={onClose} size="sm">
        <p className="password-reset-done">
          <strong>{email.trim()}</strong> 계정의 비밀번호가 변경되었습니다. 새 비밀번호로 로그인해 주세요.
        </p>
        <p className="auth-modal-hint">보안을 위해 다른 기기의 로그인도 모두 끊었습니다.</p>
        <div className="auth-modal-actions auth-modal-actions-single">
          <button className="auth-modal-button auth-modal-button-primary" type="button" onClick={onClose}>
            확인
          </button>
        </div>
      </AuthModal>
    );
  }

  const errorText = error && (
    <p className="auth-modal-error" role="alert">
      {error}
    </p>
  );

  return (
    <AuthModal
      title="비밀번호 찾기"
      subtitle={
        step === 'password'
          ? '이메일 인증이 끝났어요. 새 비밀번호를 입력해 주세요.'
          : '가입할 때 사용한 이메일로 인증 코드를 보내 본인을 확인합니다.'
      }
      onClose={onClose}
      busy={busy}
      size="sm"
    >
      {step === 'email' && (
        <form onSubmit={handleSendCode} noValidate>
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
              disabled={busy}
              data-autofocus
              className={error ? 'has-error' : undefined}
            />
            {errorText}
          </div>
          <div className="auth-modal-actions">
            <button className="auth-modal-button" type="button" onClick={onClose} disabled={busy}>
              취소
            </button>
            <button className="auth-modal-button auth-modal-button-primary" type="submit" disabled={busy}>
              {busy ? '보내는 중…' : '인증 코드 받기'}
            </button>
          </div>
        </form>
      )}

      {step === 'code' && (
        <form onSubmit={handleConfirmCode} noValidate>
          <p className="password-reset-notice">{notice}</p>
          <div className="auth-modal-field">
            <label htmlFor="reset-code">
              인증 코드{' '}
              <span className="password-reset-timer">
                {codeLeft > 0 ? `${Math.floor(codeLeft / 60)}:${String(codeLeft % 60).padStart(2, '0')}` : '만료됨'}
              </span>
            </label>
            <input
              id="reset-code"
              type="text"
              inputMode="numeric"
              placeholder="인증 코드 6자리"
              autoComplete="one-time-code"
              maxLength={6}
              value={code}
              onChange={(event) => {
                setCode(event.target.value.replace(/\D/g, ''));
                setError('');
              }}
              disabled={busy}
              data-autofocus
              className={error ? 'has-error' : undefined}
            />
            {errorText}
          </div>
          <div className="auth-modal-actions">
            <button
              className="auth-modal-button password-reset-resend"
              type="button"
              onClick={handleSendCode}
              disabled={busy || resendWait > 0}
            >
              {resendWait > 0 ? `다시 받기 (${resendWait}초)` : '다시 받기'}
            </button>
            <button
              className="auth-modal-button auth-modal-button-primary"
              type="submit"
              disabled={busy || codeLeft <= 0}
            >
              {busy ? '확인 중…' : '확인'}
            </button>
          </div>
        </form>
      )}

      {step === 'password' && (
        <form onSubmit={handleReset} noValidate>
          <div className="auth-modal-field">
            <label htmlFor="reset-password">새 비밀번호</label>
            <PasswordInput
              id="reset-password"
              placeholder="영문·숫자·특수문자 포함 8~20자"
              autoComplete="new-password"
              maxLength={PASSWORD_MAX}
              value={password}
              onChange={(event) => {
                setPassword(event.target.value);
                setError('');
              }}
              disabled={busy}
            />
            <ul className="password-reset-rules" aria-label="비밀번호 조건">
              {passwordRules.map((rule) => (
                <li className={rule.met ? 'is-met' : ''} key={rule.label}>
                  {rule.met ? '✓' : '○'} {rule.label}
                </li>
              ))}
            </ul>
          </div>
          <div className="auth-modal-field">
            <label htmlFor="reset-password-confirm">새 비밀번호 확인</label>
            <PasswordInput
              id="reset-password-confirm"
              placeholder="새 비밀번호를 한 번 더 입력"
              autoComplete="new-password"
              maxLength={PASSWORD_MAX}
              value={passwordConfirm}
              onChange={(event) => {
                setPasswordConfirm(event.target.value);
                setError('');
              }}
              disabled={busy}
            />
            {errorText}
          </div>
          <div className="auth-modal-actions">
            <button className="auth-modal-button" type="button" onClick={onClose} disabled={busy}>
              취소
            </button>
            <button className="auth-modal-button auth-modal-button-primary" type="submit" disabled={busy}>
              {busy ? '변경 중…' : '비밀번호 변경'}
            </button>
          </div>
        </form>
      )}
    </AuthModal>
  );
}
