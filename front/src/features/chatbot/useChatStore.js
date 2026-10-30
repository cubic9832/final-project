import { create } from 'zustand';
import useAuthStore from '../../stores/useAuthStore.js';

const useChatStore = create((set) => ({
  open: false,
  questionRequest: null,
  requestId: 0,
  setOpen: (open) => set({ open }),
  explain: (term, returnFocus) => set((state) => ({
    open: true,
    requestId: state.requestId + 1,
    questionRequest: { id: state.requestId + 1, guideId: term.id, label: term.label, returnFocus },
  })),
  consumeQuestion: (id) => set((state) => state.questionRequest?.id === id ? { questionRequest: null } : {}),
}));

export default useChatStore;

useAuthStore.subscribe((state, previous) => {
  if (state.member?.id !== previous.member?.id) {
    useChatStore.setState({ open: false, questionRequest: null });
  }
});
