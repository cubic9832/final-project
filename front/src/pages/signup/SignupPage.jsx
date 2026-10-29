import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { checkNickName, confirmEmailCode, sendEmailCode, signup } from '../../features/auth/authApi';
import { checkNickNameWords } from '../../features/auth/nickNamePolicy';
import { clearProof, getProof, saveProof } from '../../features/auth/verificationProof';
import { suggestEmail } from './emailTypo';
import PasswordInput from '../../features/auth/components/PasswordInput';
import { getPasswordRules, PASSWORD_MAX, validatePassword } from '../../features/auth/passwordPolicy';
import {
  formatPhone,
  GENDER_OPTIONS,
  MIN_SIGNUP_AGE,
  validateBirthDate,
  validateGender,
  validatePhone,
} from './profileRules';
import BirthDateInput from './BirthDateInput';
import SignupCompleteModal from './SignupCompleteModal';
import TermsModal from './TermsModal';
import './SignupPage.css';

// 개별 약관. "전체 동의"는 이 목록의 체크 상태로 계산한다
// title 은 "보기" 팝업 제목에 쓴다
const terms = [
  { id: 'service', title: '서비스 이용약관', label: '서비스 이용약관에 동의합니다.', required: true },
  { id: 'privacy', title: '개인정보 수집·이용 동의', label: '개인정보 수집·이용에 동의합니다.', required: true },
  { id: 'updates', title: '차량 추천 업데이트 수신', label: '차량 추천 업데이트 소식을 받습니다.', required: false },
];

const EMAIL_PATTERN = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
// 글자 수 제한 (보완 2 · 보완 목록 ⑤). 서버 SignupRequest 와 같은 값
const EMAIL_MAX_LENGTH = 100;
const NICKNAME_MIN_LENGTH = 2;
const NICKNAME_MAX_LENGTH = 12;

// 항목 하나의 형식을 검사해 오류 메시지를 돌려준다. 문제가 없으면 빈 문자열
// (제출할 때와 "중복 확인"을 누를 때 같은 규칙을 쓴다)
function validateNickname(value) {
  const nickname = value.trim();
  if (!nickname) return '이름 또는 닉네임을 입력해 주세요.';
  if (nickname.length < NICKNAME_MIN_LENGTH || nickname.length > NICKNAME_MAX_LENGTH) {
    return `이름 또는 닉네임은 ${NICKNAME_MIN_LENGTH}~${NICKNAME_MAX_LENGTH}자로 입력해 주세요.`;
  }
  return checkNickNameWords(nickname); // 보완 3 추가: 금지어 (서버와 같은 목록)
}

function validateEmail(value) {
  const email = value.trim();
  if (!email) return '이메일을 입력해 주세요.';
  if (email.length > EMAIL_MAX_LENGTH) return `이메일은 ${EMAIL_MAX_LENGTH}자 이하로 입력해 주세요.`;
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

  // 비밀번호 규칙 (보완 2 · 보완 목록 ⑥) — 서버 PasswordPolicy 와 같은 규칙
  const passwordError = validatePassword(form.password, form.email);
  if (passwordError) errors.password = passwordError;

  // 비밀번호 확인 (보완 2 · 보완 목록 ④)
  if (!form.passwordConfirm) errors.passwordConfirm = '비밀번호를 한 번 더 입력해 주세요.';
  else if (form.passwordConfirm !== form.password) errors.passwordConfirm = '비밀번호가 일치하지 않습니다.';

  // 개인 정보 (보완 5) — 생년월일은 만 18세 이상인지도 확인한다
  const phoneError = validatePhone(form.phone, { required: true });
  if (phoneError) errors.phone = phoneError;
  const birthDateError = validateBirthDate(form.birthDate);
  if (birthDateError) errors.birthDate = birthDateError;
  const genderError = validateGender(form.gender);
  if (genderError) errors.gender = genderError;

  if (terms.some((term) => term.required && !agreements[term.id])) {
    errors.terms = '필수 약관에 모두 동의해 주세요.';
  }

  return errors;
}


export default function SignupPage() {
  const [form, setForm] = useState({
    nickname: '',
    email: '',
    password: '',
    passwordConfirm: '',
    phone: '', // 보완 5: 010-1234-5678 모양으로 저장 (입력할 때 하이픈 자동)
    birthDate: '', // 보완 5: 'YYYY-MM-DD'
    gender: '', // 보완 5: MALE · FEMALE · NONE
  });
  const [agreements, setAgreements] = useState({ service: false, privacy: false, updates: false });
  const [errors, setErrors] = useState({});
  const [notice, setNotice] = useState('');
  // "중복 확인" 결과 안내 문구 { nickname, email } (예: "사용할 수 있는 이메일입니다.")
  const [duplicateNotices, setDuplicateNotices] = useState({});
  // 보완 3: 중복 확인을 통과한 값 { nickname, email }. 입력을 바꾸면 비워져서 다시 확인해야 한다
  // 보완 7: email 은 "인증 코드 확인까지 마친 이메일" (중복 확인은 [인증 코드 받기] 에 포함)
  const [checked, setChecked] = useState({ nickname: '', email: '' });
  const [checking, setChecking] = useState(''); // 지금 요청 중인 항목 ('nickname' | 'email' | 'emailCode' | '')
  // 보완 7: 코드를 보낸 상태 { email, expiresAt, resendAt, mailEnabled } (시각은 ms). 안 보냈으면 null
  const [verification, setVerification] = useState(null);
  const [emailCode, setEmailCode] = useState(''); // 입력한 인증 코드 (숫자 6자리)
  const [now, setNow] = useState(() => Date.now()); // 남은 시간 표시용 현재 시각 (1초마다 갱신)
  const [viewingTerm, setViewingTerm] = useState(null); // "보기"로 연 약관 (없으면 null)
  const [isCompleteOpen, setIsCompleteOpen] = useState(false); // 회원가입 완료 팝업 열림 여부
  const [submitting, setSubmitting] = useState(false); // 가입 요청 중 (버튼 비활성, 중복 요청 방지)
  const [serverError, setServerError] = useState(''); // 특정 칸에 붙일 수 없는 서버 오류 문구
  const [joinedEmail, setJoinedEmail] = useState(''); // 가입된 이메일 (서버가 정리한 값, 완료 팝업에 표시)

  // 보완 7: 지금 입력한 이메일로 인증을 마쳤는지, 코드 남은 시간 · 다시 받기까지 남은 시간(초)
  const emailVerified = checked.email !== '' && checked.email === form.email.trim();
  const codeLeft = verification ? Math.max(0, Math.ceil((verification.expiresAt - now) / 1000)) : 0;
  const resendWait = verification ? Math.max(0, Math.ceil((verification.resendAt - now) / 1000)) : 0;

  const passwordRules = getPasswordRules(form.password, form.email);
  const emailSuggestion = suggestEmail(form.email); // 오타로 보이면 고친 이메일 (보완 목록 ⑨)
  const allAgreed = terms.every((term) => agreements[term.id]);

  // 입력할 때마다 값을 저장하고, 그 칸에 표시 중이던 오류와 안내는 지운다
  // (비밀번호를 바꾸면 비밀번호 확인 오류도 다시 판단해야 하므로 함께 지운다)
  function handleChange(event) {
    const { name } = event.target;
    // 전화번호는 숫자만 받아 하이픈을 자동으로 넣는다 (보완 5)
    const value = name === 'phone' ? formatPhone(event.target.value) : event.target.value;
    setForm((prev) => ({ ...prev, [name]: value }));
    setErrors((prev) => ({
      ...prev,
      [name]: undefined,
      ...(name === 'password' ? { passwordConfirm: undefined } : {}),
    }));
    setDuplicateNotices((prev) => ({ ...prev, [name]: undefined }));
    if (name in checked) setChecked((prev) => ({ ...prev, [name]: '' })); // 값이 바뀌면 중복 확인 다시
    if (name === 'email') {
      // 보완 7: 이메일을 바꾸면 보낸 코드 · 인증 결과는 무효 → 다시 받아야 한다
      setVerification(null);
      setEmailCode('');
      setErrors((prev) => ({ ...prev, emailCode: undefined }));
    }
    setNotice('');
    setServerError('');
  }

  // 보완 7: 코드를 보낸 동안 1초마다 현재 시각을 바꿔 남은 시간 · 다시 받기 대기 시간을 다시 그린다
  useEffect(() => {
    if (!verification) return undefined;
    const timer = setInterval(() => setNow(Date.now()), 1000);
    return () => clearInterval(timer);
  }, [verification]);

  // 보완 7: [인증 코드 받기] — 형식 확인 → 서버가 중복 확인 후 메일 발송
  // POST /api/v1/auth/email-verification → { expiresInSeconds, resendAfterSeconds, mailEnabled }
  async function handleSendCode() {
    const message = validateEmail(form.email);
    setDuplicateNotices((prev) => ({ ...prev, email: undefined }));
    if (message) {
      setErrors((prev) => ({ ...prev, email: message }));
      return;
    }
    const email = form.email.trim();
    // 보완 7 추가: 이 탭에서 30분 안에 인증한 이메일(예: 인증 후 새로고침) → 다시 보내지 않고 바로 인증 완료
    // (10-22: 서버가 "이미 인증됨"을 알려 주지 않고, 인증한 사람 탭에 보관한 일회용 증명 번호로 판단)
    if (getProof(email)) {
      setChecked((prev) => ({ ...prev, email }));
      setVerification(null);
      setErrors((prev) => ({ ...prev, email: undefined, emailCode: undefined }));
      setDuplicateNotices((prev) => ({ ...prev, email: '이미 인증된 이메일입니다.' }));
      return;
    }
    // 같은 이메일로 이미 코드를 보냈으면 [다시 받기] — 새 코드가 나가면 이전 코드는 쓸 수 없다
    const isResend = verification?.email === email;
    setChecking('email');
    try {
      const result = await sendEmailCode(email);
      const sentAt = Date.now();
      setVerification({
        email,
        expiresAt: sentAt + result.expiresInSeconds * 1000,
        resendAt: sentAt + result.resendAfterSeconds * 1000,
        mailEnabled: result.mailEnabled,
      });
      setNow(sentAt);
      setEmailCode('');
      setErrors((prev) => ({ ...prev, email: undefined, emailCode: undefined }));
      setDuplicateNotices((prev) => ({
        ...prev,
        email: result.mailEnabled
          // 10-26: 코드 유효 시간(5분)과 다시 받기 대기(1분)가 헷갈리지 않게 둘 다 글로 알린다
          ? `${isResend ? '새 인증 코드를 보냈습니다. 이전 코드는 쓸 수 없으니 가장 최근 메일의 코드를 넣어 주세요. ' : '인증 코드를 보냈습니다. '}코드는 ${result.expiresInSeconds / 60}분 동안 쓸 수 있어요. 메일이 안 보이면 스팸함을 확인하고, ${result.resendAfterSeconds / 60}분 뒤 [다시 받기]를 눌러 주세요.`
          : '개발 모드: 메일 대신 서버 로그에 인증 코드가 표시됩니다.',
      }));
    } catch (error) {
      // 이미 가입된 이메일(409), 너무 자주 요청(429), 메일 발송 실패(503) 등
      setErrors((prev) => ({
        ...prev,
        email: error.response?.data?.error?.message ?? '인증 코드를 보내지 못했습니다. 잠시 후 다시 시도해 주세요.',
      }));
    } finally {
      setChecking('');
    }
  }

  // 보완 7: 인증 코드 [확인] — POST /api/v1/auth/email-verification/confirm
  async function handleConfirmCode() {
    if (!/^\d{6}$/.test(emailCode)) {
      setErrors((prev) => ({ ...prev, emailCode: '인증 코드 6자리를 입력해 주세요.' }));
      return;
    }
    setChecking('emailCode');
    try {
      const token = await confirmEmailCode(verification.email, emailCode);
      saveProof(verification.email, token); // 가입할 때 같이 보낼 일회용 증명 번호
      setChecked((prev) => ({ ...prev, email: verification.email }));
      setVerification(null);
      setErrors((prev) => ({ ...prev, email: undefined, emailCode: undefined }));
      setDuplicateNotices((prev) => ({ ...prev, email: '이메일 인증이 완료되었습니다.' }));
    } catch (error) {
      // 틀림(남은 횟수 안내) · 만료 · 5번 틀림
      setErrors((prev) => ({
        ...prev,
        emailCode: error.response?.data?.error?.message ?? '인증에 실패했습니다. 잠시 후 다시 시도해 주세요.',
      }));
    } finally {
      setChecking('');
    }
  }

  // 남은 초 → "4:59"
  function formatSeconds(seconds) {
    return `${Math.floor(seconds / 60)}:${String(seconds % 60).padStart(2, '0')}`;
  }

  // 보완 3: 닉네임 중복 확인 — 형식을 먼저 검사하고, 통과하면 서버에 사용 가능 여부를 묻는다
  // GET /api/v1/auth/check-nickname → { available }  (이메일은 보완 7 부터 [인증 코드 받기] 가 대신한다)
  async function handleDuplicateCheck(name) {
    const message = validateNickname(form[name]);
    setDuplicateNotices((prev) => ({ ...prev, [name]: undefined }));
    if (message) {
      setErrors((prev) => ({ ...prev, [name]: message }));
      return;
    }

    const value = form[name].trim();
    setChecking(name);
    try {
      const available = await checkNickName(value);
      if (available) {
        setErrors((prev) => ({ ...prev, [name]: undefined }));
        setDuplicateNotices((prev) => ({ ...prev, [name]: '사용할 수 있는 닉네임입니다.' }));
        setChecked((prev) => ({ ...prev, [name]: value }));
      } else {
        setErrors((prev) => ({
          ...prev,
          [name]: '이미 사용 중인 닉네임입니다.',
        }));
      }
    } catch (error) {
      setErrors((prev) => ({
        ...prev,
        [name]: error.response?.data?.error?.message ?? '중복 확인에 실패했습니다. 잠시 후 다시 시도해 주세요.',
      }));
    } finally {
      setChecking('');
    }
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

  // 제출: 화면에서 먼저 검사하고, 통과하면 POST /api/v1/auth/signup 을 부른다
  async function handleSubmit(event) {
    event.preventDefault();
    if (submitting) return; // 요청 중 중복 제출 방지

    const nextErrors = validateSignup(form, agreements);
    // 보완 3: 형식이 맞는데 중복 확인을 안 했으면(또는 확인 후 값을 바꿨으면) 확인하라고 안내
    if (!nextErrors.nickname && checked.nickname !== form.nickname.trim()) {
      nextErrors.nickname = '닉네임 [중복 확인]을 눌러 주세요.';
    }
    if (!nextErrors.email && checked.email !== form.email.trim()) {
      nextErrors.email = '이메일 인증을 완료해 주세요.'; // 보완 7
    }
    setErrors(nextErrors);
    setNotice('');
    setServerError('');
    if (Object.keys(nextErrors).length > 0) return;

    setSubmitting(true);
    try {
      // 보완 9: 약관 동의도 같이 보내 동의 시각을 DB(user_agreements)에 남긴다 (필수 2개는 서버도 확인)
      const member = await signup({
        email: form.email.trim(),
        password: form.password,
        nickName: form.nickname.trim(),
        phone: form.phone,
        birthDate: form.birthDate,
        gender: form.gender,
        verificationToken: getProof(form.email.trim()), // 보완 7 추가: 인증한 사람만 가진 번호
        termsAgreed: agreements.service,
        privacyAgreed: agreements.privacy,
        updatesAgreed: agreements.updates,
      });
      clearProof(member.email); // 한 번 쓰면 끝 (서버에서도 지움)
      setJoinedEmail(member.email);
      setIsCompleteOpen(true);
    } catch (error) {
      // 서버 실패 봉투: { error: { code, message } }. 실패해도 입력값은 그대로 둔다
      const { code, message } = error.response?.data?.error ?? {};
      // 확인과 가입 사이에 다른 사람이 먼저 가입한 경우 — 해당 칸에 표시하고 다시 확인하게 한다
      if (code === 'EMAIL_DUPLICATED' || code === 'EMAIL_NOT_VERIFIED') {
        clearProof(form.email.trim()); // 서버가 거절한 번호는 버리고 다시 인증
        setErrors((prev) => ({ ...prev, email: message }));
        setChecked((prev) => ({ ...prev, email: '' }));
      } else if (code === 'NICKNAME_DUPLICATED') {
        setErrors((prev) => ({ ...prev, nickname: message }));
        setChecked((prev) => ({ ...prev, nickname: '' }));
      } else if (code === 'AGE_RESTRICTED') {
        setErrors((prev) => ({ ...prev, birthDate: message })); // 보완 5: 만 18세 미만
      } else if (code === 'PASSWORD_POLICY') {
        setErrors((prev) => ({ ...prev, password: message })); // 서버 비밀번호 규칙 위반
      } else {
        setServerError(message ?? '회원가입에 실패했습니다. 잠시 후 다시 시도해 주세요.');
      }
    } finally {
      setSubmitting(false);
    }
  }

  // 약관 팝업에서 "동의하고 닫기": 해당 약관을 체크하고 팝업을 닫는다
  function handleAgreeTerm() {
    setAgreements((prev) => ({ ...prev, [viewingTerm.id]: true }));
    setErrors((prev) => ({ ...prev, terms: undefined }));
    setViewingTerm(null);
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
      <p className="signup-field-notice" role="status">
        {duplicateNotices[name]}
      </p>
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
          {/* 보완 5: 좌우 2칸 — 왼쪽 계정 정보, 오른쪽 개인 정보 (좁은 화면에서는 위아래로 쌓인다) */}
          <div className="signup-columns">
            {/* 시안 기준: 라벨은 왼쪽, 입력칸(+중복 확인 버튼)은 오른쪽 */}
            <div className="signup-fields">
              <h3 className="signup-column-title">계정 정보</h3>
              <div className="signup-field">
                <label htmlFor="signup-nickname">이름 또는 닉네임<span className="form-required" aria-hidden="true"> *</span></label>
                <div className="signup-input-wrap">
                  <div className="signup-input-row">
                    <input
                      id="signup-nickname"
                      type="text"
                      placeholder={`${NICKNAME_MIN_LENGTH}~${NICKNAME_MAX_LENGTH}자 (예: 첫차준비생)`}
                      autoComplete="nickname"
                      maxLength={NICKNAME_MAX_LENGTH}
                      {...fieldProps('nickname')}
                    />
                    <button
                      className="signup-check-button"
                      type="button"
                      onClick={() => handleDuplicateCheck('nickname')}
                      disabled={checking === 'nickname'}
                    >
                      {checking === 'nickname' ? '확인 중…' : '중복 확인'}
                    </button>
                  </div>
                  {renderError('nickname')}
                </div>
              </div>

              <div className="signup-field">
                <label htmlFor="signup-email">이메일<span className="form-required" aria-hidden="true"> *</span></label>
                <div className="signup-input-wrap">
                  <div className="signup-input-row">
                    <input
                      id="signup-email"
                      type="email"
                      placeholder="user@example.com"
                      autoComplete="email"
                      maxLength={EMAIL_MAX_LENGTH}
                      {...fieldProps('email')}
                    />
                    {/* 보완 7: [중복 확인] 대신 [인증 코드 받기] (중복 확인 + 메일 발송). 60초 동안은 다시 받기 대기 */}
                    <button
                      className={emailVerified ? 'signup-check-button is-done' : 'signup-check-button'}
                      type="button"
                      onClick={handleSendCode}
                      disabled={checking === 'email' || emailVerified || resendWait > 0}
                    >
                      {checking === 'email'
                        ? '보내는 중…'
                        : emailVerified
                          ? '인증 완료'
                          : verification
                            ? resendWait > 0
                              ? `${resendWait}초 후 다시 받기`
                              : '다시 받기'
                            : '인증 코드 받기'}
                    </button>
                  </div>
                  {renderError('email')}
                  {/* 보완 7: 코드를 보냈으면 코드 입력칸 + [확인] + 남은 시간 */}
                  {verification && !emailVerified && (
                    <div className="signup-code-row">
                      <div className="signup-input-row">
                        <input
                          id="signup-email-code"
                          type="text"
                          inputMode="numeric"
                          placeholder="인증 코드 6자리"
                          autoComplete="one-time-code"
                          maxLength={6}
                          value={emailCode}
                          onChange={(event) => {
                            setEmailCode(event.target.value.replace(/\D/g, '')); // 숫자만 남긴다
                            setErrors((prev) => ({ ...prev, emailCode: undefined }));
                          }}
                          className={errors.emailCode ? 'has-error' : undefined}
                          aria-label="이메일 인증 코드"
                          aria-invalid={Boolean(errors.emailCode)}
                          aria-describedby={errors.emailCode ? 'signup-emailCode-error' : undefined}
                        />
                        <span className={codeLeft > 0 ? 'signup-code-timer' : 'signup-code-timer is-expired'}>
                          {codeLeft > 0 ? `남은 시간 ${formatSeconds(codeLeft)}` : '코드 만료'}
                        </span>
                        <button
                          className="signup-check-button"
                          type="button"
                          onClick={handleConfirmCode}
                          disabled={checking === 'emailCode' || codeLeft <= 0}
                        >
                          {checking === 'emailCode' ? '확인 중…' : '확인'}
                        </button>
                      </div>
                      {renderError('emailCode')}
                    </div>
                  )}
                  {/* 도메인 오타 안내 — 가입을 막지는 않고, [바꾸기]로 한 번에 고친다 */}
                  {!errors.email && emailSuggestion && (
                    <p className="signup-email-hint" role="status">
                      <strong>{emailSuggestion.split('@')[1]}</strong> 을(를) 입력하려던 건가요?
                      <button
                        type="button"
                        onClick={() => handleChange({ target: { name: 'email', value: emailSuggestion } })}
                      >
                        바꾸기
                      </button>
                    </p>
                  )}
                </div>
              </div>

              <div className="signup-field">
                <label htmlFor="signup-password">비밀번호<span className="form-required" aria-hidden="true"> *</span></label>
                <div className="signup-input-wrap">
                  <PasswordInput
                    id="signup-password"
                    placeholder="영문·숫자·특수문자 포함 8~20자"
                    autoComplete="new-password"
                    maxLength={PASSWORD_MAX}
                    {...fieldProps('password')}
                  />
                  <ul className="signup-password-requirements" aria-label="비밀번호 조건">
                    {passwordRules.map((rule) => (
                      <li className={rule.met ? 'is-met' : ''} key={rule.label}>
                        <span aria-hidden="true">{rule.met ? '✓' : '○'}</span>
                        {rule.label}
                      </li>
                    ))}
                  </ul>
                  {renderError('password')}
                </div>
              </div>

              {/* 비밀번호 확인 (보완 2 · 보완 목록 ④) — 서버로는 보내지 않고 화면에서만 비교 */}
              <div className="signup-field">
                <label htmlFor="signup-password-confirm">비밀번호 확인<span className="form-required" aria-hidden="true"> *</span></label>
                <div className="signup-input-wrap">
                  <PasswordInput
                    id="signup-password-confirm"
                    placeholder="영문·숫자·특수문자 포함 8~20자"
                    autoComplete="new-password"
                    maxLength={PASSWORD_MAX}
                    {...fieldProps('passwordConfirm')}
                  />
                  {renderError('passwordConfirm')}
                </div>
              </div>
            </div>

            {/* 보완 5: 개인 정보 — 저장은 user_profiles(V8). 전화번호는 필수(보완 11), 인증하지 않고 형식만 확인 */}
            <div className="signup-fields">
              <h3 className="signup-column-title">개인 정보</h3>
              <div className="signup-field">
                <label htmlFor="signup-birth-date">생년월일<span className="form-required" aria-hidden="true"> *</span></label>
                <div className="signup-input-wrap">
                  <BirthDateInput id="signup-birth-date" {...fieldProps('birthDate')} />
                  {renderError('birthDate')}
                </div>
              </div>

              <div className="signup-field">
                <span className="signup-field-label" id="signup-gender-label">
                  성별<span className="form-required" aria-hidden="true"> *</span>
                </span>
                <div className="signup-input-wrap">
                  <div
                    className={errors.gender ? 'signup-gender has-error' : 'signup-gender'}
                    role="radiogroup"
                    aria-labelledby="signup-gender-label"
                    aria-describedby={errors.gender ? 'signup-gender-error' : undefined}
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
                <label htmlFor="signup-phone">
                  전화번호<span className="form-required" aria-hidden="true"> *</span>
                </label>
                <div className="signup-input-wrap">
                  <input
                    id="signup-phone"
                    type="tel"
                    inputMode="numeric"
                    placeholder="010-1234-5678"
                    autoComplete="tel-national"
                    maxLength={13}
                    {...fieldProps('phone')}
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
          </div>

          <fieldset
            className={errors.terms ? 'signup-terms has-error' : 'signup-terms'}
            aria-describedby={errors.terms ? 'signup-terms-error' : undefined}
          >
            <legend>약관 동의</legend>
            <div className="signup-term signup-term-all">
              <label htmlFor="signup-term-all">
                <input id="signup-term-all" type="checkbox" checked={allAgreed} onChange={handleAllAgree} />
                <span>모든 약관에 동의합니다.</span>
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
                <button
                  className="signup-term-detail"
                  type="button"
                  aria-label={`${term.title} 보기`}
                  onClick={() => setViewingTerm(term)}
                >
                  보기
                </button>
              </div>
            ))}
          </fieldset>
          {renderError('terms')}

          <p className="signup-notice" role="status">
            {notice}
          </p>
          {serverError && (
            <p className="signup-error" role="alert">
              {serverError}
            </p>
          )}
          <button className="signup-submit" type="submit" disabled={submitting}>
            {submitting ? '가입 중…' : '회원가입 완료'}
          </button>
        </form>

        <p className="signup-login-link">
          이미 계정이 있으신가요? <Link to="/login">로그인</Link>
        </p>
      </section>

      <footer className="signup-footer">
        <strong>CreditCompass</strong>
        <p>첫차 구매 전, 감당 가능한 비용부터 확인하세요.</p>
        <small>본 서비스는 교육·시연용이며 실제 NICE·KCB 신용점수나 금융기관 심사 결과를 의미하지 않습니다.</small>
      </footer>

      {/* 팝업: 약관 보기, 회원가입 완료 */}
      {viewingTerm && (
        <TermsModal
          term={viewingTerm}
          agreed={agreements[viewingTerm.id]}
          onAgree={handleAgreeTerm}
          onClose={() => setViewingTerm(null)}
        />
      )}
      {isCompleteOpen && <SignupCompleteModal email={joinedEmail} onClose={() => setIsCompleteOpen(false)} />}
    </div>
  );
}
