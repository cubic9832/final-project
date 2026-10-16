import { Link } from 'react-router-dom';
import { useEffect, useRef } from 'react';
import { tasteTypes } from './tasteQuestions';
import { tasteVehicleExamples } from './tasteVehicleExamples';
import TasteVehicleCard from './TasteVehicleCard';

export default function TasteResult({ result, onSave, onRestart, saved, notice }) {
  const type = tasteTypes[result.primary];
  const title = useRef(null);
  useEffect(() => { title.current?.focus({ preventScroll: true }); }, []);
  return (
    <div className="taste-result">
      <section className="taste-result-hero taste-card" aria-labelledby="taste-result-title">
        <p className="taste-eyebrow">나의 첫 차 취향</p>
        <h1 ref={title} tabIndex={-1} id="taste-result-title">{type.name}</h1>
        <p className="taste-result-description">{type.description}</p>
        {result.secondary && <p className="taste-secondary">보조 취향 · {tasteTypes[result.secondary].name}</p>}
        {result.tied.length > 1 && <p className="taste-muted">{result.tied.map((key) => tasteTypes[key].name).join(' · ')} 성향이 같은 점수로 나타났어요. 한 가지 유형으로 단정하지 않아도 괜찮아요.</p>}
        <ul className="taste-tags">{type.tags.map((tag) => <li key={tag}>{tag}</li>)}</ul>
        <p className="taste-caption">구매 가능 여부가 아닌, 답변에 따른 선호도 탐색 결과입니다.</p>
      </section>
      <section className="taste-card taste-candidates">
        <h2>함께 살펴볼 차종</h2>
        <p className="taste-muted">취향에 맞춰 살펴볼 대표 모델이에요.</p>
        <ul className="taste-vehicle-grid">{tasteVehicleExamples[result.primary].map((vehicle) => <TasteVehicleCard key={vehicle.name} vehicle={vehicle} />)}</ul>
        <Link className="taste-button taste-button-outline" to="/search">차량 찾기에서 살펴보기</Link>
      </section>
      <div className="taste-result-actions"><button type="button" className="taste-button taste-button-cta" onClick={onSave}>{saved ? '현재 취향 다시 저장' : '현재 취향으로 저장'}</button><button type="button" className="taste-button taste-button-outline" onClick={onRestart}>다시 테스트하기</button></div>
      <p className="taste-notice" role="status">{notice}</p>
    </div>
  );
}
