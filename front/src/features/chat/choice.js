// 8단계: 선택지 + [기타] 직접 쓰기 (ChoiceWithOther 와 같이 쓴다)
export const OTHER = '기타';

// 고른 값 → 서버로 보낼 글 ("기타" 면 직접 쓴 글, 비었으면 null = 아직 못 고름)
export const choiceText = (choice, other) => (choice === OTHER ? other.trim() || null : choice || null);
