import { Outlet } from 'react-router-dom';
import { isAdminRole } from '../features/auth/roles';
import useAuthStore from '../stores/useAuthStore';
import Layout from './Layout';
import NotFound from '../pages/not-found/NotFound';

// 7단계: 관리자만 들어갈 수 있는 화면(/console)을 감싸는 레이아웃 라우트 (App.jsx 에서 사용).
// 보완 11: 관리자가 아니면(비회원 · 일반 회원) 안내 · 이동 없이 "없는 주소"와 똑같은 404 화면을 보여 준다
//   → 관리자 화면이 있다는 것 자체를 알 수 없게 (관리자 로그인 화면은 없앴고, 관리자도 일반 로그인 후 들어온다)
// 화면에서 막는 것은 길 안내일 뿐이고, 실제 데이터는 서버가 /api/v1/admin/** 를 관리자 · 총관리자에게만 준다
// (SecurityConfig — 일반 회원에게도 404)
export default function RequireAdmin() {
  const accessToken = useAuthStore((state) => state.accessToken);
  const initialized = useAuthStore((state) => state.initialized);
  const role = useAuthStore((state) => state.member?.role);

  // 새로고침 직후에는 refresh token 으로 로그인을 복원하는 중이다 → 결과가 나올 때까지 아무것도 그리지 않는다
  // (안내 문구를 띄우면 이 주소가 특별하다는 걸 알 수 있다)
  if (!initialized) {
    return null;
  }
  if (!accessToken || !isAdminRole(role)) {
    // App.jsx 의 없는 주소(*)와 같은 화면 — 헤더까지 똑같이
    return <Layout><NotFound /></Layout>;
  }
  return <Outlet />;
}
