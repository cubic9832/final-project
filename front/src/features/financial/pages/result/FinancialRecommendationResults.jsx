import './FinancialRecommendationResults.css';

export default function FinancialRecommendationResults({ result }) {
  return <section className="result-card financial-recommendation-results" aria-labelledby="financial-recommendation-title">
    <h2 id="financial-recommendation-title">진단 조건에 따른 추천 차량</h2>
    <p>입력한 소득·지출·자산·대출과 이용목적을 바탕으로 선정한 차량 후보입니다.</p>
    {result.recommendations.length ? <ol className="financial-recommendation-grid">
      {result.recommendations.map((vehicle, index) => <li key={vehicle.labelCode}>
        <span>추천 {index + 1}</span><h3>{vehicle.model}</h3><p>{vehicle.body} · {vehicle.grade}</p>
        <dl><div><dt>모델 예측 확률</dt><dd>{(vehicle.probability * 100).toFixed(1)}%</dd></div></dl>
      </li>)}
    </ol> : <p>추천 가능한 차량이 없습니다. 진단 조건을 확인해 주세요.</p>}
    <p className="financial-recommendation-caption">합성 데이터로 학습한 참고 추천입니다. 확률은 구매 적합도나 구매 가능 확률이 아닙니다. 차량별 실제 가격과 구매 가능 여부는 별도로 확인해 주세요.</p>
  </section>;
}
