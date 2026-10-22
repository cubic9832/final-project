import AuthToast from '../features/auth/components/AuthToast';
import useToastStore from '../stores/useToastStore';

// 공용 알림 표시 자리 (Layout 에 하나만 둔다)
// 모양 · 4초 뒤 자동 닫힘 · 마우스를 올리면 멈춤은 기존 AuthToast 를 그대로 쓴다.
export default function GlobalToast() {
  const message = useToastStore((state) => state.message);
  const id = useToastStore((state) => state.id);
  const hide = useToastStore((state) => state.hide);

  if (!message) return null;
  return <AuthToast key={id} message={message} onClose={hide} />;
}
