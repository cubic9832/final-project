package com.kh.back.auth.dto;

import com.kh.back.member.dto.MemberResponse;
import lombok.AllArgsConstructor;
import lombok.Getter;

/**
 * Service 가 Controller 에 넘기는 로그인 · 재발급 결과.
 * Controller 는 refreshToken 은 HttpOnly 쿠키로, 나머지(accessToken, member)는 TokenResponse 본문으로 나눠 보낸다.
 * (refresh token 을 본문에 넣으면 JavaScript 가 읽을 수 있게 되므로 본문에는 넣지 않는다)
 */
@Getter
@AllArgsConstructor
public class AuthTokens {

    private final String accessToken;
    private final String refreshToken;
    private final MemberResponse member;
}
