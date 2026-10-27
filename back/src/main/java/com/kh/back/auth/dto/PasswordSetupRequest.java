package com.kh.back.auth.dto;

import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.Pattern;
import jakarta.validation.constraints.Size;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

/**
 * 보완 10: 구글 전용 회원의 비밀번호 만들기 요청 본문. 가입 이메일 인증을 마친 뒤 새 비밀번호를 보낸다.
 * 이메일은 받지 않는다 (로그인한 회원의 가입 이메일만 쓴다). 비밀번호 규칙은 회원가입(SignupRequest)과 같다
 */
@Getter
@Setter
@NoArgsConstructor
public class PasswordSetupRequest {

    @NotBlank(message = "새 비밀번호를 입력해 주세요.")
    @Size(min = 8, max = 20, message = "비밀번호는 8~20자로 입력해 주세요.")
    @Pattern(regexp = "^(?=.*[A-Za-z])(?=.*\\d)(?=.*[^A-Za-z0-9])\\S+$",
            message = "비밀번호는 영문 · 숫자 · 특수문자를 모두 포함하고 공백이 없어야 합니다.")
    private String newPassword;

    // 코드 확인 때 받은 일회용 증명 번호
    private String verificationToken;
}
