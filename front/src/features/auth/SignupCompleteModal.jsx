// 회원가입 완료 팝업 (Figma: AUTH 02-2 · 회원가입 완료 팝업)
// 회원가입 API(POST /api/v1/auth/signup)가 성공한 뒤에 띄운다.
import { CircleCheck } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import theme from '../../styles/theme';
import AuthModal from './AuthModal';
import './SignupCompleteModal.css';

export default function SignupCompleteModal({ email, onClose }) {
  const navigate = useNavigate();

  return (
    <AuthModal title="회원가입이 완료됐어요" onClose={onClose} size="sm">
      <div className="signup-complete-icon" aria-hidden="true">
        <CircleCheck size={theme.iconSize.lg} strokeWidth={1.5} />
      </div>
      <p className="signup-complete-text">
        가입한 계정으로 로그인하여 차량 구매 부담도 분석을 시작해 보세요.
      </p>
      <p className="signup-complete-account">
        <strong>{email}</strong> 계정으로 가입되었습니다.
      </p>

      <div className="auth-modal-actions">
        <button className="auth-modal-button" type="button" onClick={() => navigate('/')}>
          홈으로
        </button>
        <button
          className="auth-modal-button auth-modal-button-primary"
          type="button"
          data-autofocus
          onClick={() => navigate('/login')}
        >
          로그인하기
        </button>
      </div>
    </AuthModal>
  );
}
