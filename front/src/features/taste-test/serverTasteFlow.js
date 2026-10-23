// 질문·선택지·분기·가중치는 서버의 공개 중인 DB 버전에서 받는다.
export function leadingTaste(scores) {
  return Object.keys(scores).sort((a, b) => scores[b] - scores[a])[0];
}

export function resolveTaste(catalog, answers) {
  const scores = Object.fromEntries(Object.keys(catalog.types).map((key) => [key, 0]));
  const path = [];
  let question = catalog.questions.find((item) => item.initial && item.step === 1);
  for (let step = 0; step < catalog.questionCount; step++) {
    if (!question || question.step !== step + 1 || question.options.length !== 4) throw new Error('질문 구성을 확인해 주세요.');
    path.push(question);
    const answer = answers[step];
    if (answer == null) return { path, scores, complete: false };
    if (!Number.isInteger(answer) || !question.options[answer]) throw new Error('선택한 답변을 확인해 주세요.');
    const option = question.options[answer];
    for (const [key, weight] of Object.entries(option.weights)) scores[key] += weight;
    if (step === catalog.questionCount - 1) break;
    const rule = catalog.rules.find((item) => item.sourceId === question.id
      && (item.optionId == null || item.optionId === option.id)
      && (item.leadingType == null || item.leadingType === leadingTaste(scores)));
    question = catalog.questions.find((item) => item.id === rule?.nextId);
  }
  const ranked = Object.keys(scores).sort((a, b) => scores[b] - scores[a]);
  return { path, scores, complete: true, result: { primary: ranked[0], secondary: scores[ranked[1]] > 0 ? ranked[1] : null,
    tied: ranked.filter((key) => scores[key] === scores[ranked[0]]) } };
}

export function savedTasteAnswers(catalog, record) {
  if (!record || record.version !== catalog.version || record.answers.length !== catalog.questionCount) return null;
  const answers = Array(catalog.questionCount).fill(null);
  for (let step = 0; step < answers.length; step++) {
    const question = resolveTaste(catalog, answers).path[step];
    if (question?.id !== record.answers[step].questionId) return null;
    const index = question.options.findIndex((option) => option.id === record.answers[step].optionId);
    if (index < 0) return null;
    answers[step] = index;
  }
  return answers;
}
