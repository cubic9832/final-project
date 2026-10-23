// 보완 8: 구글 첫 로그인 후 추가 정보 입력 (/signup/google)
// 로그인 화면이 넘겨준 { signupToken, email, name } 으로 시작한다. 이메일 · 비밀번호는 받지 않는다 (구글이 확인)
// 회원가입과 같은 규칙: 닉네임 2~12자 + 중복 확인, 전화번호 · 생년월일(만 18세 이상) · 성별 필수 (보완 5)
import { useState } from 'react';
import { Link, useLocation, useNavigate } from 'react-router-dom';
import { checkNickName, googleSignup } from '../../features/auth/authApi';
import { checkNickNameWords } from '../../features/auth/nickNamePolicy';
import { showToast } from '../../stores/useToastStore';
import {
  formatPhone,
  GENDER_OPTIONS,
  MIN_SIGNUP_AGE,
  todayString,
  validateBirthDate,
  validateGender,
  validatePhone,
} from './profileRules';
import TermsModal from './TermsModal';
import './SignupPage.css';

// 보완 5 추가(10-20): 개인정보 수집·이용 [보기] — 회원가입과 같은 내용
const PRIVACY_TERM = { id: 'privacy', title: '개인정보 수집·이용 동의', required: true };

const NICKNAME_MIN_LENGTH = 2;
const NICKNAME_MAX_LENGTH = 12;

function validateNickname(value) {
  const nickname = value.trim();
  if (!nickname) return '이름 또는 닉네임을 입력해 주세요.';
  if (nickname.length < NICKNAME_MIN_LENGTH || nickname.length > NICKNAME_MAX_LENGTH) {
    return `이름 또는 닉네임은 ${NICKNAME_MIN_LENGTH}~${NICKNAME_MAX_LENGTH}자로 입력해 주세요.`;
  }
  return checkNickNameWords(nickname); // 보완 3 추가: 금지어 (서버와 같은 목록)
}

export default function GoogleSignupPage() {
  const navigate = useNavigate();
  const pending = useLocation().state; // { signupToken, email, name } — 주소로 바로 들어오면 없다
  // 구글 이름을 닉네임 기본값으로 (12자 넘으면 잘라서) — 규칙에 맞는지는 중복 확인에서 다시 본다
  const [form, setForm] = useState(() => ({
    nickname: (pending?.name ?? '').slice(0, NICKNAME_MAX_LENGTH),
    phone: '',
    birthDate: '',
    gender: '',
  }));
  const [agreed, setAgreed] = useState(false); // 필수 약관 (서비스 이용약관 · 개인정보 수집·이용)
  const [errors, setErrors] = useState({});
  const [checkedNickname, setCheckedNickname] = useState(''); // 중복 확인을 통과한 닉네임
  const [nicknameNotice, setNicknameNotice] = useState('');
  const [checking, setChecking] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [serverError, setServerError] = useState('');
  const [isPrivacyOpen, setIsPrivacyOpen] = useState(false); // 개인정보 [보기] 팝업

  if (!pending?.signupToken) {
    return (
      <div className="signup-page">
        <section className="signup-form-card">
          <h2>구글로 가입하기</h2>
          <p className="signup-subtitle">로그인 화면에서 [Google 로 계속하기]를 먼저 눌러 주세요.</p>
          <p className="signup-login-link">
            <Link to="/login">로그인 화면으로</Link>
          </p>
        </section>
      </div>
    );
  }

  function handleChange(event) {
    const { name } = event.target;
    const value = name === 'phone' ? formatPhone(event.target.value) : event.target.value;
    setForm((prev) => ({ ...prev, [name]: value }));
    setErrors((prev) => ({ ...prev, [name]: undefined }));
    if (name === 'nickname') {
      setCheckedNickname('');
      setNicknameNotice('');
    }
    setServerError('');
  }

  async function handleNicknameCheck() {
    const message = validateNickname(form.nickname);
    setNicknameNotice('');
    if (message) {
      setErrors((prev) => ({ ...prev, nickname: message }));
      return;
    }
    setChecking(true);
    try {
      const value = form.nickname.trim();
      if (await checkNickName(value)) {
        setCheckedNickname(value);
        setNicknameNotice('사용할 수 있는 닉네임입니다.');
      } else {
        setErrors((prev) => ({ ...prev, nickname: '이미 사용 중인 닉네임입니다.' }));
      }
    } catch (error) {
      setErrors((prev) => ({ ...prev, nickname: error.response?.data?.error?.message ?? '중복 확인에 실패했습니다.' }));
    } finally {
      setChecking(false);
    }
  }

  async function handleSubmit(event) {
    event.preventDefault();
    if (submitting) return;
    const nextErrors = {};
    const nicknameError = validateNickname(form.nickname);
    if (nicknameError) nextErrors.nickname = nicknameError;
    else if (checkedNickname !== form.nickname.trim()) nextErrors.nickname = '닉네임 [중복 확인]을 눌러 주세요.';
    const phoneError = validatePhone(form.phone);
    if (phoneError) nextErrors.phone = phoneError;
    const birthError = validateBirthDate(form.birthDate);
    if (birthError) nextErrors.birthDate = birthError;
    const genderError = validateGender(form.gender);
    if (genderError) nextErrors.gender = genderError;
    if (!agreed) nextErrors.terms = '필수 약관에 동의해 주세요.';
    setErrors(nextErrors);
    setServerError('');
    if (Object.keys(nextErrors).length > 0) return;

    setSubmitting(true);
    try {
      // 가입과 동시에 로그인된다 (authApi 가 로그인 정보를 저장)
      await googleSignup({
        signupToken: pending.signupToken,
        nickName: form.nickname.trim(),
        phone: form.phone,
        birthDate: form.birthDate,
        gender: form.gender,
      });
      navigate('/taste-test', { replace: true });
      showToast('구글 계정으로 가입되었습니다.');
    } catch (error) {
      const { code, message } = error.response?.data?.error ?? {};
      if (code === 'NICKNAME_DUPLICATED') {
        setErrors((prev) => ({ ...prev, nickname: message }));
        setCheckedNickname('');
      } else if (code === 'AGE_RESTRICTED') {
        setErrors((prev) => ({ ...prev, birthDate: message }));
      } else {
        setServerError(message ?? '가입에 실패했습니다. 잠시 후 다시 시도해 주세요.'); // 시간 초과(10분) 등
      }
    } finally {
      setSubmitting(false);
    }
  }

  function renderError(name) {
    return errors[name] ? (
      <p className="signup-error" id={`google-${name}-error`}>
        {errors[name]}
      </p>
    ) : null;
  }

  return (
    <div className="signup-page">
      <header className="signup-heading">
        <h1>구글로 가입하기</h1>
        <p>처음 오셨네요. 가입을 마치려면 아래 정보를 입력해 주세요.</p>
      </header>

      <section className="signup-form-card" aria-labelledby="google-signup-title">
        <h2 id="google-signup-title">추가 정보</h2>
        <p className="signup-subtitle">구글 계정 {pending.email} 으로 가입합니다. 비밀번호는 만들지 않습니다.</p>

        <form onSubmit={handleSubmit} noValidate>
          <div className="signup-fields">
            <div className="signup-field">
              <label htmlFor="google-nickname">이름 또는 닉네임</label>
              <div className="signup-input-wrap">
                <div className="signup-input-row">
                  <input
                    id="google-nickname"
                    name="nickname"
                    type="text"
                    maxLength={NICKNAME_MAX_LENGTH}
                    value={form.nickname}
                    onChange={handleChange}
                    className={errors.nickname ? 'has-error' : undefined}
                  />
                  <button
                    className="signup-check-button"
                    type="button"
                    onClick={handleNicknameCheck}
                    disabled={checking}
                  >
                    {checking ? '확인 중…' : '중복 확인'}
                  </button>
                </div>
                {renderError('nickname') ?? (nicknameNotice && <p className="signup-field-notice">{nicknameNotice}</p>)}
              </div>
            </div>

            <div className="signup-field">
              <label htmlFor="google-phone">전화번호</label>
              <div className="signup-input-wrap">
                <input
                  id="google-phone"
                  name="phone"
                  type="tel"
                  inputMode="numeric"
                  placeholder="010-1234-5678"
                  maxLength={13}
                  value={form.phone}
                  onChange={handleChange}
                  className={errors.phone ? 'has-error' : undefined}
                />
                {renderError('phone')}
              </div>
            </div>

            <div className="signup-field">
              <label htmlFor="google-birth-date">생년월일</label>
              <div className="signup-input-wrap">
                <input
                  id="google-birth-date"
                  name="birthDate"
                  type="date"
                  min="1900-01-01"
                  max={todayString()}
                  value={form.birthDate}
                  onChange={handleChange}
                  className={errors.birthDate ? 'has-error' : undefined}
                />
                {renderError('birthDate')}
              </div>
            </div>

            <div className="signup-field">
              <span className="signup-field-label" id="google-gender-label">
                성별
              </span>
              <div className="signup-input-wrap">
                <div
                  className={errors.gender ? 'signup-gender has-error' : 'signup-gender'}
                  role="radiogroup"
                  aria-labelledby="google-gender-label"
                >
                  {GENDER_OPTIONS.map((option) => (
                    <label key={option.value}>
                      <input
                        type="radio"
                        name="gender"
                        value={option.value}
                        checked={form.gender === option.value}
                        onChange={handleChange}
                      />
                      <span>{option.label}</span>
                    </label>
                  ))}
                </div>
                {renderError('gender')}
              </div>
            </div>

            <p className="signup-privacy-note">
              생년월일 · 성별은 연령대별 차량 추천과 통계에 사용합니다. 전화번호는 연락용이며 인증에는 쓰지 않습니다.
              <br />
              차량 추천 서비스라 운전면허를 딸 수 있는 <strong>만 {MIN_SIGNUP_AGE}세 이상</strong>부터 가입할 수
              있습니다.
            </p>
          </div>

          <fieldset className={errors.terms ? 'signup-terms has-error' : 'signup-terms'}>
            <legend>약관 동의</legend>
            <div className="signup-term signup-term-all">
              <label htmlFor="google-terms">
                <input
                  id="google-terms"
                  type="checkbox"
                  checked={agreed}
                  onChange={(event) => {
                    setAgreed(event.target.checked);
                    setErrors((prev) => ({ ...prev, terms: undefined }));
                  }}
                />
                <span>만 {MIN_SIGNUP_AGE}세 이상이며 서비스 이용약관 · 개인정보 수집·이용에 동의합니다. (필수)</span>
              </label>
              <button
                className="signup-term-detail"
                type="button"
                aria-label="개인정보 수집·이용 동의 보기"
                onClick={() => setIsPrivacyOpen(true)}
              >
                보기
              </button>
            </div>
          </fieldset>
          {renderError('terms')}

          {serverError && (
            <p className="signup-error" role="alert">
              {serverError} <Link to="/login">로그인 화면으로</Link>
            </p>
          )}
          <button className="signup-submit" type="submit" disabled={submitting}>
            {submitting ? '가입 중…' : '가입 완료'}
          </button>
        </form>
      </section>

      {isPrivacyOpen && (
        <TermsModal
          term={PRIVACY_TERM}
          agreed={agreed}
          onAgree={() => {
            setAgreed(true);
            setErrors((prev) => ({ ...prev, terms: undefined }));
            setIsPrivacyOpen(false);
          }}
          onClose={() => setIsPrivacyOpen(false)}
        />
      )}
    </div>
  );
}
