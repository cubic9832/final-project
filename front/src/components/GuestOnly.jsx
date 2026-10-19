import { Navigate, Outlet, useLocation } from 'react-router-dom';
import useAuthStore from '../stores/useAuthStore';

// 보완 1 추가: 로그인하지 않은 사람만 들어가는 화면(로그인 · 회원가입)을 감싸는 레이아웃 라우트 (App.jsx 에서 사용).
// RequireAuth 의 반대: 이미 로그인했으면 메인으로 보낸다 (로그인 상태로 다시 로그인 · 가입하지 않게).
// 로그인 화면에서 막 로그인한 경우에는 로그인 화면이 보내려던 곳(location.state.from)으로 같이 보낸다.
export default function GuestOnly() {
  const accessToken = useAuthStore((state) => state.accessToken);
  const initialized = useAuthStore((state) => state.initialized);
  const location = useLocation();

  // 새로고침 직후 로그인 복원 중에는 판단하지 않는다 (로그인한 사람에게 로그인 화면이 잠깐 보이지 않게)
  if (!initialized) {
    return <p role="status">로그인 상태를 확인하는 중입니다…</p>;
  }

  if (accessToken) {
    return <Navigate to={location.state?.from ?? '/'} replace />;
  }
  return <Outlet />;
}
