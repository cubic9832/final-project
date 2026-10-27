package com.kh.back.admin.dto;

import static org.assertj.core.api.Assertions.assertThat;

import java.time.LocalDate;
import org.junit.jupiter.api.Test;

// 7단계: 관리자 회원 목록에 보내는 값 — 이메일 가리기 · 나이대 · 로그인 방법
class AdminMemberResponseTests {

    @Test
    void 이메일은_앞_두_글자만_보인다() {
        assertThat(AdminMemberResponse.maskEmail("stage6.test@example.com")).isEqualTo("st****@example.com");
        assertThat(AdminMemberResponse.maskEmail("abc@example.com")).isEqualTo("ab*@example.com");
        assertThat(AdminMemberResponse.maskEmail("a@example.com")).isEqualTo("a*@example.com");
    }

    @Test
    void 나이대는_만_나이로_계산한다() {
        assertThat(AdminMemberResponse.ageBand(LocalDate.now().minusYears(19))).isEqualTo("10대");
        assertThat(AdminMemberResponse.ageBand(LocalDate.now().minusYears(30))).isEqualTo("30대");
        assertThat(AdminMemberResponse.ageBand(LocalDate.now().minusYears(62))).isEqualTo("50대 이상");
        assertThat(AdminMemberResponse.ageBand(null)).isNull();
    }

    @Test
    void 로그인_방법은_비밀번호와_구글_연결로_정한다() {
        AdminMemberRow row = new AdminMemberRow();
        row.setEmail("x@example.com");
        row.setHasPassword(true);
        row.setHasGoogle(true);
        assertThat(AdminMemberResponse.from(row, 0).loginMethod()).isEqualTo("BOTH");
        row.setHasPassword(false);
        assertThat(AdminMemberResponse.from(row, 0).loginMethod()).isEqualTo("GOOGLE");
        row.setHasGoogle(false);
        row.setHasPassword(true);
        assertThat(AdminMemberResponse.from(row, 0).loginMethod()).isEqualTo("EMAIL");
    }
}
