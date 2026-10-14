export function reorderPriorities(items, source, target) {
  const from = items.indexOf(source);
  const to = items.indexOf(target);
  if (from < 0 || to < 0 || from === to) return items;
  const reordered = [...items];
  reordered.splice(from, 1);
  reordered.splice(to, 0, source);
  return reordered;
}
