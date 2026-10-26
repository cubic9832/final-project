package com.kh.back.auth.service;

import static org.assertj.core.api.Assertions.assertThat;

import org.junit.jupiter.api.Test;

// 보완 2 추가 · 보완 4 추가: 현재 비밀번호 틀린 횟수 (회원별, 성공하면 초기화, 변경 · 탈퇴 공통)
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

    @Test
    void 세번째부터_남은_횟수_다섯번째는_로그아웃_코드() {
        assertThat(limiter.mismatch(3L, "틀림").getCode()).isEqualTo("PASSWORD_MISMATCH");
        limiter.mismatch(3L, "틀림");
        assertThat(limiter.mismatch(3L, "틀림").getMessage()).isEqualTo("틀림 (2번 더 틀리면 로그아웃됩니다)");
        limiter.mismatch(3L, "틀림");
        assertThat(limiter.mismatch(3L, "틀림").getCode()).isEqualTo(PasswordChangeLimiter.LOGOUT_CODE);
        assertThat(limiter.recordFailure(3L)).isEqualTo(1); // 로그아웃 후 다시 1부터
    }

    @Test
    void 다섯번째_뒤에는_10분_동안_잠긴다() {
        for (int i = 0; i < PasswordChangeLimiter.LOGOUT_LIMIT; i++) {
            limiter.mismatch(4L, "틀림");
        }
        org.assertj.core.api.Assertions.assertThatThrownBy(() -> limiter.checkLocked(4L))
                .isInstanceOf(com.kh.back.common.exception.ApiException.class).hasMessageContaining("분 뒤에 다시");
        limiter.checkLocked(5L); // 다른 회원은 영향 없음
    }
}
