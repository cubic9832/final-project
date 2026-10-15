import { Navigate, Outlet, useLocation } from 'react-router-dom';
import useAuthStore from '../stores/useAuthStore';

// 로그인한 사람만 들어갈 수 있는 화면을 감싸는 레이아웃 라우트 (App.jsx 에서 사용).
// 로그인 상태가 아니면 /login 으로 보내고, 로그인 후 원래 가려던 주소로 돌아올 수 있게 from 을 넘긴다.
// (로그인 화면이 location.state.from 을 보고 돌아간다)
// 새로고침 후 로그인 복원(refresh token)은 다음 단계에서 추가한다.
export default function RequireAuth() {
  const accessToken = useAuthStore((state) => state.accessToken);
  const location = useLocation();

  if (!accessToken) {
    return <Navigate to="/login" replace state={{ from: location.pathname }} />;
  }
  return <Outlet />;
}
