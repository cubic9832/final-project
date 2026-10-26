package com.kh.back.auth.dto;

import java.time.LocalDateTime;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

/**
 * refresh_token 테이블 1행 (Flyway V6).
 * 6단계: 1행 = 로그인 중인 기기 1개. 기기 이름 · 처음 로그인 시각(V12), 마지막 사용 시각 = 이 행을 만든 시각(created_at)
 */
@Getter
@Setter
@NoArgsConstructor
public class RefreshTokenDto {

    private Long id;
    private Long userId;
    private String token;
    private LocalDateTime expiresAt;
    private String device;              // 예: Chrome · Windows (모르면 null)
    private LocalDateTime loggedInAt;   // 처음 로그인한 시각 (재발급 때도 그대로 넘김)
    private LocalDateTime createdAt;    // 이 토큰을 만든 시각 = 마지막으로 로그인을 이어 간 시각
}
