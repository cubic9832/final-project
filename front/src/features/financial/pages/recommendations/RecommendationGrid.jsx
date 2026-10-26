import { useLayoutEffect, useRef } from 'react';
import { buildRecommendationView } from './buildRecommendationView.js';
import RecommendationCard from './RecommendationCard.jsx';

export default function RecommendationGrid({ candidates, preferences, views, comparisonIds = [], onToggleComparison, rankOffset = 0 }) {
  const presented = views ?? buildRecommendationView({ recommendations: candidates });
  const gridRef = useRef(null);

  useLayoutEffect(() => {
    const grid = gridRef.current;
    const measures = grid.querySelectorAll('[data-recommendation-measure]');
    const align = () => {
      const stacked = window.matchMedia('(max-width: 768px)').matches;
      for (const group of ['summary', 'metadata', 'score', 'conditions', 'cost']) {
        const heights = [...grid.querySelectorAll(`[data-recommendation-measure="${group}"]`)]
          .map(element => element.getBoundingClientRect().height);
        const height = stacked ? 0 : Math.ceil(Math.max(0, ...heights));
        grid.style.setProperty(`--recommendation-${group}-height`, `${height}px`);
      }
    };
    align();
    const observer = new ResizeObserver(align);
    observer.observe(grid);
    measures.forEach(element => observer.observe(element));
    return () => observer.disconnect();
  }, [candidates, preferences]);

  return <ol className="financial-recommendations-grid" start={rankOffset + 1} ref={gridRef}>
    {candidates.map((candidate, index) => <RecommendationCard key={candidate.vehicle.id} candidate={candidate} rank={rankOffset + index + 1} view={presented.find(view => view.id === candidate.vehicle.id)} comparisonSelected={comparisonIds.includes(candidate.vehicle.id)} comparisonFull={comparisonIds.length >= 3} onToggleComparison={onToggleComparison} />)}
  </ol>;
}
