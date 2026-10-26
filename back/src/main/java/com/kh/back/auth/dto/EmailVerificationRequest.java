package com.kh.back.auth.dto;

import jakarta.validation.constraints.NotBlank;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

/**
 * 이메일 인증 요청 본문 (보완 7).
 * [인증 코드 받기] 는 email 만, [확인] 은 email + code 를 보낸다.
 */
@Getter
@Setter
@NoArgsConstructor
public class EmailVerificationRequest {

    @NotBlank(message = "이메일을 입력해 주세요.")
    private String email;

    private String code; // [확인] 때만 (6자리 숫자)

    public void setEmail(String email) {
        this.email = email == null ? null : email.trim();
    }
}
