import { NavLink } from 'react-router-dom';
import styled from 'styled-components';

const HeaderWrapper = styled.header`
  background: var(--color-surface);
  border-bottom: 1px solid var(--color-border);
`;

const HeaderContent = styled.div`
  max-width: var(--layout-max-width);
  margin: 0 auto;
  padding: var(--space-16) var(--layout-gutter);
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: var(--space-24);
  color: var(--color-primary);

  @media (max-width: ${({ theme }) => theme.breakpoints.tablet}) {
    flex-wrap: wrap;
    gap: var(--space-16);
  }
`;

const Brand = styled(NavLink)`
  font-size: var(--font-subtitle);
  font-weight: 800;
  letter-spacing: -0.5px;
`;

const Navigation = styled.nav`
  ul {
    display: flex;
    align-items: center;
    gap: var(--space-24);
    font-size: var(--font-body);
    color: var(--color-muted);
  }

  a:hover {
    color: var(--color-blue-strong);
  }

  @media (max-width: ${({ theme }) => theme.breakpoints.tablet}) {
    order: 3;
    width: 100%;

    ul {
      gap: var(--space-16);
      flex-wrap: wrap;
    }
  }
`;

const LoginLink = styled(NavLink)`
  display: inline-flex;
  align-items: center;
  min-height: var(--layout-control-height);
  padding: 0 var(--space-16);
  border-radius: var(--radius-sm);
  background: var(--color-blue-tint);
  color: var(--color-primary);
  font-size: var(--font-body);
  font-weight: 700;

  &:hover {
    background: var(--color-border);
  }
`;

export default function Header() {
  return (
    <HeaderWrapper>
      <HeaderContent>
        <Brand to="/">CreditComPass Auto</Brand>
        <Navigation aria-label="주 메뉴">
          <ul>
            <li>
              <NavLink to="/about">About Us</NavLink>
            </li>
            <li>
              <NavLink to="/financial">재무 진단</NavLink>
            </li>
            <li>
              <NavLink to="/search">차량 찾기</NavLink>
            </li>
            <li>
              <NavLink to="/predict">차량 추천</NavLink>
            </li>
            <li>
              <NavLink to="/vehicles/compare">차량 비교</NavLink>
            </li>
          </ul>
        </Navigation>
        <LoginLink to="/login">로그인</LoginLink>
      </HeaderContent>
    </HeaderWrapper>
  );
}
