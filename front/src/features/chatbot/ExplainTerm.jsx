import { useId } from 'react';
import { CircleHelp } from 'lucide-react';
import theme from '../../styles/theme';
import { findGlossaryTerm } from './glossaryTerms';
import useChatStore from './useChatStore';
import useAuthStore from '../../stores/useAuthStore';
import './ExplainTerm.css';

export default function ExplainTerm({ term, children }) {
  const tooltipId = useId();
  const explain = useChatStore((state) => state.explain);
  const entry = findGlossaryTerm(term);
  const member = useAuthStore((state) => state.member);
  if (!entry || !member) return children ?? term;
  return <span className="explain-term">
    <button type="button" className="explain-term-button" aria-describedby={tooltipId}
      aria-label={`${children ?? term} 뜻을 콤파에서 확인하기`} aria-controls="chat-panel"
      onClick={(event) => explain(entry, event.currentTarget)}>
      {children ?? term}<CircleHelp size={theme.iconSize.sm} aria-hidden="true" />
    </button>
    <span className="explain-term-tooltip" role="tooltip" id={tooltipId}>콤파에서 뜻 확인하기 · AI 횟수 차감 없음</span>
  </span>;
}
