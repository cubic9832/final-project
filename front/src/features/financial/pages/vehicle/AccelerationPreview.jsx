import './AccelerationPreview.css';

const examples = {
  0: { seconds: '12초 이상', duration: 12, title: '속도를 천천히 높이는 성향', description: '빠른 출발보다는 여유 있게 속도가 올라가는 차를 선호해요.' },
  0.5: { seconds: '약 7초', duration: 7, title: '적당히 경쾌한 가속', description: '속도를 높일 때 답답하지 않은 중간 수준의 가속을 선호해요.' },
  1: { seconds: '약 4초', duration: 4, title: '짧은 시간에 속도를 높이는 성향', description: '출발할 때 빠르게 속도가 붙는 차를 선호해요.' },
};

export default function AccelerationPreview({ value }) {
  const example = examples[value];
  if (!example) return null;
  return <div className="acceleration-preview" aria-live="polite" aria-atomic="true">
    <div className="acceleration-preview-heading"><span>0–100km/h 시간 예시</span><strong>{example.seconds}</strong></div>
    <div className="acceleration-preview-track" aria-hidden="true"><span style={{ width: `${example.duration / 12 * 100}%` }} /></div>
    <div className="acceleration-preview-scale" aria-hidden="true"><span>0초</span><span>6초</span><span>12초</span></div>
    <h3>{example.title}</h3><p>{example.description}</p>
  </div>;
}
