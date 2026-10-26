export default function CandidateComparisonTable({ views }) {
  const rows = [
    ['차량 가격', view => view.purchasePrice], ['예상 월 유지비', view => view.monthlyCost],
    ['구매 후 남는 예금', view => view.cashRemaining], ['유지비 지출 후 월 잔여금', view => view.monthlyRemaining],
    ['연료', view => view.fuel], ['차량 길이', view => view.length], ['승차 정원', view => view.seats],
    ['맞는 선호', view => view.matches.map(item => item.text).join(' ') || (view.evidence ? '일치가 확인된 지정 선호 없음' : '조건별 근거 미제공')],
    ['조정이 필요한 선호', view => [...view.mismatches, ...view.unknowns].map(item => item.text).join(' ') || (view.evidence ? '확인된 불일치 없음' : '조건별 근거 미제공')],
  ];
  return <div className="candidate-comparison-table-wrap" tabIndex={0} role="region" aria-label="추천 후보 공통 지표 비교표">
    <table className="candidate-comparison-table"><caption>추천 차량의 동일한 사양과 비용 비교</caption>
      <thead><tr><th scope="col">비교 항목</th>{views.map(view => <th scope="col" key={view.id}>{view.candidate.vehicle.brand} {view.candidate.vehicle.model}<small>{view.candidate.vehicle.trim}</small></th>)}</tr></thead>
      <tbody>{rows.map(([label, value]) => <tr key={label}><th scope="row">{label}</th>{views.map(view => <td key={view.id}>{value(view)}</td>)}</tr>)}</tbody>
    </table>
  </div>;
}
