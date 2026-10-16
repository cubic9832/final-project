package com.kh.back.auth.service;

import com.kh.back.auth.dto.AuthTokens;
import com.kh.back.auth.dto.LoginRequest;
import com.kh.back.auth.dto.SignupRequest;
import com.kh.back.member.dto.MemberResponse;

public interface AuthService {

    // 회원가입. 가입만 하고 로그인 상태로 만들지는 않는다
    MemberResponse signup(SignupRequest request);

    // 로그인. 이메일 · 비밀번호가 맞으면 access token 과 refresh token 을 발급한다
    AuthTokens login(LoginRequest request);

    // 재발급. refresh token 이 유효하면 새 access token 과 새 refresh token 으로 바꿔 준다 (이전 refresh token 은 폐기)
    AuthTokens refresh(String refreshToken);

    // 로그아웃. refresh token 을 DB 에서 지운다
    void logout(String refreshToken);
}
