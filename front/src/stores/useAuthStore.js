import { create } from 'zustand';

// 로그인 상태 저장소 (zustand)
// access token 은 메모리에만 둔다 → localStorage 에 두면 악성 스크립트(XSS)가 읽어 갈 수 있다.
// 새로고침하면 메모리가 비워지지만, 앱이 시작될 때 refresh token 쿠키로 다시 받아 온다 (App.jsx).

// 보완 10: 같은 브라우저의 다른 탭에 회원 정보 변경(닉네임 등)을 알린다 (BroadcastChannel, 토큰은 보내지 않음)
// 지원하지 않는 브라우저에서는 null → 예전처럼 새로고침해야 반영
const memberChannel = typeof BroadcastChannel === 'undefined' ? null : new BroadcastChannel('auth-member');
// Node(테스트)에서는 열린 채널이 프로세스를 끝나지 못하게 붙잡는다 → unref (브라우저에는 없는 함수라 ?. 로)
memberChannel?.unref?.();

const useAuthStore = create((set) => ({
  accessToken: null, // 요청마다 Authorization: Bearer 로 보낼 JWT
  member: null, // 로그인한 회원 { id, email, nickName, role }
  initialized: false, // 앱 시작 시 로그인 복원 시도가 끝났는지 (끝나기 전에는 로그인 여부를 판단하지 않는다)

  // 로그인 · 재발급 성공: 서버 응답 { accessToken, member } 를 그대로 저장
  setAuth: ({ accessToken, member }) => set({ accessToken, member }),

  // 회원 정보 일부 바꾸기 (보완 3 추가: 닉네임 변경 → 헤더의 "닉네임님"도 바로 바뀐다)
  // 보완 10: 다른 탭에도 알려서 그 탭 헤더도 바로 바뀐다
  updateMember: (changes) => set((state) => {
    if (!state.member) return { member: null };
    memberChannel?.postMessage({ memberId: state.member.id, changes });
    return { member: { ...state.member, ...changes } };
  }),

  // 로그아웃: 저장한 로그인 정보를 지운다
  clearAuth: () => set({ accessToken: null, member: null }),

  // 로그인 복원 시도가 끝남 (성공 · 실패 모두)
  setInitialized: () => set({ initialized: true }),
}));

// 보완 10: 다른 탭에서 온 변경은 같은 회원일 때만 반영한다 (다시 알리지 않게 set 으로 직접 바꿈)
memberChannel?.addEventListener('message', ({ data }) => {
  useAuthStore.setState((state) => (
    state.member?.id === data?.memberId ? { member: { ...state.member, ...data.changes } } : {}
  ));
});

export default useAuthStore;
