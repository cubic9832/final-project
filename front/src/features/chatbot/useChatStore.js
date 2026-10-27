import { create } from 'zustand';
import { buildTermQuestion } from './glossaryTerms.js';

const useChatStore = create((set) => ({
  open: false,
  questionRequest: null,
  requestId: 0,
  setOpen: (open) => set({ open }),
  explain: (term, context, returnFocus) => set((state) => ({
    open: true,
    requestId: state.requestId + 1,
    questionRequest: { id: state.requestId + 1, text: buildTermQuestion(term, context), label: term.label, returnFocus },
  })),
  consumeQuestion: (id) => set((state) => state.questionRequest?.id === id ? { questionRequest: null } : {}),
}));

export default useChatStore;
