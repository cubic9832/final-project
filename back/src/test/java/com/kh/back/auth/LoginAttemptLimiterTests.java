package com.kh.back.auth;

import static org.assertj.core.api.Assertions.assertThat;

import org.junit.jupiter.api.Test;

// 보완 6: 로그인 실패 횟수 규칙 (3번 → reCAPTCHA, 5번 → 10분 잠금, 성공 · 가입 → 초기화)
class LoginAttemptLimiterTests {

    private final LoginAttemptLimiter limiter = new LoginAttemptLimiter();

    private void fail(String email, int times) {
        for (int i = 0; i < times; i++) {
            limiter.recordFailure(email);
        }
    }

    @Test
    void 두번까지는_reCAPTCHA_없음() {
        fail("a@example.com", 2);
        assertThat(limiter.isCaptchaRequired("a@example.com")).isFalse();
        assertThat(limiter.lockedMinutesLeft("a@example.com")).isZero();
    }

    @Test
    void 세번부터_reCAPTCHA() {
        fail("a@example.com", 3);
        assertThat(limiter.isCaptchaRequired("a@example.com")).isTrue();
        assertThat(limiter.lockedMinutesLeft("a@example.com")).isZero();
    }

    @Test
    void 다섯번이면_10분_잠금() {
        fail("a@example.com", 5);
        assertThat(limiter.lockedMinutesLeft("a@example.com")).isEqualTo(10);
    }

    @Test
    void 이메일마다_따로_센다() {
        fail("a@example.com", 5);
        assertThat(limiter.failureCount("b@example.com")).isZero();
        assertThat(limiter.isCaptchaRequired("b@example.com")).isFalse();
    }

    @Test
    void 초기화하면_처음부터() {
        fail("a@example.com", 5);
        limiter.reset("a@example.com");
        assertThat(limiter.failureCount("a@example.com")).isZero();
        assertThat(limiter.lockedMinutesLeft("a@example.com")).isZero();
    }

    @Test
    void 기록이_많아도_기한_안_지난_기록은_남는다() {
        for (int i = 0; i <= LoginAttemptLimiter.CLEANUP_THRESHOLD + 10; i++) {
            limiter.recordFailure("user" + i + "@example.com");
        }
        fail("a@example.com", 3); // 정리가 돌아도 10분이 안 지난 기록은 지우지 않는다
        assertThat(limiter.failureCount("user0@example.com")).isEqualTo(1);
        assertThat(limiter.isCaptchaRequired("a@example.com")).isTrue();
    }
}
