package com.kh.back.auth;

import com.kh.back.member.MemberResponse;
import lombok.AllArgsConstructor;
import lombok.Getter;

/**
 * 로그인 응답 본문: access token(JWT) + 로그인한 회원 정보.
 * 프론트는 accessToken 을 메모리(zustand)에 두고, 이후 요청마다 Authorization: Bearer 헤더로 보낸다.
 * (refresh token 은 재발급 단계에서 쿠키로 따로 보낸다)
 */
@Getter
@AllArgsConstructor
public class TokenResponse {

    private final String accessToken;
    private final MemberResponse member;
}
