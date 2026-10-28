import { useEffect } from 'react';
import { Outlet, useLocation } from 'react-router-dom';
import styled from 'styled-components';
import GlobalToast from './GlobalToast';
import Header from './Header';
import ChatWidget from '../features/chatbot/ChatWidget';

const Main = styled.main`
  max-width: var(--layout-max-width);
  margin: 0 auto;
  padding: var(--space-24) var(--layout-gutter);
`;

// 보완 11: children 을 주면 Outlet 대신 그것을 보여 준다 (RequireAdmin 이 관리자가 아닌 사람에게 404 화면을 헤더와 함께 보여 줄 때)
export default function Layout({ children }) {
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
          {children ?? <Outlet />}
        </main>
      ) : (
        <Main>
          {children ?? <Outlet />}
        </Main>
      )}
      {/* 공용 알림 표시 자리 — 어느 화면에서든 showToast('…') 로 띄운다 */}
      <GlobalToast />
      <ChatWidget />
    </>
  );
}
