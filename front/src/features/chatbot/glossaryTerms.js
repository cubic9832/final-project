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
