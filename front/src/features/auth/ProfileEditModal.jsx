// 내 정보 수정 팝업 (Figma: ACCOUNT 02 · 내 정보 수정 팝업)
// 지금은 화면 안에서만 저장한다. API 연결 시 handleSubmit 에서 서버 요청으로 바꾼다.
import { useState } from 'react';
import { ArrowRight } from 'lucide-react';
import theme from '../../styles/theme';
import AuthModal from './AuthModal';
import './ProfileEditModal.css';

const NICKNAME_MAX_LENGTH = 50; // users.nick_name VARCHAR(50)

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

  // 처음 값과 달라졌으면 닫기 전에 폐기 여부를 묻는다 (AuthModal이 처리)
  const isDirty = value.trim() !== nickname;

  function handleChange(event) {
    setValue(event.target.value);
    setError('');
  }

  function handleSubmit(event) {
    event.preventDefault();
    const trimmed = value.trim();

    if (!trimmed) {
      setError('표시 이름을 입력해 주세요.');
      return;
    }
    if (trimmed.length > NICKNAME_MAX_LENGTH) {
      setError(`표시 이름은 ${NICKNAME_MAX_LENGTH}자 이하로 입력해 주세요.`);
      return;
    }

    // 저장 중 상태(버튼 비활성)를 보여 주기 위한 임시 지연. API 연결 시 서버 요청으로 바꾼다
    setSaving(true);
    setTimeout(() => onSave(trimmed), 400);
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
          <p className="auth-modal-example">예시 데이터 · 실제 개인정보를 사용하지 않습니다.</p>

          <form className="profile-edit-form" onSubmit={handleSubmit} noValidate>
            <div className="auth-modal-field">
              <label htmlFor="profile-nickname">표시 이름</label>
              <input
                id="profile-nickname"
                type="text"
                value={value}
                onChange={handleChange}
                disabled={saving}
                data-autofocus
                className={error ? 'has-error' : undefined}
                aria-invalid={Boolean(error)}
                aria-describedby={error ? 'profile-nickname-error' : undefined}
              />
              {error && (
                <p className="auth-modal-error" id="profile-nickname-error">
                  {error}
                </p>
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
