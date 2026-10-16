import { useState } from 'react';

export default function TasteVehicleCard({ vehicle }) {
  const [failed, setFailed] = useState(false);
  const [attempt, setAttempt] = useState(0);

  return (
    <li className="taste-vehicle-card">
      <div className="taste-vehicle-image">
        {failed ? (
          <div className="taste-vehicle-image-error" role="status">
            <p>차량 사진을 불러오지 못했어요.</p>
            <button type="button" className="taste-button taste-button-outline" onClick={() => { setFailed(false); setAttempt(attempt + 1); }}>다시 불러오기</button>
          </div>
        ) : (
          <img key={attempt} src={vehicle.image} alt={`${vehicle.name} 외관`} loading="lazy" onError={() => setFailed(true)} />
        )}
      </div>
      <div className="taste-vehicle-info"><p className="taste-caption">{vehicle.category}</p><h3>{vehicle.name}</h3></div>
    </li>
  );
}
