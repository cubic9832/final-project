import { NavLink } from 'react-router-dom';
import styled from 'styled-components';

const HeaderWrapper = styled.header`
  background: #fff;
  border-bottom: 1px solid #e5eaf2;
`;

const HeaderContent = styled.div`
  max-width: 1280px;
  margin: 0 auto;
  padding: 19px 32px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 24px;
  color: #193b64;

  @media (max-width: 650px) {
    padding: 18px 20px;
    flex-wrap: wrap;
    gap: 14px;
  }
`;

const Brand = styled(NavLink)`
  font-size: 17px;
  font-weight: 800;
  letter-spacing: -0.5px;
`;

const Navigation = styled.nav`
  ul {
    display: flex;
    align-items: center;
    gap: 26px;
    font-size: 12px;
    color: #68778b;
  }

  a:hover {
    color: #078579;
  }

  @media (max-width: 650px) {
    ul {
      gap: 17px;
      flex-wrap: wrap;
      font-size: 11px;
    }
  }
`;

const LoginLink = styled(NavLink)`
  padding: 6px 12px;
  border-radius: 6px;
  background: #edf3fa;
  color: #193b64;
  font-size: 12px;
  font-weight: 700;

  &:hover {
    background: #dfeaf7;
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
              <a href="/#intro">서비스 소개</a>
            </li>
            <li>
              <a href="/#financial">재무 진단</a>
            </li>
            <li>
              <a href="/#how-it-works">차량 찾기</a>
            </li>
            <li>
              <a href="/#analysis">분석 비교</a>
            </li>
          </ul>
        </Navigation>
        <LoginLink to="/login">로그인</LoginLink>
      </HeaderContent>
    </HeaderWrapper>
  );
}
