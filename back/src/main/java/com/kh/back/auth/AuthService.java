package com.kh.back.auth;

import com.kh.back.member.MemberResponse;

public interface AuthService {

    // 회원가입. 가입만 하고 로그인 상태로 만들지는 않는다
    MemberResponse signup(SignupRequest request);

    // 로그인. 이메일 · 비밀번호가 맞으면 access token 과 refresh token 을 발급한다
    // 보완 7: 이메일 인증 코드 받기 (형식 · 중복 확인 후 발송) · 확인
    EmailVerificationResponse sendEmailVerification(String email);

    String confirmEmailVerification(String email, String code); // 보완 7 추가: 일회용 증명 번호

    // 보완 7 추가: 비밀번호 찾기 — 가입한 이메일로 인증 코드 받기 · 확인 · 새 비밀번호로 바꾸기
    EmailVerificationResponse sendPasswordResetCode(String email);

    String confirmPasswordResetCode(String email, String code); // 보완 7 추가: 일회용 증명 번호

    void resetPassword(PasswordResetRequest request);

    // 보완 2 추가: 로그인한 회원의 비밀번호 변경 — 다른 기기 로그인은 끊고, 지금 기기에는 새 토큰을 준다
    AuthTokens changePassword(Long userId, PasswordChangeRequest request);

    // 보완 8: 구글 로그인 — 연결된 회원이면 로그인, 처음이면 추가 정보 입력 필요
    GoogleLoginResult googleLogin(String idToken);

    // 보완 8: 구글 첫 로그인 후 추가 정보로 가입 + 로그인
    AuthTokens googleSignup(GoogleSignupRequest request);

    AuthTokens login(LoginRequest request, String clientIp); // 보완 6: clientIp 는 reCAPTCHA 확인 요청에 함께 보낸다

    // 재발급. refresh token 이 유효하면 새 access token 과 새 refresh token 으로 바꿔 준다 (이전 refresh token 은 폐기)
    AuthTokens refresh(String refreshToken);

    // 로그아웃. refresh token 을 DB 에서 지운다
    void logout(String refreshToken);

    // 보완 3: 이메일 중복 확인. 형식이 맞고 아직 가입되지 않았으면 true (형식이 틀리면 400)
    boolean isEmailAvailable(String email);

    // 보완 3: 닉네임 중복 확인. 2~12자이고 아직 쓰는 사람이 없으면 true (길이가 틀리면 400)
    boolean isNickNameAvailable(String nickName);
}
