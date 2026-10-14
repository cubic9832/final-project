// 내 데이터 다운로드 및 회원 탈퇴 팝업 (Figma에는 없음. 마이페이지 "관리" 버튼용으로 추가)
// 회원 탈퇴는 되돌릴 수 없는 위험한 작업이라 바깥 클릭·Esc로 닫히지 않고(dismissible=false),
// 안내 확인 체크를 해야 탈퇴 버튼이 켜진다. 다운로드·탈퇴 API는 아직 없다.
import { useState } from 'react';
import AuthModal from './AuthModal';
import './AccountManageModal.css';

export default function AccountManageModal({ onWithdraw, onClose }) {
  const [confirmed, setConfirmed] = useState(false);
  const [notice, setNotice] = useState('');
  const [withdrawing, setWithdrawing] = useState(false);

  function handleWithdraw() {
    // 요청 중 상태를 보여 주기 위한 임시 지연. API 연결 시 서버 요청으로 바꾼다
    setWithdrawing(true);
    setTimeout(onWithdraw, 400);
  }

  return (
    <AuthModal
      title="내 데이터 및 회원 탈퇴"
      subtitle="저장한 데이터를 내려받거나 계정을 삭제합니다."
      onClose={onClose}
      dismissible={false}
      busy={withdrawing}
    >
      <section className="account-manage-section" aria-labelledby="account-download-title">
        <h3 id="account-download-title">내 데이터 다운로드</h3>
        <p>분석 기록, 관심차량, 구매계획을 파일로 내려받습니다.</p>
        <button
          className="auth-modal-button"
          type="button"
          onClick={() => setNotice('데이터 다운로드는 서버 연결 후 사용할 수 있습니다.')}
          disabled={withdrawing}
        >
          다운로드 요청
        </button>
        <p className="account-manage-notice" role="status">{notice}</p>
      </section>

      <section className="account-manage-section account-manage-danger" aria-labelledby="account-withdraw-title">
        <h3 id="account-withdraw-title">회원 탈퇴</h3>
        <ul>
          <li>저장한 분석 기록, 관심차량, 구매계획이 모두 삭제됩니다.</li>
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
      </section>

      <div className="auth-modal-actions">
        <button className="auth-modal-button" type="button" onClick={onClose} disabled={withdrawing}>
          취소
        </button>
        <button
          className="auth-modal-button auth-modal-button-danger"
          type="button"
          onClick={handleWithdraw}
          disabled={!confirmed || withdrawing}
        >
          {withdrawing ? '처리 중…' : '회원 탈퇴'}
        </button>
      </div>
    </AuthModal>
  );
}
