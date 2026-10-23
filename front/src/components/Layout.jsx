import { useEffect } from 'react';
import { Outlet, useLocation } from 'react-router-dom';
import styled from 'styled-components';
import GlobalToast from './GlobalToast';
import Header from './Header';

const Main = styled.main`
  max-width: var(--layout-max-width);
  margin: 0 auto;
  padding: var(--space-24) var(--layout-gutter);
`;

export default function Layout() {
  const { pathname } = useLocation();
  const home = pathname === '/' || pathname === '/about';

  useEffect(() => {
    window.scrollTo({ top: 0, behavior: 'instant' });
  }, [pathname]);

  return (
    <>
      <Header />
      {home ? (
        <main>
          <Outlet />
        </main>
      ) : (
        <Main>
          <Outlet />
        </Main>
      )}
      {/* 공용 알림 표시 자리 — 어느 화면에서든 showToast('…') 로 띄운다 */}
      <GlobalToast />
    </>
  );
}
