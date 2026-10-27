-- 보완 9: 가입 동의 기록 · 이메일 알림 설정 (회원 1명당 1행).
-- 이미 적용된 V1 ~ V13 은 고치지 않는다.
-- 이 표가 생기기 전에 가입한 회원은 행이 없다 → 화면은 "기록 없음" · 알림은 기본값(IMPORTANT)으로 본다

CREATE TABLE user_agreements (
    user_id BIGINT NOT NULL PRIMARY KEY,
    -- [필수] 서비스 이용약관 · 개인정보 수집 · 이용에 동의한 시각 (가입할 때)
    terms_agreed_at DATETIME NULL,
    privacy_agreed_at DATETIME NULL,
    -- 이메일 알림 범위: ALL(차량 추천 업데이트까지) · IMPORTANT(구매계획 등 중요 알림만) · NONE(받지 않음)
    email_notification VARCHAR(20) NOT NULL DEFAULT 'IMPORTANT',
    -- [선택] 차량 추천 업데이트 수신에 동의한 시각 (ALL 일 때만 값, 다른 범위로 바꾸면 NULL)
    updates_agreed_at DATETIME NULL,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    CONSTRAINT fk_user_agreements_user FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
);
