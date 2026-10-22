package com.kh.back.auth;

import com.kh.back.member.MemberResponse;
import lombok.RequiredArgsConstructor;
import lombok.Getter;

/**
 * Service 가 Controller 에 넘기는 로그인 · 재발급 결과.
 * Controller 는 refreshToken 은 HttpOnly 쿠키로, 나머지(accessToken, member)는 TokenResponse 본문으로 나눠 보낸다.
 * (refresh token 을 본문에 넣으면 JavaScript 가 읽을 수 있게 되므로 본문에는 넣지 않는다)
 */
@Getter
@RequiredArgsConstructor
public class AuthTokens {

    private final String accessToken;
    private final String refreshToken;
    private final MemberResponse member;

    // 10-22: 구글로 방금 새로 가입했으면 true → 화면이 "닉네임은 ○○로 정해졌어요" 알림을 띄운다
    private boolean newMember;

    public AuthTokens markNewMember(boolean newMember) {
        this.newMember = newMember;
        return this;
    }
}
