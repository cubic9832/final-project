package com.kh.back.auth;

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
}
