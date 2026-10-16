-- 로그인 유지용 refresh token (JWT 인증 5단계)
-- 로그인하면 1행을 저장하고, 재발급할 때마다 지우고 새로 저장(교체)하고, 로그아웃하면 지운다.
-- access token(JWT)은 서버에 저장하지 않는다. 서버가 취소할 수 있어야 하는 refresh token 만 저장한다.

-- 회원 refresh token
CREATE TABLE refresh_token (
 -- 고유 식별자 (자동 증가 기본키)
 id BIGINT NOT NULL AUTO_INCREMENT PRIMARY KEY,
 -- 토큰 주인 회원 ID
 user_id BIGINT NOT NULL,
 -- refresh token 값 (UUID 36자). 브라우저에는 HttpOnly 쿠키로만 전달한다
 token VARCHAR(36) NOT NULL,
 -- 만료 시각 (발급 시각 + jwt.refresh-token-validity)
 expires_at DATETIME NOT NULL,
 -- 생성 시각 (현재 시각 자동 기록)
 created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
 -- 같은 토큰 값 중복 방지 (토큰으로 조회하므로 인덱스 역할도 한다)
 UNIQUE KEY uq_refresh_token_token (token),
 -- 외래키: user_id → users.id 참조. 회원이 삭제되면 토큰도 함께 삭제
 CONSTRAINT fk_refresh_token_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
