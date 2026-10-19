export default function RecommendationResults({ result }) {
  if (!result) return <section className="recommendation-card recommendation-placeholder" aria-label="추천 결과 안내">
    <h2>나에게 맞는 차량 후보</h2><p>조건을 입력하고 추천을 요청하면 차량 후보 3대를 확인할 수 있습니다.</p>
  </section>;
  return <section className="recommendation-results" aria-labelledby="recommendation-results-title">
    <div className="recommendation-result-heading"><h2 id="recommendation-results-title">추천 차량 후보</h2>
      <span>{result.segment === 'domestic-car' ? '국내차' : '수입차'} · {result.recommendations.length}대</span></div>
    {result.recommendations.length ? <ol className="recommendation-result-grid">
      {result.recommendations.map((vehicle, index) => <li className="recommendation-card" key={vehicle.labelCode}>
        <span className="recommendation-rank">추천 {index + 1}</span><h3>{vehicle.model}</h3>
        <p>{vehicle.body} · {vehicle.grade}</p>
        <dl><div><dt>모델 예측 확률</dt><dd>{(vehicle.probability * 100).toFixed(1)}%</dd></div></dl>
      </li>)}
    </ol> : <p className="recommendation-card">추천 가능한 차량이 없습니다. 입력 조건을 확인해 주세요.</p>}
    <p className="recommendation-caption">확률은 모델이 차량 라벨에 배정한 값입니다. 구매 적합도나 구매 가능 확률을 의미하지 않습니다.</p>
  </section>;
}
