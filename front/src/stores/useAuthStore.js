import { create } from 'zustand';

// 로그인 상태 저장소 (zustand)
// access token 은 메모리에만 둔다 → localStorage 에 두면 악성 스크립트(XSS)가 읽어 갈 수 있다.
// 새로고침하면 메모리가 비워지지만, 앱이 시작될 때 refresh token 쿠키로 다시 받아 온다 (App.jsx).
const useAuthStore = create((set) => ({
  accessToken: null, // 요청마다 Authorization: Bearer 로 보낼 JWT
  member: null, // 로그인한 회원 { id, email, nickName, role }
  initialized: false, // 앱 시작 시 로그인 복원 시도가 끝났는지 (끝나기 전에는 로그인 여부를 판단하지 않는다)

  // 로그인 · 재발급 성공: 서버 응답 { accessToken, member } 를 그대로 저장
  setAuth: ({ accessToken, member }) => set({ accessToken, member }),

  // 로그아웃: 저장한 로그인 정보를 지운다
  clearAuth: () => set({ accessToken: null, member: null }),

  // 로그인 복원 시도가 끝남 (성공 · 실패 모두)
  setInitialized: () => set({ initialized: true }),
}));

export default useAuthStore;
