// 짧은 결과 알림 (예: "프로필을 저장했어요")
// docs/ui.md 토스트 규칙: 입력을 막지 않고 4초 뒤 닫힘, 마우스를 올리거나 포커스 중에는 멈춤, 직접 닫기 가능
import { useEffect, useState } from 'react';
import { CircleCheck, X } from 'lucide-react';
import theme from '../../styles/theme';
import './AuthToast.css';

const AUTO_CLOSE_MS = 4000;

export default function AuthToast({ message, onClose }) {
  const [paused, setPaused] = useState(false);

  // 멈춤 상태가 아닐 때만 4초 타이머를 건다. 다시 시작하면 4초를 새로 센다
  useEffect(() => {
    if (paused) return undefined;
    const timer = setTimeout(onClose, AUTO_CLOSE_MS);
    return () => clearTimeout(timer);
  }, [paused, onClose]);

  return (
    <div
      className="auth-toast"
      role="status"
      onMouseEnter={() => setPaused(true)}
      onMouseLeave={() => setPaused(false)}
      onFocus={() => setPaused(true)}
      onBlur={() => setPaused(false)}
    >
      <CircleCheck size={theme.iconSize.md} aria-hidden="true" />
      <span>{message}</span>
      <button className="auth-toast-close" type="button" aria-label="알림 닫기" onClick={onClose}>
        <X size={theme.iconSize.sm} />
      </button>
    </div>
  );
}
