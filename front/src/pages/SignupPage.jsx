import { useState } from 'react';
import { Link } from 'react-router-dom';
import './SignupPage.css';

// 개별 약관. "전체 동의"는 이 목록의 체크 상태로 계산한다
const terms = [
  { id: 'service', label: '서비스 이용약관에 동의합니다.', required: true },
  { id: 'privacy', label: '개인정보 수집·이용에 동의합니다.', required: true },
  { id: 'updates', label: '차량 추천 업데이트 소식을 받습니다.', required: false },
];

const EMAIL_PATTERN = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
const NICKNAME_MAX_LENGTH = 50; // users.nick_name VARCHAR(50)

// 비밀번호 조건. 화면 안내와 제출 검사에서 같은 규칙을 쓴다
function getPasswordRequirements(password) {
  return [
    { label: '8자 이상', met: password.length >= 8 },
    { label: '영문 포함', met: /[a-z]/i.test(password) },
    { label: '숫자 포함', met: /\d/.test(password) },
  ];
}

// 항목 하나의 형식을 검사해 오류 메시지를 돌려준다. 문제가 없으면 빈 문자열
// (제출할 때와 "중복 확인"을 누를 때 같은 규칙을 쓴다)
function validateNickname(value) {
  const nickname = value.trim();
  if (!nickname) return '이름 또는 닉네임을 입력해 주세요.';
  if (nickname.length > NICKNAME_MAX_LENGTH) {
    return `이름 또는 닉네임은 ${NICKNAME_MAX_LENGTH}자 이하로 입력해 주세요.`;
  }
  return '';
}

function validateEmail(value) {
  const email = value.trim();
  if (!email) return '이메일을 입력해 주세요.';
  if (!EMAIL_PATTERN.test(email)) return '이메일 형식이 올바르지 않습니다.';
  return '';
}

// 입력값을 검사해 { 항목 이름: 오류 메시지 } 를 돌려준다. 오류가 없으면 빈 객체
function validateSignup(form, agreements) {
  const errors = {};

  const nicknameError = validateNickname(form.nickname);
  if (nicknameError) errors.nickname = nicknameError;

  const emailError = validateEmail(form.email);
  if (emailError) errors.email = emailError;

  if (!form.password) errors.password = '비밀번호를 입력해 주세요.';
  else if (getPasswordRequirements(form.password).some((requirement) => !requirement.met)) {
    errors.password = '영문과 숫자를 포함해 8자 이상 입력해 주세요.';
  }

  if (terms.some((term) => term.required && !agreements[term.id])) {
    errors.terms = '필수 약관에 모두 동의해 주세요.';
  }

  return errors;
}

const duplicateValidators = { nickname: validateNickname, email: validateEmail };

export default function SignupPage() {
  const [form, setForm] = useState({ nickname: '', email: '', password: '' });
  const [agreements, setAgreements] = useState({ service: false, privacy: false, updates: false });
  const [errors, setErrors] = useState({});
  const [showPassword, setShowPassword] = useState(false);
  const [notice, setNotice] = useState('');
  // "중복 확인" 결과 안내 문구 { nickname, email }. 서버 연결 후 실제 결과로 바꾼다
  const [duplicateNotices, setDuplicateNotices] = useState({});

  const passwordRequirements = getPasswordRequirements(form.password);
  const allAgreed = terms.every((term) => agreements[term.id]);

  // 입력할 때마다 값을 저장하고, 그 칸에 표시 중이던 오류와 안내는 지운다
  function handleChange(event) {
    const { name, value } = event.target;
    setForm((prev) => ({ ...prev, [name]: value }));
    setErrors((prev) => ({ ...prev, [name]: undefined }));
    setDuplicateNotices((prev) => ({ ...prev, [name]: undefined }));
    setNotice('');
  }

  // 중복 확인: 먼저 형식을 검사하고, 통과하면 서버 확인 자리에 안내를 표시한다
  // 서버 연결 후 409 응답이면 errors에 "이미 사용 중인 이름 또는 닉네임입니다." /
  // "이미 가입된 이메일입니다."를 넣는다
  function handleDuplicateCheck(name) {
    const message = duplicateValidators[name](form[name]);
    setErrors((prev) => ({ ...prev, [name]: message || undefined }));
    setDuplicateNotices((prev) => ({
      ...prev,
      [name]: message ? undefined : '형식이 올바릅니다. 중복 여부는 서버 연결 후 확인됩니다.',
    }));
  }

  function handleTermChange(event) {
    const { name, checked } = event.target;
    setAgreements((prev) => ({ ...prev, [name]: checked }));
    setErrors((prev) => ({ ...prev, terms: undefined }));
    setNotice('');
  }

  // 전체 동의: 모든 약관을 한 번에 체크하거나 해제한다
  function handleAllAgree(event) {
    const { checked } = event.target;
    setAgreements(Object.fromEntries(terms.map((term) => [term.id, checked])));
    setErrors((prev) => ({ ...prev, terms: undefined }));
    setNotice('');
  }

  function handleSubmit(event) {
    event.preventDefault();
    const nextErrors = validateSignup(form, agreements);
    setErrors(nextErrors);

    if (Object.keys(nextErrors).length > 0) {
      setNotice('');
      return;
    }
    // 백엔드(POST /api/v1/auth/signup) 연결 전이라 안내만 표시한다
    setNotice('입력 확인이 끝났습니다. 실제 회원가입은 서버 연결 후 동작합니다.');
  }

  // 입력칸에 오류 상태와 오류 문구 연결(aria)을 붙인다
  function fieldProps(name) {
    return {
      name,
      value: form[name],
      onChange: handleChange,
      className: errors[name] ? 'has-error' : undefined,
      'aria-invalid': Boolean(errors[name]),
      'aria-describedby': errors[name] ? `signup-${name}-error` : undefined,
    };
  }

  function renderError(name) {
    if (errors[name]) {
      return (
        <p className="signup-error" id={`signup-${name}-error`}>
          {errors[name]}
        </p>
      );
    }
    return duplicateNotices[name] ? (
      <p className="signup-field-notice" role="status">{duplicateNotices[name]}</p>
    ) : null;
  }

  return (
    <div className="signup-page">
      <header className="signup-heading">
        <h1>회원가입</h1>
        <p>첫차 의사결정을 위한 개인 재무 프로필을 안전하게 시작합니다.</p>
      </header>

      <section className="signup-form-card" aria-labelledby="signup-form-title">
        <h2 id="signup-form-title">기본 정보</h2>
        <p className="signup-subtitle">서비스 이용에 필요한 최소한의 정보만 받습니다.</p>

        <form onSubmit={handleSubmit} noValidate>
          {/* 시안 기준: 라벨은 왼쪽, 입력칸(+중복 확인 버튼)은 오른쪽 */}
          <div className="signup-fields">
            <div className="signup-field">
              <label htmlFor="signup-nickname">이름 또는 닉네임</label>
              <div className="signup-input-wrap">
                <div className="signup-input-row">
                  <input
                    id="signup-nickname"
                    type="text"
                    placeholder="첫차준비생"
                    autoComplete="nickname"
                    {...fieldProps('nickname')}
                  />
                  <button
                    className="signup-check-button"
                    type="button"
                    onClick={() => handleDuplicateCheck('nickname')}
                  >
                    중복 확인
                  </button>
                </div>
                {renderError('nickname')}
              </div>
            </div>

            <div className="signup-field">
              <label htmlFor="signup-email">이메일</label>
              <div className="signup-input-wrap">
                <div className="signup-input-row">
                  <input
                    id="signup-email"
                    type="email"
                    placeholder="user@example.com"
                    autoComplete="email"
                    {...fieldProps('email')}
                  />
                  <button
                    className="signup-check-button"
                    type="button"
                    onClick={() => handleDuplicateCheck('email')}
                  >
                    중복 확인
                  </button>
                </div>
                {renderError('email')}
              </div>
            </div>

            <div className="signup-field">
              <label htmlFor="signup-password">비밀번호</label>
              <div className="signup-input-wrap">
                <input
                  id="signup-password"
                  type={showPassword ? 'text' : 'password'}
                  placeholder="영문·숫자 포함 8자 이상"
                  autoComplete="new-password"
                  {...fieldProps('password')}
                />
                <ul className="signup-password-requirements" aria-label="비밀번호 조건">
                  {passwordRequirements.map((requirement) => (
                    <li className={requirement.met ? 'is-met' : ''} key={requirement.label}>
                      <span aria-hidden="true">{requirement.met ? '✓' : '○'}</span>
                      {requirement.label}
                    </li>
                  ))}
                </ul>
                {renderError('password')}
              </div>
            </div>
          </div>

          <label className="signup-password-toggle" htmlFor="signup-show-password">
            <input
              id="signup-show-password"
              type="checkbox"
              checked={showPassword}
              onChange={(event) => setShowPassword(event.target.checked)}
            />
            비밀번호 표시
          </label>

          <fieldset
            className={errors.terms ? 'signup-terms has-error' : 'signup-terms'}
            aria-describedby={errors.terms ? 'signup-terms-error' : undefined}
          >
            <legend>약관 동의</legend>
            <div className="signup-term signup-term-all">
              <label htmlFor="signup-term-all">
                <input id="signup-term-all" type="checkbox" checked={allAgreed} onChange={handleAllAgree} />
                <span>만 14세 이상이며 모든 약관에 동의합니다.</span>
              </label>
            </div>
            {terms.map((term) => (
              <div className="signup-term" key={term.id}>
                <label htmlFor={`signup-term-${term.id}`}>
                  <input
                    id={`signup-term-${term.id}`}
                    name={term.id}
                    type="checkbox"
                    checked={agreements[term.id]}
                    onChange={handleTermChange}
                  />
                  <span>
                    [{term.required ? '필수' : '선택'}] {term.label}
                  </span>
                </label>
                <span className="signup-term-detail">보기</span>
              </div>
            ))}
          </fieldset>
          {renderError('terms')}

          <p className="signup-notice" role="status">
            {notice}
          </p>
          <button className="signup-submit" type="submit">
            회원가입 완료
          </button>
        </form>

        <p className="signup-login-link">
          이미 계정이 있으신가요? <Link to="/login">로그인</Link>
        </p>
      </section>

      <footer className="signup-footer">
        <strong>CreditComPass Auto</strong>
        <p>첫차 구매 전, 감당 가능한 비용부터 확인하세요.</p>
        <small>본 서비스는 교육·시연용이며 실제 NICE·KCB 신용점수나 금융기관 심사 결과를 의미하지 않습니다.</small>
      </footer>
    </div>
  );
}
