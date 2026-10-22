// 내 정보 수정 팝업 (Figma: ACCOUNT 02 · 내 정보 수정 팝업)
// 보완 3 추가: [변경사항 저장] 이 서버에 닉네임을 저장한다 (PATCH /members/me). 겹치면 팝업 안에 오류 표시
// 10-22: 회원가입처럼 [중복 확인] 버튼 — 닉네임을 바꿨으면 확인해야 저장된다 (저장할 때 서버도 한 번 더 확인)
import { useState } from 'react';
import { ArrowRight } from 'lucide-react';
import theme from '../../styles/theme';
import AuthModal from '../../features/auth/components/AuthModal';
import { checkNickName } from '../../features/auth/authApi';
import { checkNickNameWords } from '../../features/auth/nickNamePolicy';
import './ProfileEditModal.css';

// 보완 2: 회원가입과 같은 2~12자 (DB 컬럼 users.nick_name 은 50 그대로)
const NICKNAME_MIN_LENGTH = 2;
const NICKNAME_MAX_LENGTH = 12;

// 예: firstcar@example.com → fi***@example.com
function maskEmail(email) {
  const [id, domain] = email.split('@');
  return `${id.slice(0, 2)}***@${domain}`;
}

export default function ProfileEditModal({ nickname, email, onSave, onClose }) {
  const [value, setValue] = useState(nickname);
  const [error, setError] = useState('');
  const [saving, setSaving] = useState(false);
  const [notice, setNotice] = useState('');
  const [checkedValue, setCheckedValue] = useState(''); // [중복 확인] 으로 사용 가능하다고 확인한 닉네임
  const [checking, setChecking] = useState(false);

  // 처음 값과 달라졌으면 닫기 전에 폐기 여부를 묻는다 (AuthModal이 처리)
  const isDirty = value.trim() !== nickname;

  function handleChange(event) {
    setValue(event.target.value);
    setError('');
    setCheckedValue(''); // 값이 바뀌면 다시 확인해야 한다
  }

  // 화면 규칙(글자 수 · 금지어)을 먼저 보고, 문제없으면 빈 문자열
  function validate(trimmed) {
    if (!trimmed) return '표시 이름을 입력해 주세요.';
    if (trimmed.length < NICKNAME_MIN_LENGTH || trimmed.length > NICKNAME_MAX_LENGTH) {
      return `표시 이름은 ${NICKNAME_MIN_LENGTH}~${NICKNAME_MAX_LENGTH}자로 입력해 주세요.`;
    }
    return checkNickNameWords(trimmed) ?? '';
  }

  // [중복 확인] → GET /auth/check-nickname. 지금 내 닉네임이면 서버에 묻지 않는다
  async function handleCheck() {
    const trimmed = value.trim();
    if (trimmed === nickname) {
      setError('지금 사용 중인 표시 이름입니다.');
      return;
    }
    const message = validate(trimmed);
    if (message) {
      setError(message);
      return;
    }
    setChecking(true);
    try {
      const available = await checkNickName(trimmed);
      if (available) setCheckedValue(trimmed);
      else setError('이미 사용 중인 닉네임입니다.');
    } catch (err) {
      setError(err.response?.data?.error?.message ?? '중복 확인에 실패했습니다. 잠시 후 다시 시도해 주세요.');
    } finally {
      setChecking(false);
    }
  }

  async function handleSubmit(event) {
    event.preventDefault();
    const trimmed = value.trim();

    // 바뀐 게 없으면 서버에 보내지 않고 닫는다
    if (trimmed === nickname) {
      onClose();
      return;
    }
    const message = validate(trimmed);
    if (message) {
      setError(message);
      return;
    }
    if (checkedValue !== trimmed) {
      setError('[중복 확인]을 눌러 주세요.');
      return;
    }

    // onSave: 서버 저장 (MyPage). 실패하면 예외를 던지고, 이 팝업이 오류 문구를 보여 준다
    setSaving(true);
    try {
      await onSave(trimmed);
    } catch (err) {
      setError(err.response?.data?.error?.message ?? '저장에 실패했습니다. 잠시 후 다시 시도해 주세요.');
      setSaving(false);
    }
  }

  return (
    <AuthModal
      title="내 정보 수정"
      subtitle="기본 정보를 수정하고 저장하세요."
      onClose={onClose}
      isDirty={isDirty}
      busy={saving}
    >
      {(requestClose) => (
        <>
          <p className="auth-modal-example">표시 이름은 저장됩니다 · 아래 재무·차량 입력정보는 예시 화면입니다.</p>

          <form className="profile-edit-form" onSubmit={handleSubmit} noValidate>
            <div className="auth-modal-field">
              <label htmlFor="profile-nickname">표시 이름</label>
              <div className="profile-nickname-row">
                <input
                  id="profile-nickname"
                  type="text"
                  value={value}
                  onChange={handleChange}
                  disabled={saving}
                  maxLength={NICKNAME_MAX_LENGTH}
                  data-autofocus
                  className={error ? 'has-error' : undefined}
                  aria-invalid={Boolean(error)}
                  aria-describedby={error ? 'profile-nickname-error' : undefined}
                />
                <button className="auth-modal-button" type="button" onClick={handleCheck} disabled={saving || checking}>
                  {checking ? '확인 중…' : '중복 확인'}
                </button>
              </div>
              {error ? (
                <p className="auth-modal-error" id="profile-nickname-error">
                  {error}
                </p>
              ) : (
                checkedValue === value.trim() &&
                checkedValue && (
                  <p className="profile-nickname-ok" role="status">
                    사용할 수 있는 닉네임입니다.
                  </p>
                )
              )}
            </div>

            <div className="auth-modal-field">
              <label htmlFor="profile-email">이메일</label>
              <input id="profile-email" type="text" value={maskEmail(email)} readOnly disabled />
              <p className="auth-modal-hint">이메일은 이 화면에서 변경할 수 없습니다.</p>
            </div>

            <section className="profile-edit-section" aria-labelledby="profile-input-title">
              <h3 id="profile-input-title">재무·차량 입력정보</h3>
              <div className="profile-edit-info">
                <strong>소득·지출, 자산·부채, 신용정보, 차량 이용조건</strong>
                <p>변경하려면 해당 입력 단계로 이동해 다시 분석하세요.</p>
                <button
                  className="profile-edit-link"
                  type="button"
                  onClick={() => setNotice('입력정보 수정 화면 연결은 준비 중입니다.')}
                >
                  입력정보 수정으로 이동
                  <ArrowRight size={theme.iconSize.sm} aria-hidden="true" />
                </button>
              </div>
              <p className="auth-modal-hint">프로필 저장은 기존 분석 결과를 다시 계산하지 않습니다.</p>
            </section>

            <p className="profile-edit-notice" role="status">
              {notice}
            </p>

            <div className="auth-modal-actions">
              <button className="auth-modal-button" type="button" onClick={requestClose} disabled={saving}>
                취소
              </button>
              <button className="auth-modal-button auth-modal-button-primary" type="submit" disabled={saving}>
                {saving ? '저장 중…' : '변경사항 저장'}
              </button>
            </div>
          </form>
        </>
      )}
    </AuthModal>
  );
}
