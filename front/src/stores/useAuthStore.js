import { create } from 'zustand';

// 로그인 상태 저장소 (zustand)
// access token 은 메모리에만 둔다 → localStorage 에 두면 악성 스크립트(XSS)가 읽어 갈 수 있다.
// 그래서 새로고침하면 로그인이 풀린다. 새로고침 후 로그인 유지는 refresh token 단계에서 추가한다.
const useAuthStore = create((set) => ({
  accessToken: null, // 요청마다 Authorization: Bearer 로 보낼 JWT
  member: null, // 로그인한 회원 { id, email, nickName, role }

  // 로그인 성공: 서버 응답 { accessToken, member } 를 그대로 저장
  setAuth: ({ accessToken, member }) => set({ accessToken, member }),

  // 로그아웃: 저장한 로그인 정보를 지운다
  clearAuth: () => set({ accessToken: null, member: null }),
}));

export default useAuthStore;
