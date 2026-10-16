import { TASTE_QUESTION_COUNT, TASTE_VERSION } from './tasteQuestions.js';
import { isValidTasteAnswers } from './tasteFlow.js';
import { isCompleteTasteAnswers } from './calculateTasteResult.js';

// 구 질문의 선택지 번호를 새 분기형 질문에 재사용하지 않는다.
const DRAFT_KEY = `creditcompass:taste-draft:v${TASTE_VERSION}`;

export function readTasteDraft() {
  try {
    const value = JSON.parse(sessionStorage.getItem(DRAFT_KEY));
    if (!value || !isValidTasteAnswers(value.answers)) return null;
    if (value.phase === 'result' && !isCompleteTasteAnswers(value.answers)) return null;
    return {
      answers: value.answers,
      phase: ['intro', 'question', 'result'].includes(value.phase) ? value.phase : 'intro',
      step: Math.min(Number.isInteger(value.step) && value.step >= 0 && value.step < TASTE_QUESTION_COUNT ? value.step : 0,
        value.answers.indexOf(null) < 0 ? TASTE_QUESTION_COUNT - 1 : value.answers.indexOf(null)),
    };
  } catch { return null; }
}

export function writeTasteDraft(draft) {
  try { sessionStorage.setItem(DRAFT_KEY, JSON.stringify(draft)); } catch { /* 테스트 자체는 저장소 없이 이용 가능 */ }
}

const savedKey = (memberId) => `creditcompass:current-taste:v${TASTE_VERSION}:${memberId}`;
export function readCurrentTaste(memberId) {
  if (memberId == null) return null;
  try {
    const value = JSON.parse(localStorage.getItem(savedKey(memberId)));
    return value?.version === TASTE_VERSION && isCompleteTasteAnswers(value.answers) ? value : null;
  } catch { return null; }
}

// 서버 연동 전 화면 검증용. 토큰/회원 상세정보는 저장하지 않는다.
export function saveCurrentTaste(memberId, answers) {
  if (memberId == null || !isCompleteTasteAnswers(answers)) throw new Error('저장할 취향을 확인해주세요.');
  const record = { version: TASTE_VERSION, answers: [...answers], savedAt: new Date().toISOString() };
  localStorage.setItem(savedKey(memberId), JSON.stringify(record));
  return record;
}
