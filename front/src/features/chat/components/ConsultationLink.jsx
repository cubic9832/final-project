import { Headset } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import theme from '../../../styles/theme';
import './ConsultationLink.css';

// 8단계: 콤파(AI 챗봇) 안의 [상담원과 1:1 상담] 버튼 — 누르면 콤파를 닫고 상담 화면으로 이동만 한다
// 콤파는 조장 담당 파일이라 이 버튼만 따로 만들어 한 줄로 넣었다 (자세한 연동은 11-03 이후 조장과 협의)
// 로그인 전이면 /consultation 의 RequireAuth 가 로그인 화면으로 보낸다
export default function ConsultationLink({ onNavigate }) {
  const navigate = useNavigate();

  function handleClick() {
    onNavigate?.();
    navigate('/consultation');
  }

  return (
    <button type="button" className="consultation-link" onClick={handleClick}>
      <Headset size={theme.iconSize.sm} aria-hidden="true" />
      상담원과 1:1 상담하기
    </button>
  );
}
