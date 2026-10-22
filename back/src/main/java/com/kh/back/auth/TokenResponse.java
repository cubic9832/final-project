package com.kh.back.auth;

import com.kh.back.member.MemberResponse;
import lombok.RequiredArgsConstructor;
import lombok.Getter;

/**
 * 로그인 응답 본문: access token(JWT) + 로그인한 회원 정보.
 * 프론트는 accessToken 을 메모리(zustand)에 두고, 이후 요청마다 Authorization: Bearer 헤더로 보낸다.
 * (refresh token 은 재발급 단계에서 쿠키로 따로 보낸다)
 */
@Getter
@RequiredArgsConstructor
public class TokenResponse {

    private final String accessToken;
    private final MemberResponse member;

    // 10-22: 구글로 방금 새로 가입했으면 true → 화면이 "닉네임은 ○○로 정해졌어요" 알림을 띄운다
    private boolean newMember;

    public TokenResponse markNewMember(boolean newMember) {
        this.newMember = newMember;
        return this;
    }
}
