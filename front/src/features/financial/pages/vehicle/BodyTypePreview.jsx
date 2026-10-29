const bodyExamples = {
  SEDAN: { image: 'avante.webp', model: '현대 아반떼', description: '지붕 뒤로 트렁크가 따로 이어지는 형태예요.' },
  SUV: { image: 'sportage.webp', model: '기아 스포티지', description: '차체가 높고, 뒷좌석 뒤로 짐 공간이 이어지는 형태예요.' },
  HATCHBACK: { image: 'morning.webp', model: '기아 모닝', description: '뒤가 짧고, 뒷유리와 트렁크 문이 함께 위로 열리는 형태예요.' },
  WAGON: { image: 'models/g70-shooting-brake-front.webp', model: '제네시스 G70 슈팅 브레이크', description: '세단처럼 낮은 차체에 지붕과 짐 공간을 뒤로 길게 늘린 형태예요.' },
  MPV: { image: 'models/carnival.webp', model: '기아 카니발', description: '여러 사람이 타기 좋게 실내를 넓게 만든 미니밴·승합 형태예요.' },
  BOX: { image: 'ray.webp', model: '기아 레이', description: '지붕이 높고 옆모습이 상자처럼 반듯한 형태예요.' },
};

export default function BodyTypePreview({ value, label }) {
  const example = bodyExamples[value];

  return <div className="vehicle-body-preview" aria-live="polite" aria-atomic="true">
    {example ? <>
      <div className="vehicle-body-preview-image">
        <img src={`/images/recommendations/${example.image}`} alt={`${label} 형태 예시: ${example.model}`} />
      </div>
      <div className="vehicle-body-preview-copy">
        <h3>{label} · 차량 예시</h3>
        <p>{example.description}</p>
        <small>예시: {example.model} · 실제 추천 차량은 달라질 수 있어요.</small>
      </div>
    </> : <p>{value === 'OTHER' ? '해치백·왜건·미니밴·픽업·박스카를 함께 비교해요.' : '차체 형태에 제한 없이 비교해요.'}</p>}
  </div>;
}
