package com.kh.back.auth;

import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.Pattern;
import jakarta.validation.constraints.Size;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

/**
 * 비밀번호 재설정 요청 본문 (보완 7 추가: 비밀번호 찾기). 이메일 인증을 마친 뒤 새 비밀번호를 보낸다.
 * 새 비밀번호 규칙은 회원가입(SignupRequest)과 같다. 반복 · 연속 문자 등은 AuthServiceImpl 이 PasswordPolicy 로 검사
 */
@Getter
@Setter
@NoArgsConstructor
public class PasswordResetRequest {

    @NotBlank(message = "이메일을 입력해 주세요.")
    private String email;

    @NotBlank(message = "새 비밀번호를 입력해 주세요.")
    @Size(min = 8, max = 20, message = "비밀번호는 8~20자로 입력해 주세요.")
    @Pattern(regexp = "^(?=.*[A-Za-z])(?=.*\\d)(?=.*[^A-Za-z0-9])\\S+$",
            message = "비밀번호는 영문 · 숫자 · 특수문자를 모두 포함하고 공백이 없어야 합니다.")
    private String newPassword;

    // 보완 7 추가(10-22): 코드 확인 때 받은 일회용 증명 번호 (없으면 이메일 인증을 안 한 것으로 본다)
    private String verificationToken;

    public void setEmail(String email) {
        this.email = email == null ? null : email.trim();
    }
}
