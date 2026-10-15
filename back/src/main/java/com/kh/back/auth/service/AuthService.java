package com.kh.back.auth.service;

import com.kh.back.auth.dto.LoginRequest;
import com.kh.back.auth.dto.SignupRequest;
import com.kh.back.auth.dto.TokenResponse;
import com.kh.back.member.dto.MemberResponse;

public interface AuthService {

    // 회원가입. 가입만 하고 로그인 상태로 만들지는 않는다
    MemberResponse signup(SignupRequest request);

    // 로그인. 이메일 · 비밀번호가 맞으면 access token 을 발급한다
    TokenResponse login(LoginRequest request);
}
