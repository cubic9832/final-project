import { resolveTaste } from './serverTasteFlow.js';

const key = (memberId, version) => `creditcompass:member-taste-draft:${memberId}:v${version}`;

export function readMemberTasteDraft(memberId, catalog) {
  try {
    const value = JSON.parse(sessionStorage.getItem(key(memberId, catalog.version)));
    if (!value || !['intro', 'question', 'result'].includes(value.phase) || !Array.isArray(value.answers)
      || value.answers.length !== catalog.questionCount || !Number.isInteger(value.step) || value.step < 0 || value.step >= catalog.questionCount) return null;
    let empty = false;
    for (const answer of value.answers) {
      if (answer === null) empty = true;
      else if (empty || !Number.isInteger(answer) || answer < 0 || answer > 3) return null;
    }
    const flow = resolveTaste(catalog, value.answers);
    if (!flow.path[value.step] || (value.phase === 'result' && !flow.complete)) return null;
    return value;
  } catch { return null; }
}

export function writeMemberTasteDraft(memberId, version, draft) {
  try { sessionStorage.setItem(key(memberId, version), JSON.stringify(draft)); } catch { /* 임시 저장이 안 돼도 진행 가능 */ }
}
