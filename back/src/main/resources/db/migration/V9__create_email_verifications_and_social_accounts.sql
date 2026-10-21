-- 보완 7 · 8: 이메일 인증과 소셜(구글) 계정 연결
-- 두 보완이 함께 쓰는 DB 변경을 한 파일로 만든다 (보완 7 때 미리 생성, 보완 8 은 코드만 추가)

-- 보완 7: 회원가입 전 이메일 인증 코드 (이메일 1개당 1행, 다시 받으면 덮어쓴다)
CREATE TABLE email_verifications (
    -- 인증할 이메일 (소문자로 정리한 값)
    email VARCHAR(255) NOT NULL PRIMARY KEY,
    -- 인증 코드의 해시값 (BCrypt). 코드 원문은 저장하지 않는다
    code_hash VARCHAR(100) NOT NULL,
    -- 코드 만료 시각 (보낸 뒤 5분)
    expires_at DATETIME NOT NULL,
    -- 이 코드로 틀린 횟수 (5번이면 코드 무효)
    failed_attempts INT NOT NULL DEFAULT 0,
    -- 마지막으로 보낸 시각 (60초 안에는 다시 보낼 수 없다)
    last_sent_at DATETIME NOT NULL,
    -- 재전송 횟수 세기: 10분 구간의 시작 시각과 그 안에서 보낸 횟수 (최대 5번)
    send_window_started_at DATETIME NOT NULL,
    send_count INT NOT NULL DEFAULT 1,
    -- 인증 완료 시각 (완료 후 30분 안에 가입해야 한다). 아직이면 NULL
    verified_at DATETIME,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- 보완 8: 구글 계정 ↔ 회원 연결 (한 회원이 여러 소셜 계정을 연결할 수 있게 별도 테이블)
CREATE TABLE social_accounts (
    id BIGINT NOT NULL AUTO_INCREMENT PRIMARY KEY,
    user_id BIGINT NOT NULL,
    -- 제공자: GOOGLE
    provider VARCHAR(20) NOT NULL,
    -- 제공자가 준 고유 번호 (구글 sub). 이메일이 바뀌어도 같은 사람으로 알아본다
    provider_user_id VARCHAR(255) NOT NULL,
    -- 연결할 때의 소셜 계정 이메일 (참고용)
    email VARCHAR(255),
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_social_accounts_provider_user UNIQUE (provider, provider_user_id),
    CONSTRAINT fk_social_accounts_user FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
);
