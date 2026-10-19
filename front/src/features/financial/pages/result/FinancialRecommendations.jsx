import { useEffect, useMemo, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { buildFinancialRecommendation } from '../../buildFinancialRecommendation.js';
import { getFinancialRecommendations } from '../../financialRecommendationApi.js';
import './FinancialRecommendations.css';

export default function FinancialRecommendations({ diagnosis }) {
  const navigate = useNavigate();
  const { request, errors } = useMemo(() => buildFinancialRecommendation(diagnosis ?? {}), [diagnosis]);
  const [result, setResult] = useState(null);
  const [failure, setFailure] = useState('');
  const [attempt, setAttempt] = useState(0);
  const [loading, setLoading] = useState(Boolean(request));

  useEffect(() => {
    if (!request) return;
    const controller = new AbortController();
    getFinancialRecommendations(request.segment, request.profile, controller.signal).then((data) => {
      if (!controller.signal.aborted) { setResult(data); setLoading(false); }
    }).catch((error) => {
      if (!controller.signal.aborted) {
        setFailure(error.response?.data?.detail ?? '차량 추천에 연결하지 못했습니다. 재무 분석 결과는 유지됩니다. 잠시 후 다시 시도해 주세요.');
        setLoading(false);
      }
    });
    return () => controller.abort();
  }, [request, attempt]);

  function retry() {
    setLoading(true);
    setFailure('');
    setAttempt((value) => value + 1);
  }

  return <section className="financial-recommendations result-card" aria-labelledby="financial-recommendations-title" aria-busy={loading}>
    <h2 id="financial-recommendations-title">진단 조건에 따른 추천 차량</h2>
    <p className="financial-recommendation-description">입력한 재무정보와 이용목적을 바탕으로 선정한 {request?.segment === 'imported-car' ? '수입차' : '국내차'} 후보입니다.</p>
    {!request && <div className="financial-recommendation-missing"><p>추천에 필요한 정보가 부족합니다. 진단 정보를 보완하면 예산 분석과 함께 추천받을 수 있습니다.</p>
      <ul>{errors.map(({ label }, index) => <li key={`${label}-${index}`}>{label}</li>)}</ul>
      {[...new Set(errors.map(({ path }) => path))].map((path) => <button key={path} type="button"
        onClick={() => navigate(path, { state: { ...diagnosis, reviewReturn: true } })}>
        {path === '/financial/assets' ? '자산·부채 수정' : path === '/financial/vehicle' ? '차량 조건 수정' : '소득·기본 정보 수정'}</button>)}
    </div>}
    <div aria-live="polite">
      {request && loading && <p role="status">진단 정보를 바탕으로 추천 차량을 분석하고 있습니다.</p>}
      {failure && <div role="alert"><p>{failure}</p><button type="button" onClick={retry} disabled={loading}>차량 추천 다시 시도</button></div>}
      {result && !loading && <>{result.recommendations.length ? <ol className="financial-recommendation-grid">{result.recommendations.map((vehicle, index) =>
        <li key={vehicle.labelCode}><span>추천 {index + 1}</span><h3>{vehicle.model}</h3><p>{vehicle.body} · {vehicle.grade}</p>
          <dl><div><dt>모델 예측 확률</dt><dd>{(vehicle.probability * 100).toFixed(1)}%</dd></div></dl></li>)}
      </ol> : <p>추천 가능한 차량이 없습니다. 진단 조건을 확인해 주세요.</p>}
      <p className="financial-recommendation-caption">합성 데이터에 기반한 참고 추천입니다. 예측 확률은 구매 적합도나 구매 가능 확률이 아닙니다. 위 예산은 별도 계산 결과이며, 추천 후보의 실제 가격·구매 가능 여부는 따로 확인해야 합니다.</p></>}
    </div>
  </section>;
}
