package com.kh.back.auth.dto;

import jakarta.validation.constraints.NotBlank;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

// 구글 로그인 요청 (보완 8): 화면이 구글에서 받은 ID 토큰
@Getter
@Setter
@NoArgsConstructor
public class GoogleLoginRequest {

    @NotBlank(message = "구글 로그인 정보가 없습니다.")
    private String idToken;

    // 10-22: 로그인 화면의 동의 체크(만 18세 이상 · 약관 · 개인정보)를 모두 했으면 true — 처음 온 사람만 확인한다
    private boolean consent;
}
