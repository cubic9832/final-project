import { Outlet, useLocation } from 'react-router-dom';
import styled from 'styled-components';
import Header from './Header';

const Main = styled.main`
  max-width: ${({ theme }) => theme.maxWidth};
  margin: 0 auto;
  padding: 24px 16px;
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
