package com.kh.back.auth.dto;

import jakarta.validation.constraints.NotBlank;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

/**
 * 보완 10: 구글 전용 회원의 비밀번호 만들기 — 인증 코드 확인 본문 { code } (이메일은 로그인한 회원의 것)
 */
@Getter
@Setter
@NoArgsConstructor
public class PasswordSetupCodeRequest {

    @NotBlank(message = "인증 코드를 입력해 주세요.")
    private String code;
}
