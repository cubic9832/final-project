import { useCallback, useRef, useState } from 'react';
import { Car } from 'lucide-react';
import { Link, useLocation, useNavigate } from 'react-router-dom';
import { googleLogin, login } from '../../features/auth/authApi';
import PasswordInput from '../../features/auth/components/PasswordInput';
import PasswordResetModal from './PasswordResetModal';
import RecaptchaBox from './RecaptchaBox';
import GoogleLoginButton from './GoogleLoginButton';
import TermsModal from '../signup/TermsModal';
import theme from '../../styles/theme';
import './LoginPage.css';

// 구글 가입 동의 [보기] 에 쓰는 약관 (회원가입 화면과 같은 내용)
const GOOGLE_TERMS = {
  service: { id: 'service', title: '서비스 이용약관', required: true },
  privacy: { id: 'privacy', title: '개인정보 수집·이용 동의', required: true },
};

const EMAIL_PATTERN = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
// "이메일 저장"을 체크하고 로그인하면 이메일만 브라우저에 저장한다 (비밀번호 · 토큰은 저장하지 않는다)
const SAVED_EMAIL_KEY = 'savedLoginEmail';

// 저장해 둔 이메일 읽기. 브라우저 저장소를 쓸 수 없는 환경이면 빈 값
function readSavedEmail() {
  try {
    return localStorage.getItem(SAVED_EMAIL_KEY) ?? '';
  } catch {
    return '';
  }
}

function writeSavedEmail(email) {
  try {
    if (email) localStorage.setItem(SAVED_EMAIL_KEY, email);
    else localStorage.removeItem(SAVED_EMAIL_KEY);
  } catch {
    // 저장소를 쓸 수 없어도 로그인은 계속 진행한다
  }
}

// 입력값을 검사해 { 항목 이름: 오류 메시지 } 를 돌려준다. 오류가 없으면 빈 객체
function validateLogin(form) {
  const errors = {};
  const email = form.email.trim();

  if (!email) errors.email = '이메일을 입력해 주세요.';
  else if (!EMAIL_PATTERN.test(email)) errors.email = '이메일 형식이 올바르지 않습니다.';

  if (!form.password) errors.password = '비밀번호를 입력해 주세요.';

  return errors;
}

export default function LoginPage() {
  const navigate = useNavigate();
  const location = useLocation();
  // 저장해 둔 이메일이 있으면 처음부터 채워 둔다
  const [form, setForm] = useState(() => ({ email: readSavedEmail(), password: '' }));
  const [errors, setErrors] = useState({});
  const [rememberEmail, setRememberEmail] = useState(true);
  const [loginError, setLoginError] = useState(''); // 서버가 돌려준 실패 문구 (예: LOGIN_FAILED)
  // 10-22: 구글로 처음 가입할 때의 동의 (만 18세 이상 · 이용약관 / 개인정보 수집·이용). 둘 다 체크해야 가입된다
  const [consent, setConsent] = useState({ terms: false, privacy: false });
  const [consentError, setConsentError] = useState(false);
  const [openTerm, setOpenTerm] = useState(null); // [보기] 로 연 약관
  // 구글 버튼은 처음 그릴 때 받은 함수를 계속 쓰므로, 최신 체크 상태는 ref 에도 같이 넣어 둔다 (updateConsent)
  const consentRef = useRef(consent);
  const [submitting, setSubmitting] = useState(false); // 로그인 요청 중 (버튼 비활성, 중복 요청 방지)
  const [isResetOpen, setIsResetOpen] = useState(false); // 비밀번호 찾기 팝업 열림 여부
  // 보완 6: 서버가 CAPTCHA_REQUIRED 를 돌려주면 reCAPTCHA 체크박스를 보여 준다
  const [captchaRequired, setCaptchaRequired] = useState(false);
  const [captchaToken, setCaptchaToken] = useState(''); // 체크하면 구글이 준 토큰 (한 번만 쓸 수 있다)
  const [captchaResetKey, setCaptchaResetKey] = useState(0); // 값이 바뀌면 체크를 푼다

  // 체크하면 토큰을 저장하고 "확인해 주세요" · 이전 실패 문구를 지운다 (useCallback: RecaptchaBox 가 같은 함수를 계속 받도록)
  const handleCaptchaChange = useCallback((token) => {
    setCaptchaToken(token);
    if (token) {
      setErrors((prev) => ({ ...prev, captcha: undefined }));
      setLoginError(''); // 체크했으니 "로봇이 아님을 확인해 주세요" 같은 이전 실패 문구도 지운다
    }
  }, []);

  // 보완 8: 구글 계정을 고르면 서버에 확인 → 연결된 회원 · 동의한 처음 온 사람이면 로그인 (10-22: 추가 정보 화면 없음)
  const handleGoogleCredential = useCallback(
    async (idToken) => {
      setLoginError('');
      const agreed = consentRef.current.terms && consentRef.current.privacy;
      try {
        await googleLogin(idToken, agreed);
        navigate(location.state?.from ?? '/', { replace: true });
      } catch (error) {
        const { code, message } = error.response?.data?.error ?? {};
        if (code === 'SIGNUP_CONSENT_REQUIRED') setConsentError(true); // 처음 온 사람 → 동의 칸을 빨갛게
        setLoginError(message ?? '구글 로그인에 실패했습니다. 잠시 후 다시 시도해 주세요.');
      }
    },
    [navigate, location.state],
  );

  // 체크 상태를 화면(state)과 구글 버튼용 ref 에 함께 저장한다
  function updateConsent(name, checked) {
    const next = { ...consentRef.current, [name]: checked };
    consentRef.current = next;
    setConsent(next);
    setConsentError(false);
  }

  function handleConsentChange(event) {
    updateConsent(event.target.name, event.target.checked);
  }

  // 입력할 때마다 값을 저장하고, 그 칸의 오류와 실패 문구는 지운다
  function handleChange(event) {
    const { name, value } = event.target;
    setForm((prev) => ({ ...prev, [name]: value }));
    setErrors((prev) => ({ ...prev, [name]: undefined }));
    setLoginError('');
  }

  // 제출: 화면에서 먼저 검사하고, 통과하면 POST /api/v1/auth/login 을 부른다
  async function handleSubmit(event) {
    event.preventDefault();
    if (submitting) return; // 요청 중 중복 제출 방지

    const nextErrors = validateLogin(form);
    // 보완 6: 체크박스가 보이는데 체크하지 않았으면 서버에 보내지 않는다
    if (captchaRequired && !captchaToken) nextErrors.captcha = '로봇이 아님을 확인해 주세요.';
    setErrors(nextErrors);
    setLoginError('');
    if (Object.keys(nextErrors).length > 0) return;

    setSubmitting(true);
    try {
      const email = form.email.trim();
      // 성공하면 토큰 · 회원 정보가 스토어에 저장된다
      await login({ email, password: form.password, recaptchaToken: captchaToken || undefined });
      writeSavedEmail(rememberEmail ? email : '');
      // 로그인이 필요한 화면에서 넘어왔으면 그 화면으로, 아니면 메인으로 이동한다
      navigate(location.state?.from ?? '/', { replace: true });
    } catch (error) {
      // 실패해도 이메일은 그대로 두고 비밀번호만 비운다
      const { code, message } = error.response?.data?.error ?? {};
      // 보완 6: 서버가 로봇 확인을 요구하면 체크박스를 보여 주고, 이미 보이고 있었으면 체크를 풀어 다시 받게 한다
      if (code === 'CAPTCHA_REQUIRED' || code === 'CAPTCHA_FAILED') setCaptchaRequired(true);
      if (captchaRequired) setCaptchaResetKey((key) => key + 1);
      setLoginError(message ?? '로그인에 실패했습니다. 잠시 후 다시 시도해 주세요.');
      setForm((prev) => ({ ...prev, password: '' }));
    } finally {
      setSubmitting(false);
    }
  }

  // 입력칸에 오류 상태와 오류 문구 연결(aria)을 붙인다
  function fieldProps(name) {
    return {
      name,
      value: form[name],
      onChange: handleChange,
      className: errors[name] ? 'has-error' : undefined,
      'aria-invalid': Boolean(errors[name]),
      'aria-describedby': errors[name] ? `login-${name}-error` : undefined,
    };
  }

  function renderError(name) {
    return errors[name] ? (
      <p className="login-error" id={`login-${name}-error`}>
        {errors[name]}
      </p>
    ) : null;
  }

  return (
    <div className="login-page">
      <div className="login-heading">
        <h1>로그인</h1>
        <p>저장한 분석 결과와 구매계획을 이어서 확인하세요.</p>
      </div>

      <div className="login-grid">
        <section className="login-form-card" aria-labelledby="login-title">
          <h2 id="login-title">다시 만나서 반가워요</h2>
          <p className="login-subtitle">CreditCompass 계정으로 로그인해 주세요.</p>

          <form onSubmit={handleSubmit} noValidate>
            <div className="login-field">
              <label htmlFor="login-email">이메일</label>
              <div className="login-input-wrap">
                <input
                  id="login-email"
                  type="email"
                  placeholder="name@example.com"
                  autoComplete="username"
                  {...fieldProps('email')}
                />
                {renderError('email')}
              </div>
            </div>
            <div className="login-field">
              <label htmlFor="login-password">비밀번호</label>
              <div className="login-input-wrap">
                {/* 보완 2: "비밀번호 표시" 체크박스 대신 입력칸 안 눈 아이콘 (회원가입과 같은 PasswordInput) */}
                <PasswordInput
                  id="login-password"
                  placeholder="8자 이상 입력해 주세요"
                  autoComplete="current-password"
                  {...fieldProps('password')}
                />
                {renderError('password')}
              </div>
            </div>

            <div className="login-options">
              <label className="login-checkbox" htmlFor="remember-email">
                <input
                  id="remember-email"
                  type="checkbox"
                  checked={rememberEmail}
                  onChange={(event) => setRememberEmail(event.target.checked)}
                />
                이메일 저장
              </label>
              <button className="login-text-button" type="button" onClick={() => setIsResetOpen(true)}>
                비밀번호 찾기
              </button>
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
              {submitting ? '로그인 중…' : '로그인'}
            </button>
          </form>

          {/* 보완 8: 구글 로그인 */}
          <div className="login-divider">
            <span>또는</span>
          </div>
          <GoogleLoginButton onCredential={handleGoogleCredential} />
          {/* 10-22: 구글로 처음 가입할 때만 필요한 동의. 이미 가입한 회원은 체크하지 않아도 로그인된다 */}
          <fieldset className={consentError ? 'login-google-consent has-error' : 'login-google-consent'}>
            <legend>구글로 처음 가입하는 경우</legend>
            <label>
              <input type="checkbox" name="terms" checked={consent.terms} onChange={handleConsentChange} />
              <span>[필수] 만 18세 이상이며 서비스 이용약관에 동의합니다.</span>
              <button type="button" className="login-text-button" onClick={() => setOpenTerm(GOOGLE_TERMS.service)}>보기</button>
            </label>
            <label>
              <input type="checkbox" name="privacy" checked={consent.privacy} onChange={handleConsentChange} />
              <span>[필수] 개인정보 수집·이용에 동의합니다.</span>
              <button type="button" className="login-text-button" onClick={() => setOpenTerm(GOOGLE_TERMS.privacy)}>보기</button>
            </label>
            <p>닉네임은 구글 이름으로 정해지고, 생년월일 · 성별은 가입 후 마이페이지에서 입력할 수 있습니다.</p>
          </fieldset>

          <p className="login-signup login-card-footer">
            처음이신가요?{' '}
            <Link className="login-text-button" to="/signup">
              회원가입
            </Link>
          </p>
        </section>

        <aside className="login-demo-card" aria-labelledby="demo-title">
          <div className="login-demo-icon" aria-hidden="true">
            <Car size={theme.iconSize.lg} strokeWidth={1.5} />
          </div>
          <span className="login-demo-eyebrow">로그인 없이 먼저 확인</span>
          <h2 id="demo-title">예시 조건으로 간편 체험해 보세요.</h2>
          <p>입력 없이 추천 예산, 신용위험 요인, 차량 6대를 바로 확인할 수 있습니다.</p>
          {/* 체험용 예시 조건 (실제 사용자 정보 아님) */}
          <div className="login-demo-tags">
            <span>월소득 280만 원</span>
            <span>선수금 500만 원</span>
            <span>연 15,000km</span>
          </div>
          <button
            className="login-demo-button"
            type="button"
            onClick={() => navigate('/#financial')}
          >
            간편 체험 시작하기
          </button>
          <div className="login-card-footer" aria-hidden="true" />
        </aside>
      </div>

      <aside className="login-privacy">
        <h2>계정이 필요한 이유</h2>
        <p>분석 결과 저장과 이전 기록 조회는 로그인이 필요합니다. 체험 결과는 브라우저를 닫으면 저장되지 않습니다.</p>
      </aside>

      <footer className="login-footer">
        <strong>CreditCompass</strong>
        <p>첫차 구매 전, 감당 가능한 비용부터 확인하세요.</p>
        <small>본 서비스는 교육·시연용이며 실제 NICE·KCB 신용점수나 금융기관 심사 결과를 의미하지 않습니다.</small>
      </footer>

      {/* 비밀번호 찾기 팝업. 로그인 칸에 적은 이메일을 미리 채워 준다 */}
      {isResetOpen && (
        <PasswordResetModal initialEmail={form.email} onClose={() => setIsResetOpen(false)} />
      )}

      {/* 10-22: 구글 가입 동의 [보기] — [동의하기] 를 누르면 그 항목을 체크한다 */}
      {openTerm && (
        <TermsModal
          term={openTerm}
          agreed={consent[openTerm.id === 'service' ? 'terms' : 'privacy']}
          onAgree={() => {
            updateConsent(openTerm.id === 'service' ? 'terms' : 'privacy', true);
            setOpenTerm(null);
          }}
          onClose={() => setOpenTerm(null)}
        />
      )}
    </div>
  );
}
