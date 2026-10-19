import { useState } from 'react';
import { Car } from 'lucide-react';
import theme from '../../../../styles/theme.js';
import { recommendationImages } from './recommendationImages.js';

export default function RecommendationCard({ vehicle, rank }) {
  const [failedUrl, setFailedUrl] = useState(null);
  const image = recommendationImages[vehicle.labelCode];
  const source = vehicle.imageUrl || image?.src;
  const showImage = source && failedUrl !== source;

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
      <p className="financial-recommendation-category">{vehicle.body} · {vehicle.grade}</p>
      <h2>{vehicle.model}</h2>
      <p className="financial-recommendation-card-description">입력하신 재무 조건과 이용목적으로 선정한 후보</p>
      <dl><div><dt>모델 예측 확률</dt><dd>{(vehicle.probability * 100).toFixed(1)}<span>%</span></dd></div></dl>
    </div>
  </li>;
}
