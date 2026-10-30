// 보완 8: 구글 첫 로그인 후 가입 마무리 (/signup/google)
// 로그인 화면이 넘겨준 { signupToken, email, name } 으로 시작한다. 이메일 · 비밀번호는 받지 않는다 (구글이 확인)
// 닉네임은 구글 이름으로 자동으로 정하고(가입 후 개인정보 · 계정 관리에서 변경), 여기서는
// 생년월일(만 18세 이상) · 성별 필수, 전화번호 선택, 필수 동의 1개를 받는다 (회원가입과 같은 규칙)
import { useState } from 'react';
import { Link, useLocation, useNavigate } from 'react-router-dom';
import { googleSignup } from '../../features/auth/authApi';
import { showToast } from '../../stores/useToastStore';
import {
  formatPhone,
  GENDER_OPTIONS,
  MIN_SIGNUP_AGE,
  validateBirthDate,
  validateGender,
  validatePhone,
} from './profileRules';
import BirthDateInput from './BirthDateInput';
import TermsModal from './TermsModal';
import './SignupPage.css';

// [보기] 로 여는 약관 — 회원가입 화면과 같은 내용
const TERMS = {
  service: { id: 'service', title: '서비스 이용약관', required: true },
  privacy: { id: 'privacy', title: '개인정보 수집·이용 동의', required: true },
};

export default function GoogleSignupPage() {
  const navigate = useNavigate();
  const pending = useLocation().state; // { signupToken, email, name } — 주소로 바로 들어오면 없다
  const [form, setForm] = useState({ phone: '', birthDate: '', gender: '' });
  const [agreed, setAgreed] = useState(false); // 필수 동의 (만 18세 이상 · 이용약관 · 개인정보 수집·이용)
  const [updatesAgreed, setUpdatesAgreed] = useState(false); // 보완 9: [선택] 차량 추천 업데이트 수신
  const [errors, setErrors] = useState({});
  const [submitting, setSubmitting] = useState(false);
  const [serverError, setServerError] = useState('');
  const [openTerm, setOpenTerm] = useState(null); // [보기] 로 연 약관

  if (!pending?.signupToken) {
    return (
      <div className="signup-page">
        <section className="signup-form-card">
          <h2>구글로 가입하기</h2>
          <p className="signup-subtitle">로그인 화면에서 [Google 계정으로 계속하기]를 먼저 눌러 주세요.</p>
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
    setServerError('');
  }

  function updateAgreed(checked) {
    setAgreed(checked);
    setErrors((prev) => ({ ...prev, terms: undefined }));
  }

  // [가입 완료] → POST /auth/google/signup. 가입과 동시에 로그인된다 (authApi 가 로그인 정보를 저장)
  async function handleSubmit(event) {
    event.preventDefault();
    if (submitting) return;
    const nextErrors = {};
    const birthError = validateBirthDate(form.birthDate);
    if (birthError) nextErrors.birthDate = birthError;
    const genderError = validateGender(form.gender);
    if (genderError) nextErrors.gender = genderError;
    const phoneError = validatePhone(form.phone, { required: true });
    if (phoneError) nextErrors.phone = phoneError;
    if (!agreed) nextErrors.terms = '필수 동의 항목에 체크해 주세요.';
    setErrors(nextErrors);
    setServerError('');
    if (Object.keys(nextErrors).length > 0) return;

    setSubmitting(true);
    try {
      const member = await googleSignup({
        signupToken: pending.signupToken,
        phone: form.phone,
        birthDate: form.birthDate,
        gender: form.gender,
        consent: agreed,
        updatesAgreed,
      });
      // 새로 가입했으면 첫 차 취향 테스트로 (조원 취향 테스트 흐름), 자동으로 정한 닉네임은 토스트로 알린다
      navigate('/taste-test', { replace: true });
      showToast(`가입되었습니다. 닉네임은 '${member.nickName}'(으)로 정해졌어요. 마이페이지 > 개인정보 · 계정 관리에서 바꿀 수 있습니다.`);
    } catch (error) {
      const { code, message } = error.response?.data?.error ?? {};
      if (code === 'AGE_RESTRICTED') {
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
        <p className="signup-subtitle">
          구글 계정 {pending.email} 으로 가입합니다. 비밀번호는 만들지 않고, 닉네임은 구글 이름으로 정해집니다.
        </p>

        <form onSubmit={handleSubmit} noValidate>
          <div className="signup-fields">
            <div className="signup-field">
              <label htmlFor="google-birth-date">생년월일<span className="form-required" aria-hidden="true"> *</span></label>
              <div className="signup-input-wrap">
                <BirthDateInput
                  id="google-birth-date"
                  name="birthDate"
                  value={form.birthDate}
                  onChange={handleChange}
                  className={errors.birthDate ? 'has-error' : undefined}
                />
                {renderError('birthDate')}
              </div>
            </div>

            <div className="signup-field">
              <span className="signup-field-label" id="google-gender-label">
                성별<span className="form-required" aria-hidden="true"> *</span>
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

            <div className="signup-field">
              <label htmlFor="google-phone">
                전화번호<span className="form-required" aria-hidden="true"> *</span>
              </label>
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

            <p className="signup-privacy-note">
              생년월일 · 성별은 연령대별 차량 추천과 통계에 사용합니다. 전화번호는 서비스 관련 연락에만 사용합니다.
              <br />
              차량 추천 서비스라 운전면허를 딸 수 있는 <strong>만 {MIN_SIGNUP_AGE}세 이상</strong>부터 가입할 수
              있습니다.
            </p>
          </div>

          {/* 필수 동의 1개: 만 18세 이상 · 이용약관 · 개인정보 수집·이용 ([보기] 에서 [동의하기] 를 눌러도 체크된다) */}
          <fieldset className={errors.terms ? 'signup-terms has-error' : 'signup-terms'}>
            <legend>약관 동의</legend>
            <div className="signup-term signup-term-all">
              <label htmlFor="google-terms">
                <input
                  id="google-terms"
                  type="checkbox"
                  checked={agreed}
                  onChange={(event) => updateAgreed(event.target.checked)}
                />
                <span>만 {MIN_SIGNUP_AGE}세 이상이며 서비스 이용약관 · 개인정보 수집·이용에 동의합니다. (필수)</span>
              </label>
              <span className="signup-term-links">
                <button className="signup-term-detail" type="button" onClick={() => setOpenTerm(TERMS.service)}>
                  이용약관 보기
                </button>
                <button className="signup-term-detail" type="button" onClick={() => setOpenTerm(TERMS.privacy)}>
                  개인정보 보기
                </button>
              </span>
            </div>
            {/* 보완 9: [선택] 회원가입 화면과 같은 항목. 체크하면 이메일 알림 "모든 알림", 안 하면 "중요 계획 알림만" */}
            <div className="signup-term">
              <label htmlFor="google-updates">
                <input
                  id="google-updates"
                  type="checkbox"
                  checked={updatesAgreed}
                  onChange={(event) => setUpdatesAgreed(event.target.checked)}
                />
                <span>[선택] 차량 추천 업데이트 소식을 받습니다.</span>
              </label>
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

      {openTerm && (
        <TermsModal
          term={openTerm}
          agreed={agreed}
          onAgree={() => {
            updateAgreed(true);
            setOpenTerm(null);
          }}
          onClose={() => setOpenTerm(null)}
        />
      )}
    </div>
  );
}
