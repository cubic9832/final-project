// 약관 보기 팝업 (Figma에는 없음. 회원가입 약관 옆 "보기" 버튼용으로 추가)
// 확정된 약관 문구가 없어 본문은 비워 두고 준비 중 안내만 보여 준다. 약관 문구를 지어내지 않는다.
import AuthModal from '../../features/auth/components/AuthModal';
import './TermsModal.css';

export default function TermsModal({ term, agreed, onAgree, onClose }) {
  return (
    <AuthModal
      title={`[${term.required ? '필수' : '선택'}] ${term.title}`}
      onClose={onClose}
      size="lg"
    >
      <div className="terms-body" tabIndex={0} aria-label={`${term.title} 본문`}>
        <p>약관 본문은 준비 중입니다.</p>
        <p>팀에서 확정한 약관 문구가 나오면 이 영역에 표시됩니다.</p>
      </div>

      <div className="auth-modal-actions">
        <button className="auth-modal-button" type="button" onClick={onClose}>
          닫기
        </button>
        {/* 이미 동의했으면 동의 버튼 대신 상태만 보여 준다 */}
        <button
          className="auth-modal-button auth-modal-button-primary"
          type="button"
          onClick={onAgree}
          disabled={agreed}
        >
          {agreed ? '동의함' : '동의하고 닫기'}
        </button>
      </div>
    </AuthModal>
  );
}
