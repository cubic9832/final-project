package com.kh.back.auth.service;

import com.kh.back.auth.dto.SignupRequest;
import com.kh.back.member.dto.MemberResponse;

public interface AuthService {

    // 회원가입. 가입만 하고 로그인 상태로 만들지는 않는다
    MemberResponse signup(SignupRequest request);
}
