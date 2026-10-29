const entries = [
  ['MPV', 'MPV · 다목적 차량', ['미니밴', '승합']],
  ['SUV', 'SUV · 스포츠 유틸리티 차량', []],
  ['MIDSIZE_SUV', '중형 SUV', ['중형 SUV']],
  ['SUBCOMPACT_SUV', '소형 SUV', ['소형 SUV']],
  ['COMPACT_SUV', '준중형 SUV', ['준중형 SUV']],
  ['LARGE_SUV', '대형 SUV', ['대형 SUV']],
  ['COMPACT_SEDAN', '준중형 세단', ['준중형 세단']],
  ['MIDSIZE_SEDAN', '중형 세단', ['중형 세단']],
  ['FULLSIZE_SEDAN', '대형 세단', ['대형 세단']],
  ['MINI', '경차', ['경차']],
  ['SEDAN', '세단', ['세단']],
  ['HYBRID', '하이브리드', ['HEV', '하이브리드']],
  ['MILD_HYBRID', '마일드 하이브리드', ['마일드 하이브리드']],
  ['PHEV', '플러그인 하이브리드', ['플러그인 하이브리드']],
  ['ELECTRIC', '전기차', ['EV', 'BEV', '전기차', '전기 SUV']],
  ['GASOLINE', '가솔린', ['가솔린', '휘발유']],
  ['DIESEL', '디젤', ['디젤', '경유']],
  ['LPG', 'LPG', []],
  ['RUNNING_COST', '예상 월 유지비', ['예상 월 유지비', '월 유지비']],
  ['EFFICIENCY', '복합연비', ['복합연비', '연비']],
];

const normalize = (value) => String(value ?? '').trim().toUpperCase();
const terms = new Map(entries.flatMap(([id, label, aliases]) =>
  [id, label, ...aliases].map((alias) => [normalize(alias), { id, label }])));

export function findGlossaryTerm(value) {
  return terms.get(normalize(value)) ?? null;
}

export function buildTermQuestion(term, context = '') {
  const location = context ? `지금 보고 있는 화면 정보: ${context.slice(0, 250)}.\n` : '';
  const name = /_(SUV|SEDAN)$/.test(term.id) ? `${term.id}(${term.label})` : term.label;
  return `${location}화면에 나온 ${name}의 쉬운 뜻을 알려주세요. 헷갈리기 쉬운 비슷한 용어가 있다면 차이도 설명해 주세요.`;
}
