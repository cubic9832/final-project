package com.kh.back.auth.service;

import static org.assertj.core.api.Assertions.assertThat;

import org.junit.jupiter.api.Test;

// 보완 3 추가: 닉네임 금지어 (운영자 사칭 · 욕설). 공백 · 숫자 · 기호 · 대소문자를 바꿔도 걸리는지
class NickNamePolicyTests {

    @Test
    void 보통_닉네임은_통과() {
        assertThat(NickNamePolicy.check("첫차준비생")).isNull();
        assertThat(NickNamePolicy.check("drive_2027")).isNull();
    }

    @Test
    void 운영자_사칭_단어는_거절() {
        assertThat(NickNamePolicy.check("관리자")).contains("운영자로 오해");
        assertThat(NickNamePolicy.check("Admin_01")).contains("운영자로 오해");
        assertThat(NickNamePolicy.check("운 영 자")).contains("운영자로 오해");
    }

    @Test
    void 욕설은_숫자를_섞어도_거절() {
        assertThat(NickNamePolicy.check("시1발")).isEqualTo("사용할 수 없는 단어가 들어 있습니다.");
        assertThat(NickNamePolicy.check("F.U.C.K")).isEqualTo("사용할 수 없는 단어가 들어 있습니다.");
    }
}
