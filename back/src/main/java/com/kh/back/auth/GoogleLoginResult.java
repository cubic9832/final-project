package com.kh.back.auth;

/**
 * 구글 로그인 결과 (보완 8): 둘 중 하나만 채워진다.
 * - tokens: 이미 연결된(또는 같은 이메일로 가입된) 회원 → 바로 로그인
 * - signup: 처음 온 사람 → 추가 정보 입력 화면으로 (가입 대기 번호 · 구글 이메일 · 이름)
 */
public record GoogleLoginResult(AuthTokens tokens, SignupRequired signup) {

    public record SignupRequired(String signupToken, String email, String name) {
    }
}
