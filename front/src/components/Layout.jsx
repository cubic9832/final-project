import { useEffect } from 'react';
import { Outlet, useLocation } from 'react-router-dom';
import styled from 'styled-components';
import Header from './Header';

const Main = styled.main`
  max-width: var(--layout-max-width);
  margin: 0 auto;
  padding: var(--space-24) var(--layout-gutter);
`;

export default function Layout() {
  const { pathname } = useLocation();
  const home = pathname === '/';

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
    </>
  );
}
