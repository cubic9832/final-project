import { useEffect, useRef, useState } from 'react';
import { ChevronLeft, ChevronRight } from 'lucide-react';
import theme from '../../styles/theme';
import ProfilePresetCard from './ProfilePresetCard';

export default function ProfilePresetSlider({ presets, onSelect }) {
  const trackRef = useRef(null);
  const [edges, setEdges] = useState({ start: true, end: false });

  useEffect(() => {
    const track = trackRef.current;
    const updateEdges = () => setEdges({ start: track.scrollLeft <= 1, end: track.scrollLeft + track.clientWidth >= track.scrollWidth - 1 });
    const observer = new ResizeObserver(updateEdges);
    observer.observe(track);
    track.addEventListener('scroll', updateEdges, { passive: true });
    updateEdges();
    return () => { observer.disconnect(); track.removeEventListener('scroll', updateEdges); };
  }, []);

  function move(direction) {
    const track = trackRef.current;
    const card = track.firstElementChild;
    const gap = parseFloat(getComputedStyle(track).columnGap);
    track.scrollBy({ left: direction * (card.getBoundingClientRect().width + gap), behavior: window.matchMedia('(prefers-reduced-motion: reduce)').matches ? 'instant' : 'smooth' });
  }

  return (
    <section className="profile-preset-slider" aria-label="상황별 예시 프로필" aria-roledescription="슬라이드">
      <p className="profile-slider-hint">양옆 화살표를 눌러 나와 닮은 프로필을 찾아보세요</p>
      <div className="profile-slider-stage">
        <button className="profile-slider-arrow" type="button" aria-label="이전 프로필 보기" aria-controls="profile-preset-track" disabled={edges.start} onClick={() => move(-1)}><ChevronLeft size={theme.iconSize.lg} aria-hidden="true" /></button>
      <div className="profile-preset-track" id="profile-preset-track" ref={trackRef}>
        {presets.map((preset) => <ProfilePresetCard key={preset.id} preset={preset} onSelect={onSelect} />)}
      </div>
        <button className="profile-slider-arrow" type="button" aria-label="다음 프로필 보기" aria-controls="profile-preset-track" disabled={edges.end} onClick={() => move(1)}><ChevronRight size={theme.iconSize.lg} aria-hidden="true" /></button>
      </div>
    </section>
  );
}
