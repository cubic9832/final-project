package com.kh.back.auth.dto;

import java.time.LocalDateTime;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

/**
 * email_verifications 테이블 1행 (보완 7). 이메일 1개당 1행이며 코드를 다시 받으면 덮어쓴다.
 */
@Getter
@Setter
@NoArgsConstructor
public class EmailVerificationDto {

    private String email;
    private String codeHash;                     // 코드 원문이 아니라 BCrypt 해시
    private LocalDateTime expiresAt;
    private int failedAttempts;
    private LocalDateTime lastSentAt;
    private LocalDateTime sendWindowStartedAt;
    private int sendCount;
    private LocalDateTime verifiedAt;            // 인증 전이면 null
}
