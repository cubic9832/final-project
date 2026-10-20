// 비밀번호 변경 팝업 (보완 2 추가 · 10-20, 마이페이지 "계정 및 데이터 → 비밀번호 변경 [변경]")
// 현재 비밀번호 확인 → 새 비밀번호(회원가입과 같은 규칙) → 저장. 바꾸면 다른 기기 로그인은 끊기고 이 기기는 그대로
import { useState } from 'react';
import AuthModal from '../../features/auth/components/AuthModal';
import PasswordInput from '../../features/auth/components/PasswordInput';
import { getPasswordRules, PASSWORD_MAX, validatePassword } from '../../features/auth/passwordPolicy';
import './PasswordChangeModal.css';

// onChange({ currentPassword, newPassword }): 서버 저장. 실패하면 예외를 던지고, 이 팝업이 오류 문구를 보여 준다
export default function PasswordChangeModal({ email, onChange, onClose }) {
  const [form, setForm] = useState({ currentPassword: '', newPassword: '', confirm: '' });
  const [error, setError] = useState('');
  const [saving, setSaving] = useState(false);

  const rules = getPasswordRules(form.newPassword, email);
  const isDirty = Object.values(form).some((value) => value !== '');

  function handleChange(event) {
    const { name, value } = event.target;
    setForm((prev) => ({ ...prev, [name]: value }));
    setError('');
  }

  async function handleSubmit(event) {
    event.preventDefault();
    if (!form.currentPassword) return setError('현재 비밀번호를 입력해 주세요.');
    const ruleError = validatePassword(form.newPassword, email);
    if (ruleError) return setError(ruleError);
    if (form.newPassword !== form.confirm) return setError('새 비밀번호가 일치하지 않습니다.');
    if (form.newPassword === form.currentPassword) return setError('현재와 다른 비밀번호를 입력해 주세요.');

    setSaving(true);
    try {
      await onChange({ currentPassword: form.currentPassword, newPassword: form.newPassword });
    } catch (err) {
      // 현재 비밀번호 틀림 · 규칙 위반 등
      setError(err.response?.data?.error?.message ?? '비밀번호를 바꾸지 못했습니다. 잠시 후 다시 시도해 주세요.');
      setSaving(false);
    }
  }

  return (
    <AuthModal
      title="비밀번호 변경"
      subtitle="바꾸면 다른 기기의 로그인은 끊기고, 지금 기기는 유지돼요."
      onClose={onClose}
      isDirty={isDirty}
      busy={saving}
      size="sm"
    >
      {(requestClose) => (
        <form className="password-change-form" onSubmit={handleSubmit} noValidate>
          <div className="auth-modal-field">
            <label htmlFor="current-password">현재 비밀번호</label>
            <PasswordInput
              id="current-password"
              name="currentPassword"
              autoComplete="current-password"
              value={form.currentPassword}
              onChange={handleChange}
              disabled={saving}
              data-autofocus
            />
          </div>
          <div className="auth-modal-field">
            <label htmlFor="change-password">새 비밀번호</label>
            <PasswordInput
              id="change-password"
              name="newPassword"
              placeholder="영문·숫자·특수문자 포함 8~20자"
              autoComplete="new-password"
              maxLength={PASSWORD_MAX}
              value={form.newPassword}
              onChange={handleChange}
              disabled={saving}
            />
            <ul className="password-change-rules" aria-label="비밀번호 조건">
              {rules.map((rule) => (
                <li className={rule.met ? 'is-met' : ''} key={rule.label}>
                  {rule.met ? '✓' : '○'} {rule.label}
                </li>
              ))}
            </ul>
          </div>
          <div className="auth-modal-field">
            <label htmlFor="change-password-confirm">새 비밀번호 확인</label>
            <PasswordInput
              id="change-password-confirm"
              name="confirm"
              placeholder="새 비밀번호를 한 번 더 입력"
              autoComplete="new-password"
              maxLength={PASSWORD_MAX}
              value={form.confirm}
              onChange={handleChange}
              disabled={saving}
            />
            {error && (
              <p className="auth-modal-error" role="alert">
                {error}
              </p>
            )}
          </div>
          <div className="auth-modal-actions">
            <button className="auth-modal-button" type="button" onClick={requestClose} disabled={saving}>
              취소
            </button>
            <button className="auth-modal-button auth-modal-button-primary" type="submit" disabled={saving}>
              {saving ? '변경 중…' : '비밀번호 변경'}
            </button>
          </div>
        </form>
      )}
    </AuthModal>
  );
}
