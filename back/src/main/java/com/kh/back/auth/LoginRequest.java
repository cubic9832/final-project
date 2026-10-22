package com.kh.back.auth;

import jakarta.validation.constraints.NotBlank;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

/**
 * 로그인 요청 본문. 형식 검사는 빈 값만 한다.
 * (이메일 형식이 틀려도 "이메일 또는 비밀번호가 올바르지 않습니다"로 똑같이 응답하기 위해)
 */
@Getter
@Setter
@NoArgsConstructor
public class LoginRequest {

    @NotBlank(message = "이메일을 입력해 주세요.")
    private String email;

    @NotBlank(message = "비밀번호를 입력해 주세요.")
    private String password;

    // 보완 6: 로그인에 여러 번 실패한 뒤에만 필요한 reCAPTCHA 토큰 ("로봇이 아닙니다" 체크 결과). 평소에는 비어 있다
    private String recaptchaToken;

    // 회원가입과 같은 규칙: 앞뒤 공백을 먼저 지운다 (비밀번호는 그대로)
    public void setEmail(String email) {
        this.email = email == null ? null : email.trim();
    }
}
