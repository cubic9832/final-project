import { create } from 'zustand';

// 공용 알림(토스트) 저장소
// 화면이 바뀌어도(예: 로그아웃 후 메인으로 이동) 알림이 남아 있도록, 알림 내용을 화면 밖 저장소에 둔다.
// 표시는 Layout 의 <GlobalToast /> 한 곳에서 한다.
const useToastStore = create((set) => ({
  message: '', // 빈 문자열이면 알림 숨김
  id: 0, // 알림을 띄울 때마다 바뀌는 번호 → 같은 문구를 다시 띄워도 새 알림으로 보고 4초를 새로 센다

  show: (message) => set((state) => ({ message, id: state.id + 1 })),
  hide: () => set({ message: '' }),
}));

// 어느 파일에서든 한 줄로 알림을 띄운다: showToast('로그아웃되었습니다.')
export const showToast = (message) => useToastStore.getState().show(message);

export default useToastStore;
