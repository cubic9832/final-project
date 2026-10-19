// 회원 탈퇴 팝업 (마이페이지 "계정 및 데이터 → 회원 탈퇴 [탈퇴]" 버튼)
// 회원 탈퇴는 되돌릴 수 없는 위험한 작업이라 바깥 클릭·Esc로 닫히지 않고(dismissible=false),
// 안내 확인 체크 + 비밀번호 확인을 해야 탈퇴 버튼이 켜진다. (보완 4: 탈퇴 API 연결)
import { useState } from 'react';
import AuthModal from './AuthModal';
import PasswordInput from './PasswordInput';
import './AccountManageModal.css';

// onWithdraw(password): 탈퇴 요청. 실패하면 예외를 던지고, 이 팝업이 오류 문구를 보여 준다
export default function AccountManageModal({ onWithdraw, onClose }) {
  const [confirmed, setConfirmed] = useState(false);
  const [password, setPassword] = useState('');
  const [error, setError] = useState(''); // 탈퇴 실패 문구 (예: 비밀번호가 올바르지 않습니다.)
  const [withdrawing, setWithdrawing] = useState(false);

  async function handleWithdraw() {
    setWithdrawing(true);
    setError('');
    try {
      await onWithdraw(password); // 성공하면 마이페이지가 팝업을 닫고 메인으로 이동한다
    } catch (err) {
      setError(err.response?.data?.error?.message ?? '탈퇴에 실패했습니다. 잠시 후 다시 시도해 주세요.');
      setPassword('');
      setWithdrawing(false);
    }
  }

  return (
    <AuthModal
      title="회원 탈퇴"
      subtitle="계정을 삭제합니다."
      onClose={onClose}
      dismissible={false}
      busy={withdrawing}
    >
      <section className="account-manage-section account-manage-danger" aria-labelledby="account-withdraw-title">
        <h3 id="account-withdraw-title">탈퇴 전 확인해 주세요</h3>
        <ul>
          <li>회원 정보와 분석 기록·관심차량·구매계획이 모두 삭제됩니다.</li>
          <li>삭제한 데이터는 다시 복구할 수 없습니다.</li>
        </ul>
        <label className="account-manage-confirm">
          <input
            type="checkbox"
            checked={confirmed}
            onChange={(event) => setConfirmed(event.target.checked)}
            disabled={withdrawing}
          />
          위 내용을 확인했으며 탈퇴에 동의합니다.
        </label>

        {/* 보완 4: 되돌릴 수 없는 작업이라 비밀번호를 한 번 더 확인한다 */}
        <label className="account-manage-password-label" htmlFor="withdraw-password">
          비밀번호 확인
        </label>
        <PasswordInput
          id="withdraw-password"
          className="account-manage-password"
          placeholder="현재 비밀번호를 입력해 주세요"
          autoComplete="current-password"
          value={password}
          onChange={(event) => {
            setPassword(event.target.value);
            setError('');
          }}
          disabled={withdrawing}
        />
        {error && (
          <p className="account-manage-error" role="alert">
            {error}
          </p>
        )}
      </section>

      <div className="auth-modal-actions">
        <button className="auth-modal-button" type="button" onClick={onClose} disabled={withdrawing}>
          취소
        </button>
        <button
          className="auth-modal-button auth-modal-button-danger"
          type="button"
          onClick={handleWithdraw}
          disabled={!confirmed || !password || withdrawing}
        >
          {withdrawing ? '처리 중…' : '회원 탈퇴'}
        </button>
      </div>
    </AuthModal>
  );
}
