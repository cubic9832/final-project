import { useState } from 'react';
import { Car } from 'lucide-react';
import { Link, useNavigate } from 'react-router-dom';
import theme from '../styles/theme';
import './LoginPage.css';

const EMAIL_PATTERN = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

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
  const [form, setForm] = useState({ email: '', password: '' });
  const [errors, setErrors] = useState({});
  const [showPassword, setShowPassword] = useState(false);
  const [rememberEmail, setRememberEmail] = useState(true);
  // 서버 응답 메시지 자리. API 연결 후 LOGIN_FAILED 등의 오류 문구를 여기에 넣는다
  const [notice, setNotice] = useState('');

  // 입력할 때마다 값을 저장하고, 그 칸의 오류와 안내 문구는 지운다
  function handleChange(event) {
    const { name, value } = event.target;
    setForm((prev) => ({ ...prev, [name]: value }));
    setErrors((prev) => ({ ...prev, [name]: undefined }));
    setNotice('');
  }

  function handleSubmit(event) {
    event.preventDefault();
    const nextErrors = validateLogin(form);
    setErrors(nextErrors);

    if (Object.keys(nextErrors).length > 0) {
      setNotice('');
      return;
    }
    // 백엔드(POST /api/v1/auth/login) 연결 전이라 안내만 표시한다
    setNotice('입력 확인이 끝났습니다. 실제 로그인은 서버 연결 후 동작합니다.');
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
          <p className="login-subtitle">CreditComPass Auto 계정으로 로그인해 주세요.</p>

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
                <input
                  id="login-password"
                  type={showPassword ? 'text' : 'password'}
                  placeholder="8자 이상 입력해 주세요"
                  autoComplete="current-password"
                  {...fieldProps('password')}
                />
                {renderError('password')}
              </div>
            </div>

            <label className="login-checkbox" htmlFor="show-password">
              <input
                id="show-password"
                type="checkbox"
                checked={showPassword}
                onChange={(event) => setShowPassword(event.target.checked)}
              />
              비밀번호 표시
            </label>

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
              {/* 비밀번호 찾기 팝업은 다음 단계에서 연결한다 */}
              <button className="login-text-button" type="button">
                비밀번호 찾기
              </button>
            </div>

            <p className="login-notice" role="status">{notice}</p>
            <button className="login-submit" type="submit">
              로그인
            </button>
          </form>

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
        <strong>CreditComPass Auto</strong>
        <p>첫차 구매 전, 감당 가능한 비용부터 확인하세요.</p>
        <small>본 서비스는 교육·시연용이며 실제 NICE·KCB 신용점수나 금융기관 심사 결과를 의미하지 않습니다.</small>
      </footer>
    </div>
  );
}
