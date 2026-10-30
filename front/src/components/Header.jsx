import { useState } from 'react';
import { NavLink, useNavigate } from 'react-router-dom';
import styled from 'styled-components';
import { logout } from '../features/auth/authApi';
import LogoutConfirmModal from '../features/auth/components/LogoutConfirmModal';
import useAuthStore from '../stores/useAuthStore';
import { showToast } from '../stores/useToastStore';

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

// 로고 칸 · 오른쪽 버튼 칸은 같은 비율(flex: 1)로 남는 폭을 나눠 가진다
// → 오른쪽 내용이 "로그인" 에서 "닉네임님 + 로그아웃" 으로 넓어져도 가운데 메뉴 위치가 바뀌지 않는다
const Side = styled.div`
  flex: 1 1 0;
  display: flex;
  justify-content: ${({ $end }) => ($end ? 'flex-end' : 'flex-start')};
  min-width: max-content;

  /* 태블릿 이하에서는 메뉴가 아래 줄로 내려가므로 가운데 맞춤이 필요 없다 → 원래 크기로 */
  @media (max-width: ${({ theme }) => theme.breakpoints.tablet}) {
    flex: 0 1 auto;
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

  const [isLogoutOpen, setIsLogoutOpen] = useState(false); // 로그아웃 확인 팝업 열림 여부

  // [로그아웃] 버튼 → 확인 팝업 → [로그아웃] 확인 시:
  // 서버 로그아웃(refresh token 삭제)이 끝난 뒤 팝업을 닫고 메인으로 이동, 공용 알림으로 결과를 알려 준다
  async function handleLogout() {
    await logout();
    setIsLogoutOpen(false);
    navigate('/');
    showToast('로그아웃되었습니다.');
  }

  return (
    <HeaderWrapper>
      <HeaderContent>
        <Side>
          <Brand to="/">CreditComPass</Brand>
        </Side>
        <Navigation aria-label="주 메뉴">
          <ul>
            <li>
              <NavLink to="/about">About Us</NavLink>
            </li>
            <li>
              <NavLink to="/financial">차량 맞춤 추천</NavLink>
            </li>
            <li>
              <NavLink to="/search">차량 찾기</NavLink>
            </li>
            <li><NavLink to="/vehicles/compare">차량 비교</NavLink></li>
            <li><NavLink to="/dream-car">드림카 플래너</NavLink></li>
          </ul>
        </Navigation>
        <Side $end>
          {/* 로그인 복원 중에는 비워 둔다 → 로그인한 사람에게 "로그인" 버튼이 잠깐 보였다 바뀌는 깜빡임 방지 */}
          {!initialized ? null : member ? (
            <AccountArea>
              <NavLink to="/mypage">{member.nickName}님</NavLink>
              <LogoutButton onClick={() => setIsLogoutOpen(true)}>로그아웃</LogoutButton>
            </AccountArea>
          ) : (
            <LoginLink to="/login">로그인</LoginLink>
          )}
        </Side>
      </HeaderContent>
      {isLogoutOpen && <LogoutConfirmModal onConfirm={handleLogout} onClose={() => setIsLogoutOpen(false)} />}
    </HeaderWrapper>
  );
}
