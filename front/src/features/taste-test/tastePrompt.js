import { getCurrentTaste } from './tasteApi';

// 보완 11: 로그인할 때마다 취향 테스트로 안내 — 테스트를 끝냈거나(저장된 취향이 있음) "나중에 하기"를 누를 때까지
// "나중에 하기"는 회원 번호별로 이 브라우저에 기억한다 (다른 기기에서는 한 번 더 안내될 수 있다 — 서버 저장은 하지 않음)
const dismissedKey = (memberId) => `taste-prompt-dismissed:${memberId}`;

export function dismissTastePrompt(memberId) {
  if (memberId == null) return;
  try {
    localStorage.setItem(dismissedKey(memberId), '1');
  } catch {
    // 저장소를 못 쓰는 브라우저(사생활 보호 모드 등) — 다음 로그인 때 다시 안내될 뿐이다
  }
}

// 로그인 직후 갈 곳: 취향 테스트를 아직 안 했고 "나중에 하기"도 안 눌렀으면 /taste-test, 아니면 원래 가려던 곳
export async function afterLoginPath(memberId, fallback) {
  try {
    if (localStorage.getItem(dismissedKey(memberId))) return fallback;
    const taste = await getCurrentTaste();
    return taste ? fallback : '/taste-test';
  } catch {
    return fallback; // 확인이 실패하면 안내하지 않고 원래대로 (로그인 흐름을 막지 않는다)
  }
}
