import { Target } from 'lucide-react';
import theme from '../../../styles/theme';
import './DreamCarPageHeader.css';

export default function DreamCarPageHeader({ eyebrow, title, description }) {
  return <header className="dream-car-page-header"><span><Target size={theme.iconSize.sm} aria-hidden />{eyebrow}</span><h1>{title}</h1><p>{description}</p></header>;
}
