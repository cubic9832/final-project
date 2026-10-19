package com.kh.back.auth;

import com.kh.back.member.MemberResponse;

public interface AuthService {

    // 회원가입. 가입만 하고 로그인 상태로 만들지는 않는다
    MemberResponse signup(SignupRequest request);

    // 로그인. 이메일 · 비밀번호가 맞으면 access token 과 refresh token 을 발급한다
    AuthTokens login(LoginRequest request, String clientIp); // 보완 6: 실패 횟수를 IP 별로도 센다

    // 재발급. refresh token 이 유효하면 새 access token 과 새 refresh token 으로 바꿔 준다 (이전 refresh token 은 폐기)
    AuthTokens refresh(String refreshToken);

    // 로그아웃. refresh token 을 DB 에서 지운다
    void logout(String refreshToken);

    // 보완 3: 이메일 중복 확인. 형식이 맞고 아직 가입되지 않았으면 true (형식이 틀리면 400)
    boolean isEmailAvailable(String email);

    // 보완 3: 닉네임 중복 확인. 2~12자이고 아직 쓰는 사람이 없으면 true (길이가 틀리면 400)
    boolean isNickNameAvailable(String nickName);
}
