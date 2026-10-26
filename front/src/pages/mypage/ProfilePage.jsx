// 6단계: 개인정보 · 계정 관리 (/mypage/profile) — 마이페이지 프로필 카드의 [개인정보 · 계정 관리] 로 들어온다
// 위: 개인정보 수정 — 한 상자 안에 왼쪽 기본 정보 + 차량 구매 정보, 오른쪽 개인 정보. 제목 줄 [저장] 이 바뀐 항목을 한 번에 저장
// 아래: 계정 관리 (로그인 = 방법 + 로그인된 기기 · 비밀번호 변경 · 이메일 알림 · 회원 탈퇴) — 마이페이지에서 옮겨 옴, 팝업은 그대로
import { useCallback, useEffect, useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import {
  changePassword,
  checkNickName,
  getSessions,
  logout,
  logoutOtherSessions,
  logoutSession,
} from '../../features/auth/authApi';
import { getMe, updateNickName, updateProfile, withdraw } from '../../features/auth/memberApi';
import { checkNickNameWords } from '../../features/auth/nickNamePolicy';
import useAuthStore from '../../stores/useAuthStore';
import { showToast } from '../../stores/useToastStore';
import BirthDateInput from '../signup/BirthDateInput';
import { formatPhone, GENDER_OPTIONS, getAge, MIN_SIGNUP_AGE, validateBirthDate, validatePhone } from '../signup/profileRules';
import AccountManageModal from './AccountManageModal';
import { CardError, CardLoading } from './CardStatus';
import EmailNotificationModal from './EmailNotificationModal';
import { NOTIFICATION_OPTIONS } from './notificationOptions';
import PasswordChangeModal from './PasswordChangeModal';
import { deviceName, DRIVING_OPTIONS, formatDateTime, PURCHASE_OPTIONS } from './profileOptions';
import './MyPage.css';
import './ProfilePage.css';

const NICKNAME_MIN = 2;
const NICKNAME_MAX = 12;
const SESSION_PREVIEW = 3; // 로그인된 기기는 처음에 최근 3대만 보여 준다

// 바뀐 항목 이름 (화면 순서대로) — 저장 버튼 옆 "바꾼 항목" 과 저장 알림에 쓴다
const FIELD_LABELS = {
  nickname: '닉네임',
  drivingExperience: '운전 경력',
  purchaseTiming: '구매 예정',
  birthDate: '생년월일',
  gender: '성별',
  phone: '전화번호',
};

// 서버에서 받은 내 정보 → 입력칸 값 (전화번호는 가린 값만 오므로 입력칸은 비워 두고 "현재 번호" 로 보여 준다)
const toForm = (me) => ({
  nickname: me.nickName ?? '',
  birthDate: me.birthDate ?? '',
  gender: me.gender ?? '',
  phone: '',
  drivingExperience: me.drivingExperience ?? '',
  purchaseTiming: me.purchaseTiming ?? '',
});

// 처음 값(서버)과 지금 입력을 비교해 바뀐 항목 목록을 만든다
function changedFields(form, me, clearPhone) {
  const original = toForm(me);
  return Object.keys(FIELD_LABELS).filter((key) => {
    if (key === 'phone') return form.phone !== '' || clearPhone; // 전화번호는 새로 입력했거나 지우기를 눌렀을 때만
    if (key === 'nickname') return form.nickname.trim() !== original.nickname;
    return form[key] !== original[key];
  });
}

// 바뀐 칸 라벨 옆 작은 점
function ChangedDot({ on }) {
  return on ? <span className="profile-changed-dot" title="바뀐 항목">•</span> : null;
}

export default function ProfilePage() {
  const navigate = useNavigate();
  const [me, setMe] = useState(null);                   // 서버의 내 정보 (저장하면 새 값으로 바뀜)
  const [meStatus, setMeStatus] = useState('loading');  // 'loading' | 'done' | 'error'
  const [reloadKey, setReloadKey] = useState(0);
  const [form, setForm] = useState(null);
  const [errors, setErrors] = useState({});
  const [checkedNickname, setCheckedNickname] = useState(''); // [중복 확인] 으로 사용 가능하다고 확인한 닉네임
  const [checking, setChecking] = useState(false);
  const [clearPhone, setClearPhone] = useState(false);  // 저장된 전화번호 지우기
  const [saving, setSaving] = useState(false);
  const [saveError, setSaveError] = useState('');

  // 로그인된 기기
  const [sessions, setSessions] = useState([]);
  const [sessionStatus, setSessionStatus] = useState('loading');
  const [sessionBusy, setSessionBusy] = useState(false);
  const [showAllSessions, setShowAllSessions] = useState(false); // 기기가 많으면 최근 3대만 보이다가 펼침

  // 계정 관리 팝업: 'password' | 'notification' | 'account' | null
  const [modal, setModal] = useState(null);
  const [notification, setNotification] = useState('IMPORTANT'); // 이메일 알림 (예시 기능, 저장은 보완 9)

  // 내 정보 불러오기
  useEffect(() => {
    let ignore = false; // 응답 전에 화면을 떠나면 결과를 버린다
    getMe()
      .then((data) => {
        if (ignore) return;
        setMe(data);
        setForm(toForm(data));
        setMeStatus('done');
      })
      .catch(() => !ignore && setMeStatus('error'));
    return () => {
      ignore = true;
    };
  }, [reloadKey]);

  // 로그인된 기기 불러오기 (기기 로그아웃 뒤에도 다시 부른다)
  const loadSessions = useCallback(() => {
    setSessionStatus('loading');
    getSessions()
      .then((list) => {
        setSessions(list);
        setSessionStatus('done');
      })
      .catch(() => setSessionStatus('error'));
  }, []);

  useEffect(() => {
    loadSessions();
  }, [loadSessions]);

  function handleChange(event) {
    const { name, value } = event.target;
    // 전화번호는 숫자만 받아 하이픈을 자동으로 넣는다 (회원가입과 같음)
    setForm((prev) => ({ ...prev, [name]: name === 'phone' ? formatPhone(value) : value }));
    setErrors((prev) => ({ ...prev, [name]: undefined }));
    if (name === 'nickname') setCheckedNickname(''); // 닉네임을 바꾸면 다시 확인해야 한다
    if (name === 'phone') setClearPhone(false);
    setSaveError('');
  }

  // 닉네임 화면 규칙 (글자 수 · 금지어). 문제없으면 빈 문자열
  function nicknameRule(value) {
    if (!value) return '닉네임을 입력해 주세요.';
    if (value.length < NICKNAME_MIN || value.length > NICKNAME_MAX) {
      return `닉네임은 ${NICKNAME_MIN}~${NICKNAME_MAX}자로 입력해 주세요.`;
    }
    return checkNickNameWords(value) ?? '';
  }

  // [중복 확인] → GET /auth/check-nickname (지금 닉네임 그대로면 묻지 않는다)
  async function handleCheckNickname() {
    const value = form.nickname.trim();
    if (value === me.nickName) {
      setErrors((prev) => ({ ...prev, nickname: '지금 사용 중인 닉네임입니다.' }));
      return;
    }
    const rule = nicknameRule(value);
    if (rule) {
      setErrors((prev) => ({ ...prev, nickname: rule }));
      return;
    }
    setChecking(true);
    try {
      if (await checkNickName(value)) setCheckedNickname(value);
      else setErrors((prev) => ({ ...prev, nickname: '이미 사용 중인 닉네임입니다.' }));
    } catch (error) {
      setErrors((prev) => ({ ...prev, nickname: error.response?.data?.error?.message ?? '중복 확인에 실패했습니다.' }));
    } finally {
      setChecking(false);
    }
  }

  // 저장 전 화면 검사. 오류가 있으면 { 칸: 문구 }
  function validate() {
    const next = {};
    const nickname = form.nickname.trim();
    if (nickname !== me.nickName) {
      next.nickname = nicknameRule(nickname) || (checkedNickname !== nickname ? '[중복 확인]을 눌러 주세요.' : undefined);
    }
    if (form.birthDate) {
      const message = validateBirthDate(form.birthDate);
      if (message) next.birthDate = message;
    }
    if (form.phone) {
      const message = validatePhone(form.phone);
      if (message) next.phone = message;
    }
    return Object.fromEntries(Object.entries(next).filter(([, value]) => value));
  }

  // [개인정보 저장] — 닉네임이 바뀌었으면 PATCH /members/me, 나머지는 PUT /members/me/profile
  async function handleSave(event) {
    event.preventDefault();
    if (saving) return;
    const changedNow = changedFields(form, me, clearPhone);
    if (changedNow.length === 0) return; // 바뀐 게 없으면 보내지 않는다
    const found = validate();
    setErrors(found);
    if (Object.keys(found).length) {
      setSaveError('저장하지 못했습니다. 빨간 칸을 확인해 주세요.');
      return;
    }
    setSaving(true);
    setSaveError('');
    try {
      const nickname = form.nickname.trim();
      if (nickname !== me.nickName) {
        const updated = await updateNickName(nickname);
        useAuthStore.getState().updateMember({ nickName: updated.nickName }); // 헤더 닉네임도 바로 바꾼다
      }
      const saved = await updateProfile({
        birthDate: form.birthDate || null,       // 비어 있으면 그대로 (지우지 않음)
        gender: form.gender || null,
        phone: clearPhone ? '' : form.phone || null, // 새로 입력했을 때만 바꾼다
        drivingExperience: form.drivingExperience, // '' 이면 지우기
        purchaseTiming: form.purchaseTiming,
      });
      setMe(saved);
      setForm(toForm(saved));
      setCheckedNickname('');
      setClearPhone(false);
      showToast(`${changedNow.map((key) => FIELD_LABELS[key]).join(' · ')}을(를) 저장했어요.`);
    } catch (error) {
      const { code, message } = error.response?.data?.error ?? {};
      if (code === 'AGE_RESTRICTED') setErrors((prev) => ({ ...prev, birthDate: message }));
      else if (code?.startsWith('NICKNAME')) setErrors((prev) => ({ ...prev, nickname: message }));
      setSaveError(code === 'AGE_RESTRICTED' || code?.startsWith('NICKNAME')
        ? '저장하지 못했습니다. 빨간 칸을 확인해 주세요.'
        : message ?? '저장에 실패했습니다. 잠시 후 다시 시도해 주세요.');
    } finally {
      setSaving(false);
    }
  }

  // 기기 하나 로그아웃
  async function handleLogoutSession(session) {
    setSessionBusy(true);
    try {
      await logoutSession(session.id);
      showToast(`${deviceName(session.device)} 기기를 로그아웃했어요. 열려 있던 화면은 최대 30분 안에 로그아웃됩니다.`);
    } catch (error) {
      showToast(error.response?.data?.error?.message ?? '로그아웃하지 못했습니다.');
    } finally {
      setSessionBusy(false);
      loadSessions();
    }
  }

  // 다른 기기 모두 로그아웃 (지금 기기만 남김)
  async function handleLogoutOthers() {
    setSessionBusy(true);
    try {
      const count = await logoutOtherSessions();
      showToast(count ? `다른 기기 ${count}대를 로그아웃했어요. 열려 있던 화면은 최대 30분 안에 로그아웃됩니다.` : '로그아웃할 다른 기기가 없어요.');
    } catch (error) {
      showToast(error.response?.data?.error?.message ?? '로그아웃하지 못했습니다.');
    } finally {
      setSessionBusy(false);
      loadSessions();
    }
  }

  // 현재 비밀번호를 (변경 · 탈퇴 합쳐) 5번 틀리면 서버가 로그아웃시킨다(PASSWORD_CONFIRM_LOGOUT)
  // → 팝업을 닫고 이 화면도 로그아웃. 그 밖의 실패는 팝업 안에 오류 문구
  async function logoutIfTooManyFailures(error) {
    const failure = error.response?.data?.error;
    if (failure?.code !== 'PASSWORD_CONFIRM_LOGOUT') throw error;
    setModal(null);
    await logout(); // 로그인 정보가 지워지면 RequireAuth 가 로그인 화면으로 보낸다
    showToast(failure.message);
  }

  async function handleChangePassword(passwords) {
    try {
      await changePassword(passwords);
    } catch (error) {
      await logoutIfTooManyFailures(error);
      return;
    }
    setModal(null);
    loadSessions(); // 다른 기기 로그인이 끊겼으니 목록도 새로
    showToast('비밀번호를 변경했어요. 다른 기기는 로그인을 이어 갈 수 없어요.');
  }

  // 회원 탈퇴: 서버 탈퇴 → 메인으로 먼저 이동 → 로그아웃 처리 → 공용 알림
  async function handleWithdraw(confirmation) {
    try {
      await withdraw(confirmation);
    } catch (error) {
      await logoutIfTooManyFailures(error);
      return;
    }
    setModal(null);
    navigate('/'); // 먼저 이동 — 로그인 정보가 지워지면 RequireAuth 가 로그인 화면으로 보내기 때문
    await logout();
    showToast('회원 탈퇴가 완료되었습니다. 그동안 이용해 주셔서 감사합니다.');
  }

  function handleSaveNotification(value) {
    setNotification(value);
    setModal(null);
    showToast('이메일 알림 설정을 바꿨어요. (예시 기능 · 저장은 준비 중)');
  }

  if (meStatus === 'loading') {
    return <div className="profile-page"><CardLoading label="내 정보를 불러오는 중…" /></div>;
  }
  if (meStatus === 'error') {
    return (
      <div className="profile-page">
        <CardError message="내 정보를 불러오지 못했습니다." onRetry={() => { setMeStatus('loading'); setReloadKey((key) => key + 1); }} />
      </div>
    );
  }

  const changed = changedFields(form, me, clearPhone);
  const ageError = errors.birthDate && form.birthDate && getAge(form.birthDate) < MIN_SIGNUP_AGE;
  const otherSessions = sessions.filter((session) => !session.current);
  const notificationLabel = NOTIFICATION_OPTIONS.find((option) => option.value === notification)?.label;

  return (
    <div className="profile-page">
      {/* 지금 위치 — 취향 테스트 화면(taste-breadcrumb)과 같은 모양 */}
      <nav className="profile-breadcrumb" aria-label="현재 위치">
        <Link to="/mypage">마이페이지</Link>
        <span aria-hidden="true">/</span>
        <span aria-current="page">개인정보 · 계정 관리</span>
      </nav>
      <header className="profile-heading">
        <h1>개인정보 · 계정 관리</h1>
        {/* 마이페이지 제목 아래 설명과 같은 방식: 이 화면에서 할 수 있는 일을 한 줄로 */}
        <p>닉네임 · 생년월일 같은 개인정보를 고치고, 로그인된 기기와 비밀번호를 관리하세요.</p>
      </header>

      {me.socialOnly && (!me.birthDate || !me.gender) && (
        <p className="profile-notice">
          <strong>구글로 가입하셨어요.</strong> 닉네임은 구글 이름으로 자동으로 정해졌어요. 생년월일 · 성별을 입력하면
          연령대별 추천을 받을 수 있습니다.
        </p>
      )}

      {/* ① 개인정보 수정 — 한 상자로 묶고, 제목 줄의 [저장] 이 상자 전체(기본 정보 · 차량 구매 정보 · 개인 정보)를 저장한다 */}
      <form className="my-card profile-edit" onSubmit={handleSave} noValidate>
        <div className="profile-edit-head">
          <div>
            <h2>개인정보 수정</h2>
            <p>
              {changed.length
                ? <>바꾼 항목 <strong>{changed.length}개</strong>: {changed.map((key) => FIELD_LABELS[key]).join(' · ')}</>
                : '바꾼 항목만 저장됩니다. 아래 세 영역을 한 번에 저장합니다.'}
            </p>
            {saveError && <p className="profile-save-error" role="alert">{saveError}</p>}
          </div>
          <div className="profile-edit-buttons">
            <Link className="my-outline-button profile-small-button" to="/mypage">취소</Link>
            <button className="profile-dark-button" type="submit" disabled={saving || changed.length === 0}>
              {saving ? '저장 중…' : changed.length ? `저장 (${changed.length})` : '저장'}
            </button>
          </div>
        </div>

        <div className="profile-grid">
          <div className="profile-column">
            <h3 className="profile-column-title">기본 정보</h3>
            <p className="profile-card-desc">다른 회원에게 보이는 이름입니다.</p>

            <div className="profile-field">
              <label htmlFor="profile-nickname">닉네임<ChangedDot on={changed.includes('nickname')} /></label>
              <div>
                <div className="profile-input-row">
                  <input id="profile-nickname" name="nickname" value={form.nickname} onChange={handleChange}
                    maxLength={NICKNAME_MAX} className={errors.nickname ? 'has-error' : undefined}
                    aria-invalid={Boolean(errors.nickname)} aria-describedby="profile-nickname-msg" />
                  <button className="profile-dark-button" type="button" onClick={handleCheckNickname} disabled={checking}>
                    {checking ? '확인 중…' : '중복 확인'}
                  </button>
                </div>
                {errors.nickname ? (
                  <p className="profile-error" id="profile-nickname-msg">{errors.nickname}</p>
                ) : checkedNickname && checkedNickname === form.nickname.trim() ? (
                  <p className="profile-ok" id="profile-nickname-msg" role="status">사용할 수 있는 닉네임입니다.</p>
                ) : null}
              </div>
            </div>

            <div className="profile-field">
              <label htmlFor="profile-email">이메일</label>
              <div>
                <input id="profile-email" value={me.email} disabled />
                <p className="profile-hint">이메일은 바꿀 수 없습니다.</p>
              </div>
            </div>

            {/* 차량 구매 정보 (선택) */}
            <h3 className="profile-column-title profile-subtitle">차량 구매 정보</h3>
            <p className="profile-card-desc">보험료 · 구매계획 같은 비용 계산에 쓸 수 있는 정보입니다. (선택)</p>

            <div className="profile-field">
              <span className="profile-label" id="profile-driving-label">운전 경력<ChangedDot on={changed.includes('drivingExperience')} /></span>
              <ChoiceGroup name="drivingExperience" labelledBy="profile-driving-label" options={DRIVING_OPTIONS}
                value={form.drivingExperience} onChange={handleChange} />
            </div>

            <div className="profile-field">
              <span className="profile-label" id="profile-purchase-label">구매 예정<ChangedDot on={changed.includes('purchaseTiming')} /></span>
              <ChoiceGroup name="purchaseTiming" labelledBy="profile-purchase-label" options={PURCHASE_OPTIONS}
                value={form.purchaseTiming} onChange={handleChange} />
            </div>
          </div>

          <div className="profile-column">
            <h3 className="profile-column-title">개인 정보</h3>
            <p className="profile-card-desc">연령대별 추천 · 통계에 사용합니다. 다른 회원에게 보이지 않습니다.</p>

            <div className="profile-field">
              <label htmlFor="profile-birth">생년월일<ChangedDot on={changed.includes('birthDate')} /></label>
              <div>
                <BirthDateInput id="profile-birth" name="birthDate" value={form.birthDate} onChange={handleChange}
                  className={errors.birthDate ? 'has-error' : undefined} aria-invalid={Boolean(errors.birthDate)} />
                {ageError ? (
                  // 만 18세 미만: 저장하지 않고, 다시 확인하거나 탈퇴하도록 안내 (서버도 AGE_RESTRICTED 로 거절)
                  <p className="profile-age-error" role="alert">
                    <strong>만 {MIN_SIGNUP_AGE}세 이상만 입력할 수 있습니다.</strong> 생년월일을 다시 확인해 주세요.<br />
                    만 {MIN_SIGNUP_AGE}세 미만이라면 서비스를 이용할 수 없으니 아래 계정 관리의{' '}
                    <a href="#profile-withdraw">회원 탈퇴</a>를 해 주세요.
                  </p>
                ) : errors.birthDate ? (
                  <p className="profile-error">{errors.birthDate}</p>
                ) : (
                  <p className="profile-hint">만 {MIN_SIGNUP_AGE}세 이상만 입력할 수 있습니다.</p>
                )}
              </div>
            </div>

            <div className="profile-field">
              <span className="profile-label" id="profile-gender-label">성별<ChangedDot on={changed.includes('gender')} /></span>
              <div className="profile-choices is-three" role="radiogroup" aria-labelledby="profile-gender-label">
                {GENDER_OPTIONS.map((option) => (
                  <label key={option.value}>
                    <input type="radio" name="gender" value={option.value} checked={form.gender === option.value} onChange={handleChange} />
                    <span>{option.label}</span>
                  </label>
                ))}
              </div>
            </div>

            <div className="profile-field">
              <label htmlFor="profile-phone">전화번호<ChangedDot on={changed.includes('phone')} /> <small>(선택)</small></label>
              <div>
                <input id="profile-phone" name="phone" type="tel" inputMode="numeric" maxLength={13}
                  placeholder={me.phoneMasked && !clearPhone ? '새 번호 입력' : '010-1234-5678'}
                  value={form.phone} onChange={handleChange} className={errors.phone ? 'has-error' : undefined} />
                {errors.phone ? (
                  <p className="profile-error">{errors.phone}</p>
                ) : me.phoneMasked ? (
                  <p className="profile-hint">
                    {clearPhone ? '저장하면 전화번호를 지웁니다. ' : `현재 ${me.phoneMasked} · `}
                    <button className="profile-text-button" type="button" onClick={() => setClearPhone((value) => !value)}>
                      {clearPhone ? '지우지 않기' : '전화번호 지우기'}
                    </button>
                  </p>
                ) : (
                  <p className="profile-hint">입력하면 서비스 관련 연락에만 사용합니다.</p>
                )}
              </div>
            </div>
          </div>
        </div>
      </form>

      {/* ② 계정 관리 (마이페이지에서 옮겨 옴) — 로그인(방법 + 로그인된 기기) · 비밀번호 · 이메일 알림 · 탈퇴 */}
      <section className="my-card profile-section" aria-labelledby="profile-account-title">
        <div className="profile-section-head">
          <div>
            <h2 id="profile-account-title">계정 관리</h2>
            <p>각 항목은 누르면 바로 처리됩니다. (위 저장 버튼과 별개)</p>
          </div>
        </div>
        <ul className="profile-account-list">
          {/* 로그인: 로그인 방법 한 줄 + 로그인된 기기 칩 (기기 · 로그인/마지막 사용 시각 · [로그아웃], 현재 기기는 초록 테두리) */}
          <li className="profile-login-row">
            <strong>로그인</strong>
            <div>
              <span>{me.socialOnly ? `구글 계정 · ${me.email}` : `이메일 · ${me.email}`}</span>
              {sessionStatus === 'loading' && <small>로그인된 기기를 불러오는 중…</small>}
              {sessionStatus === 'error' && (
                <small className="profile-error">
                  로그인된 기기를 불러오지 못했습니다.{' '}
                  <button className="profile-text-button" type="button" onClick={loadSessions}>다시 시도</button>
                </small>
              )}
              {sessionStatus === 'done' && (
                <ul className="profile-device-chips" aria-label={`로그인된 기기 ${sessions.length}대`}>
                  {(showAllSessions ? sessions : sessions.slice(0, SESSION_PREVIEW)).map((session) => (
                    <li key={session.id} className={session.current ? 'is-current' : undefined}>
                      <strong>{deviceName(session.device)}</strong>
                      {session.current && <em className="profile-chip-current">현재 기기</em>}
                      <small>로그인 {formatDateTime(session.loggedInAt)} · 마지막 사용 {formatDateTime(session.lastUsedAt)}</small>
                      {!session.current && (
                        <button type="button" onClick={() => handleLogoutSession(session)} disabled={sessionBusy}>
                          로그아웃
                        </button>
                      )}
                    </li>
                  ))}
                  {sessions.length > SESSION_PREVIEW && (
                    <li className="profile-chip-more">
                      <button type="button" onClick={() => setShowAllSessions((value) => !value)}>
                        {showAllSessions ? '접기' : `+${sessions.length - SESSION_PREVIEW}대 더 보기`}
                      </button>
                    </li>
                  )}
                </ul>
              )}
              <small>모르는 기기가 있으면 [로그아웃]을 누르고 비밀번호를 바꿔 주세요. 이미 열려 있던 화면은 최대 30분 안에 로그아웃됩니다.</small>
            </div>
            <button className="my-outline-button profile-small-button" type="button" onClick={handleLogoutOthers}
              disabled={sessionBusy || sessionStatus !== 'done' || otherSessions.length === 0}>
              다른 기기 모두 로그아웃
            </button>
          </li>
          {!me.socialOnly && (
            <li>
              <strong>비밀번호</strong>
              <div>
                <span>영문 · 숫자 · 특수문자 8~20자</span>
                <small>바꾸면 다른 기기는 로그인을 이어 갈 수 없습니다</small>
              </div>
              <button className="my-outline-button" type="button" onClick={() => setModal('password')}>변경</button>
            </li>
          )}
          <li>
            <strong>이메일 알림</strong>
            <div>
              <span>{notificationLabel}</span>
              <small>예시 기능 — 저장은 준비 중입니다</small>
            </div>
            <button className="my-outline-button" type="button" onClick={() => setModal('notification')}>설정</button>
          </li>
        </ul>
        <div className="profile-withdraw" id="profile-withdraw">
          <span>탈퇴하면 개인 정보 · 취향 결과가 모두 삭제되며 되돌릴 수 없습니다.</span>
          <button type="button" onClick={() => setModal('account')}>회원 탈퇴</button>
        </div>
      </section>

      {/* 팝업은 열 때마다 새로 만들어서 입력값이 남지 않게 한다 */}
      {modal === 'password' && <PasswordChangeModal email={me.email} onChange={handleChangePassword} onClose={() => setModal(null)} />}
      {modal === 'notification' && (
        <EmailNotificationModal currentValue={notification} onSave={handleSaveNotification} onClose={() => setModal(null)} />
      )}
      {modal === 'account' && <AccountManageModal socialOnly={me.socialOnly} onWithdraw={handleWithdraw} onClose={() => setModal(null)} />}
    </div>
  );
}

// 운전 경력 · 구매 예정 시기 버튼 묶음 (선택 항목이라 "선택 안 함" 으로 지울 수 있다)
function ChoiceGroup({ name, labelledBy, options, value, onChange }) {
  return (
    <div className="profile-choices" role="radiogroup" aria-labelledby={labelledBy}>
      {[...options, { value: '', label: '선택 안 함' }].map((option) => (
        <label key={option.value || 'none'}>
          <input type="radio" name={name} value={option.value} checked={value === option.value} onChange={onChange} />
          <span>{option.label}</span>
        </label>
      ))}
    </div>
  );
}
