import { useEffect } from 'react';
import { Navigate, Outlet, useLocation } from 'react-router-dom';
import { isAdminRole } from '../features/auth/roles';
import useAuthStore from '../stores/useAuthStore';
import { showToast } from '../stores/useToastStore';

// 7단계: 관리자만 들어갈 수 있는 화면(/admin)을 감싸는 레이아웃 라우트 (App.jsx 에서 사용).
// RequireAuth 와 같은 방식에 "role 이 관리자(ADMIN) · 총관리자(SUPER_ADMIN)인지" 를 더 본다.
// - 로그인 전: 관리자 로그인 화면(/admin/login)으로 (로그인 후 돌아올 수 있게 from 을 넘긴다)
// - 일반 회원: 메인으로 보내고 알림
// 화면에서 막는 것은 길 안내일 뿐이고, 실제 데이터는 서버가 /api/v1/admin/** 를 관리자 · 총관리자에게만 준다 (SecurityConfig)
export default function RequireAdmin() {
  const accessToken = useAuthStore((state) => state.accessToken);
  const initialized = useAuthStore((state) => state.initialized);
  const role = useAuthStore((state) => state.member?.role);
  const location = useLocation();
  const blocked = initialized && Boolean(accessToken) && !isAdminRole(role);

  // 일반 회원이 주소로 들어오면 메인으로 보내면서 이유를 알려 준다
  useEffect(() => {
    if (blocked) showToast('관리자만 들어갈 수 있는 화면입니다.');
  }, [blocked]);

  // 새로고침 직후에는 refresh token 으로 로그인을 복원하는 중이다 → 결과가 나올 때까지 기다린다
  if (!initialized) {
    return <p role="status">로그인 상태를 확인하는 중입니다…</p>;
  }
  if (!accessToken) {
    return <Navigate to="/admin/login" replace state={{ from: location.pathname + location.search }} />;
  }
  if (blocked) {
    return <Navigate to="/" replace />;
  }
  return <Outlet />;
}
