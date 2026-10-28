package com.kh.back.auth.dto;

import jakarta.validation.constraints.AssertTrue;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotNull;
import jakarta.validation.constraints.Past;
import jakarta.validation.constraints.Pattern;
import java.time.LocalDate;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

/**
 * 구글 가입 화면(/signup/google)의 추가 정보 (보완 8).
 * 회원가입(SignupRequest)과 같은 규칙. 이메일 · 비밀번호는 없고(구글이 확인), 닉네임은 구글 이름으로 자동으로 정한다
 * (가입 후 개인정보 · 계정 관리에서 바꿀 수 있음).
 */
@Getter
@Setter
@NoArgsConstructor
public class GoogleSignupRequest {

    @NotBlank(message = "구글 로그인을 다시 시도해 주세요.")
    private String signupToken;

    // 보완 11: 전화번호는 필수 (회원가입과 같은 규칙)
    @NotBlank(message = "전화번호를 입력해 주세요.")
    @Pattern(regexp = "^010-?\\d{4}-?\\d{4}$", message = "전화번호는 010-1234-5678 형식으로 입력해 주세요.")
    private String phone;

    @NotNull(message = "생년월일을 입력해 주세요.")
    @Past(message = "생년월일이 올바르지 않습니다.")
    private LocalDate birthDate;

    @NotBlank(message = "성별을 선택해 주세요.")
    @Pattern(regexp = "^(MALE|FEMALE|NONE)$", message = "성별을 선택해 주세요.")
    private String gender;

    // 만 18세 이상 · 서비스 이용약관 · 개인정보 수집 · 이용 동의 (체크 1개)
    @AssertTrue(message = "필수 동의 항목에 체크해 주세요.")
    private boolean consent;

    // 보완 9: [선택] 차량 추천 업데이트 수신 — 체크하면 이메일 알림 ALL, 안 하면 IMPORTANT
    private boolean updatesAgreed;
}
