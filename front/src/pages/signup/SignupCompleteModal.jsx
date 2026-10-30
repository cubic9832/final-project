// 회원가입 완료 팝업 (Figma: AUTH 02-2 · 회원가입 완료 팝업)
// 회원가입 API(POST /api/v1/auth/signup)가 성공한 뒤에 띄운다.
import { CircleCheck } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import theme from '../../styles/theme';
import AuthModal from '../../features/auth/components/AuthModal';
import './SignupCompleteModal.css';

export default function SignupCompleteModal({ email, onClose }) {
  const navigate = useNavigate();

  return (
    <AuthModal title="회원가입이 완료됐어요" onClose={() => { onClose(); navigate('/'); }} size="sm">
      {/* 보완 11: 체크 아이콘이 한 줄을 통째로 차지하지 않게 안내 문구 왼쪽에 나란히 둔다 */}
      <div className="signup-complete-head">
        <span className="signup-complete-icon" aria-hidden="true">
          <CircleCheck size={theme.iconSize.md} strokeWidth={1.75} />
        </span>
        <p className="signup-complete-text">
          내 첫 차 취향을 알아볼까요? 로그인 후 8가지 질문으로 확인할 수 있어요. 지금 하지 않아도 괜찮아요.
        </p>
      </div>
      <p className="signup-complete-account">
        <strong>{email}</strong> 계정으로 가입되었습니다.
      </p>

      <div className="auth-modal-actions">
        <button className="auth-modal-button" type="button" onClick={() => navigate('/')}>
          나중에 하기
        </button>
        <button
          className="auth-modal-button auth-modal-button-primary"
          type="button"
          data-autofocus
          onClick={() => navigate('/login', { state: { from: '/taste-test' } })}
        >
          로그인하고 취향 테스트
        </button>
      </div>
    </AuthModal>
  );
}
