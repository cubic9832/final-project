import { getTasteScores, isValidTasteAnswers } from './tasteFlow.js';

export const isCompleteTasteAnswers = (answers) => isValidTasteAnswers(answers, true);

export function calculateTasteResult(answers) {
  if (!isCompleteTasteAnswers(answers)) throw new Error('모든 질문에 답해주세요.');
  const scores = getTasteScores(answers);
  const ranked = Object.keys(scores).sort((a, b) => scores[b] - scores[a]);
  const primary = ranked[0];
  return {
    primary,
    secondary: scores[ranked[1]] > 0 ? ranked[1] : null,
    tied: ranked.filter((key) => scores[key] === scores[primary]),
  };
}
