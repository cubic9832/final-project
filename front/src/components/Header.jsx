import { NavLink, useNavigate } from 'react-router-dom';
import styled from 'styled-components';
import { logout } from '../api/authApi';
import useAuthStore from '../stores/useAuthStore';
import ExploreMenu from './ExploreMenu';

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

// 로그인 후 우측 영역: "닉네임님"(마이페이지 링크) + 로그아웃 버튼
const AccountArea = styled.div`
  display: flex;
  align-items: center;
  gap: var(--space-12);
  font-size: var(--font-body);

  a {
    font-weight: 700;
    color: var(--color-primary);
  }

  a:hover {
    color: var(--color-blue-strong);
  }
`;

const LogoutButton = styled(LoginLink).attrs({ as: 'button', type: 'button' })`
  border: 0;
  cursor: pointer;
`;

export default function Header() {
  const navigate = useNavigate();
  const member = useAuthStore((state) => state.member); // 로그인 상태가 바뀌면 헤더가 다시 그려진다
  const initialized = useAuthStore((state) => state.initialized); // 새로고침 직후 로그인 복원이 끝났는지

  // 서버 로그아웃(refresh token 삭제)이 끝난 뒤 메인으로 이동한다
  async function handleLogout() {
    await logout();
    navigate('/');
  }

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
            <ExploreMenu />
          </ul>
        </Navigation>
        {/* 로그인 복원 중에는 비워 둔다 → 로그인한 사람에게 "로그인" 버튼이 잠깐 보였다 바뀌는 깜빡임 방지 */}
        {!initialized ? null : member ? (
          <AccountArea>
            <NavLink to="/mypage">{member.nickName}님</NavLink>
            <LogoutButton onClick={handleLogout}>로그아웃</LogoutButton>
          </AccountArea>
        ) : (
          <LoginLink to="/login">로그인</LoginLink>
        )}
      </HeaderContent>
    </HeaderWrapper>
  );
}
