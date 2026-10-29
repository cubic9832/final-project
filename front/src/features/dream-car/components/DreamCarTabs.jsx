import { NavLink } from 'react-router-dom';
import './DreamCarTabs.css';

export default function DreamCarTabs() {
  return <nav className="dream-car-tabs" aria-label="드림카 계획 화면">
    <NavLink to="/dream-car" end>구매 계획</NavLink>
    <NavLink to="/dream-car/progress">저축 실행 현황</NavLink>
  </nav>;
}
