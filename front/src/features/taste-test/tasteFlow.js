import { TASTE_QUESTION_COUNT, tasteTypes, firstQuestion, purposeQuestions, detailQuestions, concernQuestion, supportQuestions, exteriorQuestion, interiorQuestion, confirmationQuestions } from './tasteQuestions.js';

export const emptyTasteAnswers = () => Array(TASTE_QUESTION_COUNT).fill(null);
const isAnswer = (answer) => Number.isInteger(answer) && answer >= 0 && answer < 4;
const leadingType = (scores) => Object.keys(tasteTypes).sort((a, b) => (scores[b] ?? 0) - (scores[a] ?? 0))[0];

export function getTasteQuestion(step, answers) {
  switch (step) {
    case 0: return firstQuestion;
    case 1: return purposeQuestions[answers[0]] ?? null;
    case 2: {
      const choice = purposeQuestions[answers[0]]?.options[answers[1]];
      return choice ? detailQuestions[leadingType(choice.weights)] : null;
    }
    case 3: return concernQuestion;
    case 4: return supportQuestions[answers[3]] ?? null;
    case 5: return exteriorQuestion;
    case 6: return interiorQuestion;
    case 7: return answers.slice(0, 7).every(isAnswer) ? confirmationQuestions[leadingType(getTasteScores(answers.slice(0, 7)))] : null;
    default: return null;
  }
}

export function getTasteScores(answers) {
  const scores = Object.fromEntries(Object.keys(tasteTypes).map((key) => [key, 0]));
  for (let step = 0; step < answers.length; step++) {
    const choice = getTasteQuestion(step, answers)?.options[answers[step]];
    if (!choice) break;
    for (const [key, weight] of Object.entries(choice.weights)) scores[key] += weight;
  }
  return scores;
}

// 앞선 답변이 바뀌면 다른 분기의 답을 재사용하지 않도록 이후 답변을 초기화한다.
export function selectTasteAnswer(answers, step, answer) {
  if (!Number.isInteger(step) || step < 0 || step >= TASTE_QUESTION_COUNT || !isAnswer(answer)
    || answers.slice(0, step).some((value) => !isAnswer(value)) || !getTasteQuestion(step, answers)) return answers;
  if (answers[step] === answer) return answers;
  return answers.map((value, index) => index < step ? value : index === step ? answer : null);
}

export function isValidTasteAnswers(answers, complete = false) {
  if (!Array.isArray(answers) || answers.length !== TASTE_QUESTION_COUNT) return false;
  let unanswered = false;
  for (let step = 0; step < TASTE_QUESTION_COUNT; step++) {
    if (!Object.hasOwn(answers, step)) return false;
    if (answers[step] === null) { unanswered = true; if (complete) return false; }
    else if (unanswered || !isAnswer(answers[step]) || !getTasteQuestion(step, answers)) return false;
  }
  return true;
}
