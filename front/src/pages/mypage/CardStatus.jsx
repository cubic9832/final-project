// 6단계: 마이페이지 · 개인정보 화면의 카드별 상태 표시 (스터디 step2 의 PageSpinner 패턴)
// 카드마다 따로 불러오므로, 한 카드가 실패해도 다른 카드는 그대로 보인다.
// 스피너는 패키지를 더하지 않고 CSS 로 그린다 (react-spinners 는 프로젝트에 없음)

export function CardLoading({ label = '불러오는 중…' }) {
  return (
    <div className="card-status" role="status">
      <span className="card-spinner" aria-hidden="true" />
      <span>{label}</span>
    </div>
  );
}

// 실패: 문구 + [다시 시도]
export function CardError({ message, onRetry }) {
  return (
    <div className="card-status card-status-error" role="alert">
      <span>{message}</span>
      {onRetry && (
        <button className="my-outline-button" type="button" onClick={onRetry}>
          다시 시도
        </button>
      )}
    </div>
  );
}
