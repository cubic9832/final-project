import { Link, useNavigate } from 'react-router-dom';
import './NotFound.css';

// 없는 주소(404) 화면. 보완 11: 관리자가 아닌 사람이 관리자 주소(/console)에 들어와도 이 화면이 똑같이 보인다 (RequireAdmin)
// → 어떤 주소든 "없는 페이지"로만 보여서, 관리자 화면이 있는지 알 수 없다
function NotFound() {
  const navigate = useNavigate();

  return (
    <section className="not-found" aria-labelledby="not-found-title">
      <p className="not-found-code" aria-hidden="true">404</p>
      <h1 id="not-found-title">페이지를 찾을 수 없습니다</h1>
      <p className="not-found-desc">
        주소가 잘못 입력되었거나, 페이지가 이동 또는 삭제되었을 수 있습니다.
        <br />
        입력한 주소를 다시 확인해 주세요.
      </p>
      <div className="not-found-actions">
        <Link className="not-found-button is-primary" to="/">홈으로 가기</Link>
        <button className="not-found-button" type="button" onClick={() => navigate(-1)}>이전 페이지</button>
      </div>
    </section>
  );
}

export default NotFound;
