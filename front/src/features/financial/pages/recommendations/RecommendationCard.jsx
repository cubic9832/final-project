import { useState } from 'react';
import { Car } from 'lucide-react';
import theme from '../../../../styles/theme.js';
import { recommendationImages } from './recommendationImages.js';
import { buildRecommendationDetails } from './buildRecommendationDetails.js';

export default function RecommendationCard({ vehicle, rank, diagnosis }) {
  const [failedUrl, setFailedUrl] = useState(null);
  const image = recommendationImages[vehicle.labelCode];
  const source = image?.src || vehicle.imageUrl;
  const showImage = source && failedUrl !== source;
  const details = buildRecommendationDetails(vehicle, diagnosis, rank);

  return <li className="financial-recommendation-card">
    <div className="financial-recommendation-media">
      <span className="financial-recommendation-rank">추천 {rank}</span>
      {showImage ? <img src={source} alt={image?.alt || `${vehicle.model} 예시 이미지`}
        loading="lazy" decoding="async" onError={() => setFailedUrl(source)} />
        : <div className="financial-recommendation-image-placeholder">
          <Car size={theme.iconSize.lg} aria-hidden="true" /><span>차량 이미지 준비 중</span>
        </div>}
    </div>
    <div className="financial-recommendation-card-body">
      <p className="financial-recommendation-category">{details.brand}</p>
      <h2>{vehicle.model}</h2>
      <dl className="financial-recommendation-specs" aria-label={`${vehicle.model} 주요 정보`}>
        <div><dt>차체</dt><dd>{vehicle.body || '확인 필요'}</dd></div>
        <div><dt>차급</dt><dd>{vehicle.grade || '확인 필요'}</dd></div>
      </dl>
      <section className="financial-recommendation-reasons" aria-label={`${vehicle.model} 추천 사유`}>
        <h3>추천 사유</h3>
        <ul>{details.reasons.map(reason => <li key={reason.title}>
          <strong>{reason.title}</strong><p>{reason.description}</p>
        </li>)}</ul>
        <p className="financial-recommendation-reason-note">차량 특징은 차체·이용목적 기준 참고 설명입니다. 모델의 개별 판단 근거를 뜻하지 않습니다.</p>
      </section>
      <dl className="financial-recommendation-probability"><div><dt>모델 예측 확률</dt><dd>{(vehicle.probability * 100).toFixed(1)}<span>%</span></dd></div></dl>
    </div>
  </li>;
}
