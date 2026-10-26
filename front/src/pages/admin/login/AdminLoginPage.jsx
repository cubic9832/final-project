// 7단계: 관리자 로그인 (/admin/login)
// 일반 로그인과 같은 POST /api/v1/auth/login 을 쓰고, 로그인한 회원의 role 이 ADMIN 이 아니면
// 바로 로그아웃시키고 "관리자 계정이 아닙니다" 를 보여 준다. 관리자 계정은 DB 에서 role 을 ADMIN 으로 바꿔 만든다.
// 화면 모양은 일반 로그인 화면(LoginPage.css)을 그대로 쓰고 카드 하나만 둔다 (회의: 기존 UI 유지)
import { useCallback, useState } from 'react';
import { Link, Navigate, useLocation, useNavigate } from 'react-router-dom';
import { login, logout } from '../../../features/auth/authApi';
import PasswordInput from '../../../features/auth/components/PasswordInput';
import useAuthStore from '../../../stores/useAuthStore';
import RecaptchaBox from '../../login/RecaptchaBox';
import '../../login/LoginPage.css';
import './AdminLoginPage.css';

const EMAIL_PATTERN = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

// 입력값 검사 — 일반 로그인 화면과 같은 규칙
function validate(form) {
  const errors = {};
  const email = form.email.trim();
  if (!email) errors.email = '이메일을 입력해 주세요.';
  else if (!EMAIL_PATTERN.test(email)) errors.email = '이메일 형식이 올바르지 않습니다.';
  if (!form.password) errors.password = '비밀번호를 입력해 주세요.';
  return errors;
}

export default function AdminLoginPage() {
  const navigate = useNavigate();
  const location = useLocation();
  const initialized = useAuthStore((state) => state.initialized);
  const member = useAuthStore((state) => state.member);
  const [form, setForm] = useState({ email: '', password: '' });
  const [errors, setErrors] = useState({});
  const [loginError, setLoginError] = useState('');
  const [submitting, setSubmitting] = useState(false);
  // 보완 6: 여러 번 틀리면 서버가 로봇 확인(reCAPTCHA)을 요구한다 — 일반 로그인과 같은 카운터
  const [captchaRequired, setCaptchaRequired] = useState(false);
  const [captchaToken, setCaptchaToken] = useState('');
  const [captchaResetKey, setCaptchaResetKey] = useState(0);

  const handleCaptchaChange = useCallback((token) => {
    setCaptchaToken(token);
    if (token) setErrors((prev) => ({ ...prev, captcha: undefined }));
  }, []);

  // 이미 관리자로 로그인했으면 바로 관리자 화면으로
  if (initialized && member?.role === 'ADMIN') {
    return <Navigate to={location.state?.from ?? '/admin'} replace />;
  }

  function handleChange(event) {
    const { name, value } = event.target;
    setForm((prev) => ({ ...prev, [name]: value }));
    setErrors((prev) => ({ ...prev, [name]: undefined }));
    setLoginError('');
  }

  // 제출: 로그인 → role 확인. ADMIN 이 아니면 로그아웃(서버의 refresh token 도 지움)하고 안내
  async function handleSubmit(event) {
    event.preventDefault();
    if (submitting) return;
    const nextErrors = validate(form);
    if (captchaRequired && !captchaToken) nextErrors.captcha = '로봇이 아님을 확인해 주세요.';
    setErrors(nextErrors);
    setLoginError('');
    if (Object.keys(nextErrors).length > 0) return;

    setSubmitting(true);
    try {
      const loggedIn = await login({
        email: form.email.trim(),
        password: form.password,
        recaptchaToken: captchaToken || undefined,
      });
      if (loggedIn.role !== 'ADMIN') {
        await logout();
        setLoginError('관리자 계정이 아닙니다. 일반 회원은 일반 로그인 화면을 이용해 주세요.');
        setForm((prev) => ({ ...prev, password: '' }));
        return;
      }
      navigate(location.state?.from ?? '/admin', { replace: true });
    } catch (error) {
      const { code, message } = error.response?.data?.error ?? {};
      if (code === 'CAPTCHA_REQUIRED' || code === 'CAPTCHA_FAILED') setCaptchaRequired(true);
      if (captchaRequired) setCaptchaResetKey((key) => key + 1);
      setLoginError(message ?? '로그인에 실패했습니다. 잠시 후 다시 시도해 주세요.');
      setForm((prev) => ({ ...prev, password: '' }));
    } finally {
      setSubmitting(false);
    }
  }

  function renderError(name) {
    return errors[name] ? (
      <p className="login-error" id={`admin-login-${name}-error`}>
        {errors[name]}
      </p>
    ) : null;
  }

  return (
    <div className="login-page admin-login-page">
      <div className="login-heading">
        <h1>관리자 로그인</h1>
        <p>관리자 계정으로 로그인하면 관리자 화면으로 이동합니다.</p>
      </div>

      <section className="login-form-card" aria-labelledby="admin-login-title">
        <h2 id="admin-login-title">관리자 계정</h2>
        {member && member.role !== 'ADMIN' ? (
          // 일반 회원으로 로그인된 채 들어온 경우 — 관리자 계정으로 로그인하면 그 계정으로 바뀐다
          <p className="login-subtitle">
            지금 일반 회원({member.nickName})으로 로그인되어 있습니다. 관리자 계정으로 로그인하면 바뀝니다.
          </p>
        ) : (
          <p className="login-subtitle">관리자 권한이 있는 계정만 로그인할 수 있습니다.</p>
        )}

        <form onSubmit={handleSubmit} noValidate>
          <div className="login-field">
            <label htmlFor="admin-login-email">이메일</label>
            <div className="login-input-wrap">
              <input
                id="admin-login-email"
                name="email"
                type="email"
                placeholder="name@example.com"
                autoComplete="username"
                value={form.email}
                onChange={handleChange}
                className={errors.email ? 'has-error' : undefined}
                aria-invalid={Boolean(errors.email)}
              />
              {renderError('email')}
            </div>
          </div>
          <div className="login-field">
            <label htmlFor="admin-login-password">비밀번호</label>
            <div className="login-input-wrap">
              <PasswordInput
                id="admin-login-password"
                name="password"
                placeholder="비밀번호를 입력해 주세요"
                autoComplete="current-password"
                value={form.password}
                onChange={handleChange}
                className={errors.password ? 'has-error' : undefined}
                aria-invalid={Boolean(errors.password)}
              />
              {renderError('password')}
            </div>
          </div>

          {captchaRequired && (
            <>
              <RecaptchaBox onChange={handleCaptchaChange} resetKey={captchaResetKey} />
              {renderError('captcha')}
            </>
          )}

          {loginError && (
            <p className="login-error login-failed" role="alert">
              {loginError}
            </p>
          )}
          <button className="login-submit" type="submit" disabled={submitting}>
            {submitting ? '로그인 중…' : '관리자 로그인'}
          </button>
        </form>

        <p className="login-signup login-card-footer">
          일반 회원이신가요?{' '}
          <Link className="login-text-button" to="/login">
            일반 로그인
          </Link>
        </p>
      </section>
    </div>
  );
}
