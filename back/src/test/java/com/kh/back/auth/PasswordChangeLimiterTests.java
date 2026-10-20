package com.kh.back.auth;

import static org.assertj.core.api.Assertions.assertThat;

import org.junit.jupiter.api.Test;

// 보완 2 추가: 비밀번호 변경에서 현재 비밀번호 틀린 횟수 (회원별, 성공하면 초기화)
class PasswordChangeLimiterTests {

    private final PasswordChangeLimiter limiter = new PasswordChangeLimiter();

    @Test
    void 회원별로_따로_센다() {
        limiter.recordFailure(1L);
        limiter.recordFailure(1L);
        assertThat(limiter.recordFailure(1L)).isEqualTo(3);
        assertThat(limiter.recordFailure(2L)).isEqualTo(1);
    }

    @Test
    void 초기화하면_다시_1부터() {
        for (int i = 0; i < PasswordChangeLimiter.LOGOUT_LIMIT; i++) {
            limiter.recordFailure(1L);
        }
        limiter.reset(1L);
        assertThat(limiter.recordFailure(1L)).isEqualTo(1);
    }
}
