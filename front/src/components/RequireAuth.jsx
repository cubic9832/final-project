import { Navigate, Outlet, useLocation } from 'react-router-dom';
import useAuthStore from '../stores/useAuthStore';

// 로그인한 사람만 들어갈 수 있는 화면을 감싸는 레이아웃 라우트 (App.jsx 에서 사용).
// 로그인 상태가 아니면 /login 으로 보내고, 로그인 후 원래 가려던 주소로 돌아올 수 있게 from 을 넘긴다.
// (로그인 화면이 location.state.from 을 보고 돌아간다)
export default function RequireAuth() {
  const accessToken = useAuthStore((state) => state.accessToken);
  const initialized = useAuthStore((state) => state.initialized);
  const location = useLocation();

  // 새로고침 직후에는 refresh token 으로 로그인을 복원하는 중이다 → 결과가 나올 때까지 기다린다
  // (기다리지 않으면 로그인한 사람도 잠깐 토큰이 없어서 로그인 화면으로 튕긴다)
  if (!initialized) {
    return <p role="status">로그인 상태를 확인하는 중입니다…</p>;
  }

  if (!accessToken) {
    return <Navigate to="/login" replace state={{ from: location.pathname }} />;
  }
  return <Outlet />;
}
