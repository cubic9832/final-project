package com.kh.back.auth.dto;

import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.Pattern;
import jakarta.validation.constraints.Size;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

/**
 * 비밀번호 변경 요청 본문 (보완 2 추가: 마이페이지 비밀번호 변경). 로그인한 상태에서 현재 비밀번호를 확인하고 바꾼다.
 * 새 비밀번호 규칙은 회원가입(SignupRequest)과 같다. 반복 · 연속 문자 등은 AuthServiceImpl 이 PasswordPolicy 로 검사
 */
@Getter
@Setter
@NoArgsConstructor
public class PasswordChangeRequest {

    @NotBlank(message = "현재 비밀번호를 입력해 주세요.")
    private String currentPassword;

    @NotBlank(message = "새 비밀번호를 입력해 주세요.")
    @Size(min = 8, max = 20, message = "비밀번호는 8~20자로 입력해 주세요.")
    @Pattern(regexp = "^(?=.*[A-Za-z])(?=.*\\d)(?=.*[^A-Za-z0-9])\\S+$",
            message = "비밀번호는 영문 · 숫자 · 특수문자를 모두 포함하고 공백이 없어야 합니다.")
    private String newPassword;
}
