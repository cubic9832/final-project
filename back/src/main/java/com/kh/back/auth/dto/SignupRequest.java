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
    @Size(max = 255, message = "이메일은 255자 이하로 입력해 주세요.") // users.email VARCHAR(255)
    private String email;

    @NotBlank(message = "비밀번호를 입력해 주세요.")
    @Size(min = 8, max = 64, message = "비밀번호는 8~64자로 입력해 주세요.")
    @Pattern(regexp = "^(?=.*[A-Za-z])(?=.*\\d).+$", message = "비밀번호는 영문과 숫자를 포함해야 합니다.")
    private String password;

    @NotBlank(message = "이름 또는 닉네임을 입력해 주세요.")
    @Size(max = 50, message = "이름 또는 닉네임은 50자 이하로 입력해 주세요.") // users.nick_name VARCHAR(50)
    private String nickName;

    // 앞뒤 공백을 먼저 지운 뒤 검사한다 ("user@example.com " 을 형식 오류로 보지 않게)
    public void setEmail(String email) {
        this.email = email == null ? null : email.trim();
    }

    public void setNickName(String nickName) {
        this.nickName = nickName == null ? null : nickName.trim();
    }
}
