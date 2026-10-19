package com.kh.back.auth;

import java.time.LocalDateTime;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

/**
 * refresh_token 테이블 1행 (Flyway V6).
 */
@Getter
@Setter
@NoArgsConstructor
public class RefreshTokenDto {

    private Long id;
    private Long userId;
    private String token;
    private LocalDateTime expiresAt;
}
