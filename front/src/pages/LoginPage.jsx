import { useState } from 'react';
import { Car } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import theme from '../styles/theme';
import './LoginPage.css';

export default function LoginPage() {
  const navigate = useNavigate();
  const [showPassword, setShowPassword] = useState(false);
  const [notice, setNotice] = useState('');

  function handleSubmit(event) {
    event.preventDefault();
    setNotice('로그인 화면 미리보기입니다. 실제 로그인 기능은 아직 연결되지 않았습니다.');
  }

  return (
    <div className="login-page">
      <div className="login-heading">
        <h1>로그인</h1>
        <p>저장한 분석 결과와 구매 계획을 이어서 확인하세요.</p>
      </div>

      <div className="login-grid">
        <section className="login-form-card" aria-labelledby="login-title">
          <h2 id="login-title">다시 만나서 반가워요</h2>
          <p className="login-subtitle">CreditComPass Auto 계정으로 로그인해 주세요.</p>

          <form onSubmit={handleSubmit}>
            <div className="login-field">
              <label htmlFor="login-email">이메일</label>
              <input
                id="login-email"
                name="email"
                type="email"
                placeholder="name@example.com"
                autoComplete="username"
                required
              />
            </div>
            <div className="login-field">
              <label htmlFor="login-password">비밀번호</label>
              <input
                id="login-password"
                name="password"
                type={showPassword ? 'text' : 'password'}
                placeholder="비밀번호를 입력해 주세요"
                autoComplete="current-password"
                required
              />
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
                <input id="remember-email" type="checkbox" />
                이메일 저장
              </label>
              <button
                className="login-text-button"
                type="button"
                onClick={() => setNotice('비밀번호 찾기는 준비 중입니다.')}
              >
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
            <button
              className="login-text-button"
              type="button"
              onClick={() => setNotice('회원가입은 준비 중입니다.')}
            >
              회원가입
            </button>
          </p>
        </section>

        <aside className="login-demo-card" aria-labelledby="demo-title">
          <div className="login-demo-icon" aria-hidden="true">
            <Car size={theme.iconSize.lg} strokeWidth={1.5} />
          </div>
          <span className="login-demo-eyebrow">로그인 없이 먼저 확인</span>
          <h2 id="demo-title">취업 2년 차 예시 프로필로 간편 체험해 보세요.</h2>
          <p>입력 없이 추천 예산, 신용위험 요인, 차량 선택 흐름을 확인할 수 있습니다.</p>
          <div className="login-demo-tags">
            <span>월 소득 280만 원</span>
            <span>신용점수 850점</span>
            <span>현금 1,500만 원</span>
          </div>
          <button
            className="login-demo-button"
            type="button"
            onClick={() => navigate('/#financial')}
          >
            비회원 간편 체험 시작하기
          </button>
          <div className="login-card-footer" aria-hidden="true" />
        </aside>
      </div>

      <aside className="login-privacy">
        <h2>개인정보 보호와 이용</h2>
        <p>분석 결과 저장을 위해 계정 정보로 로그인이 필요합니다. 차량 추천은 비회원으로도 간편하게 체험할 수 있습니다.</p>
      </aside>

      <footer className="login-footer">
        <strong>CreditComPass Auto</strong>
        <p>갖고 싶은 차, 감당 가능한 범위부터 확인하세요.</p>
        <small>본 서비스는 교육·시연용이며 실제 대출·신용 판단이나 금융기관 심사 결과를 의미하지 않습니다.</small>
      </footer>
    </div>
  );
}
