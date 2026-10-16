import { useEffect, useRef, useState } from 'react';
import { NavLink } from 'react-router-dom';
import { ChevronDown } from 'lucide-react';
import styled from 'styled-components';

const Menu = styled.li`
  position: relative;
  > button {
    display: inline-flex;
    align-items: center;
    gap: var(--space-4);
    min-height: 40px;
    border: 0;
    background: transparent;
    color: inherit;
  }
  > button[aria-expanded='true'], > button:hover {
    color: var(--color-blue-strong);
  }
  .explore-dropdown {
    position: absolute;
    z-index: 30;
    top: 100%;
    left: -16px;
    min-width: 180px;
    padding: var(--space-8);
    background: var(--color-surface);
    border: 1px solid var(--color-border);
    border-radius: var(--radius-sm);
    box-shadow: 0 8px 24px #20396014;
  }
  .explore-dropdown a {
    display: flex;
    align-items: center;
    min-height: 40px;
    padding: var(--space-8) var(--space-16);
    border-radius: var(--radius-sm);
    white-space: nowrap;
  }
  .explore-dropdown a:hover, .explore-dropdown a.active {
    color: var(--color-blue-strong);
    background: var(--color-blue-tint);
  }
`;

export default function ExploreMenu() {
  const [open, setOpen] = useState(false);
  const root = useRef(null);
  const trigger = useRef(null);

  useEffect(() => {
    function dismiss(event) {
      if (!root.current?.contains(event.target)) setOpen(false);
    }
    function escape(event) {
      if (event.key === 'Escape' && open) {
        setOpen(false);
        trigger.current?.focus();
      }
    }
    document.addEventListener('pointerdown', dismiss);
    document.addEventListener('keydown', escape);
    return () => {
      document.removeEventListener('pointerdown', dismiss);
      document.removeEventListener('keydown', escape);
    };
  }, [open]);

  return (
    <Menu ref={root} onMouseEnter={() => setOpen(true)} onMouseLeave={() => setOpen(false)}
      onBlur={(event) => { if (!event.currentTarget.contains(event.relatedTarget)) setOpen(false); }}>
      <button ref={trigger} type="button" aria-expanded={open} aria-controls="explore-navigation"
        onClick={() => setOpen((value) => !value)}
        onKeyDown={(event) => {
          if (event.key === 'ArrowDown') {
            event.preventDefault();
            setOpen(true);
            requestAnimationFrame(() => root.current?.querySelector('a')?.focus());
          }
        }}>
        자동차 알아보기 <ChevronDown size={16} aria-hidden="true" />
      </button>
      {open && <div id="explore-navigation" className="explore-dropdown">
        <NavLink to="/vehicles/compare" onClick={() => setOpen(false)}>차량 비교</NavLink>
        <NavLink to="/taste-test" onClick={() => setOpen(false)}>취향 테스트</NavLink>
      </div>}
    </Menu>
  );
}
