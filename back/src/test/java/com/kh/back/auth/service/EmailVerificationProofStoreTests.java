package com.kh.back.auth.service;

import static org.assertj.core.api.Assertions.assertThat;

import org.junit.jupiter.api.Test;

// 보완 7 추가(10-22): 일회용 증명 번호 — 인증한 이메일에만 맞고, 한 번 쓰면 끝
class EmailVerificationProofStoreTests {

    private final EmailVerificationProofStore store = new EmailVerificationProofStore();

    @Test
    void 발급한_이메일에만_맞는다() {
        String token = store.issue("a@example.com");
        assertThat(store.isValid(token, "a@example.com")).isTrue();
        assertThat(store.isValid(token, "b@example.com")).isFalse();
        assertThat(store.isValid("guess", "a@example.com")).isFalse();
        assertThat(store.isValid(null, "a@example.com")).isFalse();
    }

    @Test
    void 한_번_쓰면_다시_쓸_수_없다() {
        String token = store.issue("a@example.com");
        store.remove(token);
        assertThat(store.isValid(token, "a@example.com")).isFalse();
    }
}
