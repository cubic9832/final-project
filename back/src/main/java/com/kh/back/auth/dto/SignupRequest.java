package com.kh.back.auth.dto;

import jakarta.validation.constraints.Email;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.Pattern;
import jakarta.validation.constraints.Size;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

/**
 * 회원가입 요청 본문. Controller 의 @Valid 가 아래 조건을 검사하고,
 * 어긋나면 GlobalExceptionHandler 가 400 과 message 를 돌려준다.
 * 조건은 회원가입 화면(SignupPage)의 검사 규칙과 같게 맞춘다. (프론트 검사는 편의, 서버 검사는 보안)
 */
@Getter
@Setter
@NoArgsConstructor
public class SignupRequest {

    @NotBlank(message = "이메일을 입력해 주세요.")
    @Email(message = "이메일 형식이 올바르지 않습니다.")
    @Size(max = 100, message = "이메일은 100자 이하로 입력해 주세요.") // 보완 2: 255 → 100 (DB 컬럼은 255 그대로)
    private String email;

    // 보완 2: 8~20자 + 영문 · 숫자 · 특수문자. 반복 · 연속 문자, 이메일 아이디, 흔한 비밀번호는
    // 이메일과 함께 봐야 해서 AuthServiceImpl 에서 PasswordPolicy 로 검사한다
    @NotBlank(message = "비밀번호를 입력해 주세요.")
    @Size(min = 8, max = 20, message = "비밀번호는 8~20자로 입력해 주세요.")
    @Pattern(regexp = "^(?=.*[A-Za-z])(?=.*\\d)(?=.*[^A-Za-z0-9])\\S+$",
            message = "비밀번호는 영문 · 숫자 · 특수문자를 모두 포함하고 공백이 없어야 합니다.")
    private String password;

    @NotBlank(message = "이름 또는 닉네임을 입력해 주세요.")
    @Size(min = 2, max = 12, message = "이름 또는 닉네임은 2~12자로 입력해 주세요.") // 보완 2: 50 → 2~12 (DB 컬럼은 50 그대로)
    private String nickName;

    // 앞뒤 공백을 먼저 지운 뒤 검사한다 ("user@example.com " 을 형식 오류로 보지 않게)
    public void setEmail(String email) {
        this.email = email == null ? null : email.trim();
    }

    public void setNickName(String nickName) {
        this.nickName = nickName == null ? null : nickName.trim();
    }
}
