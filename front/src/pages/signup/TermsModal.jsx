// 약관 보기 팝업 (Figma에는 없음. 회원가입 약관 옆 "보기" 버튼용으로 추가)
// 확정된 약관 문구가 없어 서비스 이용약관 · 마케팅 동의는 준비 중 안내만 보여 준다. 약관 문구를 지어내지 않는다.
// 보완 5 추가(10-20): 개인정보 수집·이용은 "이 서비스가 실제로 받는 항목 · 쓰는 곳 · 지우는 때" 만 표로 보여 준다
import AuthModal from '../../features/auth/components/AuthModal';
import './TermsModal.css';

// 코드에서 실제로 저장하는 항목 기준 (V1 users · V8 user_profiles · V9 email_verifications · social_accounts)
const PRIVACY_ROWS = [
  {
    group: '필수 (이메일 가입)',
    items: '이메일, 비밀번호(암호화해 저장), 이름 또는 닉네임',
    purpose: '회원 식별, 로그인',
  },
  {
    group: '필수',
    items: '생년월일, 성별',
    purpose: '만 18세 이상 확인, 연령대별 차량 추천 · 통계',
  },
  { group: '선택', items: '전화번호', purpose: '서비스 관련 연락 (입력한 경우만)' },
  { group: '필수 (이메일 가입)', items: '이메일 인증 기록', purpose: '본인 이메일 확인 (가입하면 바로 삭제)' },
  { group: '구글로 가입 · 연결 시', items: '구글 계정 고유번호, 구글 이메일, 이름', purpose: '구글 로그인 연결' },
];

function PrivacyBody() {
  return (
    <>
      <p className="terms-example">예시 문구 · 실제 서비스에 쓰려면 법률 검토가 필요합니다.</p>
      <table className="terms-table">
        <thead>
          <tr>
            <th scope="col">구분</th>
            <th scope="col">수집 항목</th>
            <th scope="col">이용 목적</th>
          </tr>
        </thead>
        <tbody>
          {PRIVACY_ROWS.map((row) => (
            <tr key={row.items}>
              <td>{row.group}</td>
              <td>{row.items}</td>
              <td>{row.purpose}</td>
            </tr>
          ))}
        </tbody>
      </table>
      <p>
        <strong>보유 기간</strong> 회원 탈퇴 시 회원 정보 · 개인 정보 · 구글 연결 정보를 함께 삭제합니다.
      </p>
      <p>동의하지 않으면 회원가입을 할 수 없습니다.</p>
    </>
  );
}

export default function TermsModal({ term, agreed, onAgree, onClose }) {
  return (
    <AuthModal title={`[${term.required ? '필수' : '선택'}] ${term.title}`} onClose={onClose} size="lg">
      <div className="terms-body" tabIndex={0} aria-label={`${term.title} 본문`}>
        {term.id === 'privacy' ? (
          <PrivacyBody />
        ) : (
          <>
            <p>약관 본문은 준비 중입니다.</p>
            <p>팀에서 확정한 약관 문구가 나오면 이 영역에 표시됩니다.</p>
          </>
        )}
      </div>

      <div className="auth-modal-actions">
        <button className="auth-modal-button" type="button" onClick={onClose}>
          닫기
        </button>
        {/* 이미 동의했으면 동의 버튼 대신 상태만 보여 준다 */}
        <button
          className="auth-modal-button auth-modal-button-primary"
          type="button"
          onClick={onAgree}
          disabled={agreed}
        >
          {agreed ? '동의함' : '동의하고 닫기'}
        </button>
      </div>
    </AuthModal>
  );
}
