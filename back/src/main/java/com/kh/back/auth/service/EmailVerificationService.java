package com.kh.back.auth.service;

import java.time.Duration;

public interface EmailVerificationService {
    Duration CODE_VALIDITY = Duration.ofMinutes(5);
    Duration RESEND_COOLDOWN = Duration.ofSeconds(60);
    Duration SIGNUP_DEADLINE = Duration.ofMinutes(30);

    void sendCode(String email);

    void confirmCode(String email, String code);

    boolean isVerified(String email);

    void consume(String email);

    boolean isMailEnabled();
}
