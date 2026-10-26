// 회원 탈퇴 팝업 (마이페이지 "계정 및 데이터 → 회원 탈퇴 [탈퇴]" 버튼)
// 회원 탈퇴는 되돌릴 수 없는 위험한 작업이라 바깥 클릭·Esc로 닫히지 않고(dismissible=false),
// 안내 확인 체크 + 비밀번호 확인을 해야 탈퇴 버튼이 켜진다. (보완 4: 탈퇴 API 연결)
import { useState } from 'react';
import AuthModal from '../../features/auth/components/AuthModal';
import PasswordInput from '../../features/auth/components/PasswordInput';
import './AccountManageModal.css';

// onWithdraw({ password, confirmText }): 탈퇴 요청. 실패하면 예외를 던지고, 이 팝업이 오류 문구를 보여 준다
// socialOnly(보완 8): 구글로만 가입해 비밀번호가 없으면 비밀번호 대신 "탈퇴" 를 입력해 확인한다
export default function AccountManageModal({ socialOnly = false, onWithdraw, onClose }) {
  const [confirmed, setConfirmed] = useState(false);
  const [password, setPassword] = useState('');
  const [error, setError] = useState(''); // 탈퇴 실패 문구 (예: 비밀번호가 올바르지 않습니다.)
  const [withdrawing, setWithdrawing] = useState(false);

  async function handleWithdraw() {
    setWithdrawing(true);
    setError('');
    try {
      // 성공하면 마이페이지가 팝업을 닫고 메인으로 이동한다
      await onWithdraw(socialOnly ? { confirmText: password } : { password });
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
          {/* 실제 탈퇴 동작(MemberServiceImpl.withdraw)과 맞춘 문구 */}
          <li>회원 정보 · 개인정보 · 취향 테스트 결과 · 구매계획 · 관심차량(이 브라우저에 저장한 목록 포함)이 삭제됩니다.</li>
          <li>재무 진단 기록은 회원과의 연결을 끊어, 누구의 기록인지 알 수 없는 상태로 남습니다.</li>
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

        {/* 보완 4: 되돌릴 수 없는 작업이라 비밀번호를 한 번 더 확인한다
            보완 8: 구글로만 가입한 회원은 비밀번호가 없어 "탈퇴" 를 직접 입력한다 */}
        <label className="account-manage-password-label" htmlFor="withdraw-password">
          {socialOnly ? '확인을 위해 "탈퇴"를 입력해 주세요' : '비밀번호 확인'}
        </label>
        {socialOnly ? (
          <input
            id="withdraw-password"
            className="account-manage-password"
            type="text"
            placeholder="탈퇴"
            autoComplete="off"
            value={password}
            onChange={(event) => {
              setPassword(event.target.value);
              setError('');
            }}
            disabled={withdrawing}
          />
        ) : (
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
        )}
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
          disabled={!confirmed || (socialOnly ? password.trim() !== '탈퇴' : !password) || withdrawing}
        >
          {withdrawing ? '처리 중…' : '회원 탈퇴'}
        </button>
      </div>
    </AuthModal>
  );
}
