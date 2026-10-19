package com.kh.back.auth;

import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotNull;
import jakarta.validation.constraints.Past;
import jakarta.validation.constraints.Pattern;
import jakarta.validation.constraints.Size;
import java.time.LocalDate;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

/**
 * 구글 첫 로그인 후 추가 정보 입력 (보완 8). 회원가입(SignupRequest)과 같은 규칙, 이메일 · 비밀번호는 없다.
 */
@Getter
@Setter
@NoArgsConstructor
public class GoogleSignupRequest {

    @NotBlank(message = "구글 로그인을 다시 시도해 주세요.")
    private String signupToken;

    @NotBlank(message = "이름 또는 닉네임을 입력해 주세요.")
    @Size(min = 2, max = 12, message = "이름 또는 닉네임은 2~12자로 입력해 주세요.")
    private String nickName;

    @NotBlank(message = "전화번호를 입력해 주세요.")
    @Pattern(regexp = "^010-?\\d{4}-?\\d{4}$", message = "전화번호는 010-1234-5678 형식으로 입력해 주세요.")
    private String phone;

    @NotNull(message = "생년월일을 입력해 주세요.")
    @Past(message = "생년월일이 올바르지 않습니다.")
    private LocalDate birthDate;

    @NotBlank(message = "성별을 선택해 주세요.")
    @Pattern(regexp = "^(MALE|FEMALE|NONE)$", message = "성별을 선택해 주세요.")
    private String gender;

    public void setNickName(String nickName) {
        this.nickName = nickName == null ? null : nickName.trim();
    }
}
