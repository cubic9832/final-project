import { useId } from 'react';
import { CircleHelp } from 'lucide-react';
import theme from '../../styles/theme';
import { findGlossaryTerm } from './glossaryTerms';
import useChatStore from './useChatStore';
import './ExplainTerm.css';

export default function ExplainTerm({ term, children, context = '' }) {
  const tooltipId = useId();
  const explain = useChatStore((state) => state.explain);
  const entry = findGlossaryTerm(term);
  if (!entry) return children ?? term;
  return <span className="explain-term">
    <button type="button" className="explain-term-button" aria-describedby={tooltipId}
      aria-label={`${children ?? term} 뜻을 콤파에게 물어보기`} aria-controls="chat-panel"
      onClick={(event) => explain(entry, context, event.currentTarget)}>
      {children ?? term}<CircleHelp size={theme.iconSize.sm} aria-hidden="true" />
    </button>
    <span className="explain-term-tooltip" role="tooltip" id={tooltipId}>콤파에게 물어보기</span>
  </span>;
}
