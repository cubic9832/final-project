import { Outlet, useLocation } from 'react-router-dom';
import styled from 'styled-components';
import Header from './Header';

const Main = styled.main`
  max-width: var(--layout-max-width);
  margin: 0 auto;
  padding: var(--space-24) var(--layout-gutter);
`;

export default function Layout() {
  const home = useLocation().pathname === '/';

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
