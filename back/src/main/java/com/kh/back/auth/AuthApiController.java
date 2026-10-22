package com.kh.back.auth;

import com.kh.back.common.dto.ApiResponse;
import com.kh.back.common.exception.ApiException;
import com.kh.back.common.jwt.JwtProvider;
import com.kh.back.member.MemberResponse;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.validation.Valid;
import java.time.Duration;
import lombok.RequiredArgsConstructor;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.http.HttpHeaders;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseCookie;
import org.springframework.http.ResponseEntity;
import org.springframework.security.core.annotation.AuthenticationPrincipal;
import org.springframework.web.bind.annotation.CookieValue;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

/**
 * 회원가입 · 로그인 · 토큰 재발급 · 로그아웃.
 * 이 주소들은 로그인 전에도 불러야 하므로 SecurityConfig 에서 /api/v1/auth/** 를 공개해 두었다.
 *
 * access token 은 응답 본문으로 보내고(프론트가 메모리에 보관),
 * refresh token 은 HttpOnly 쿠키로 보낸다(JavaScript 가 읽을 수 없고, 브라우저가 알아서 저장 · 전송).
 */
@RestController
@RequestMapping("/api/v1/auth")
@RequiredArgsConstructor
public class AuthApiController {

    private static final String REFRESH_COOKIE = "refreshToken";

    private final AuthService authService;
    private final JwtProvider jwtProvider;

    // https 에서만 쿠키를 보내라는 Secure 속성. 로컬 http 개발에서는 false (application.yml 의 jwt.cookie-secure)
    @Value("${jwt.cookie-secure}")
    private boolean cookieSecure;

    // POST /api/v1/auth/signup — 회원가입. 성공하면 201 과 가입한 회원 정보
    // 호출: SignupPage.jsx [회원가입 완료] 버튼(handleSubmit) → authApi.signup
    @PostMapping("/signup")
    public ResponseEntity<ApiResponse<MemberResponse>> signup(@Valid @RequestBody SignupRequest request) {
        return ResponseEntity.status(HttpStatus.CREATED).body(ApiResponse.ok(authService.signup(request)));
    }

    // GET /api/v1/auth/check-email?email=… — 이메일 중복 확인 (보완 3). { available }
    // 호출: SignupPage.jsx 이메일 [중복 확인] 버튼 → authApi.checkEmail
    @GetMapping("/check-email")
    public ApiResponse<AvailabilityResponse> checkEmail(@RequestParam String email) {
        return ApiResponse.ok(new AvailabilityResponse(authService.isEmailAvailable(email)));
    }

    // GET /api/v1/auth/check-nickname?nickName=… — 닉네임 중복 확인 (보완 3). { available }
    // 호출: SignupPage.jsx 닉네임 [중복 확인] 버튼 → authApi.checkNickName
    @GetMapping("/check-nickname")
    public ApiResponse<AvailabilityResponse> checkNickName(@RequestParam String nickName) {
        return ApiResponse.ok(new AvailabilityResponse(authService.isNickNameAvailable(nickName)));
    }

    // POST /api/v1/auth/email-verification — 보완 7: 인증 코드 받기. 본문 { email }
    // 호출: SignupPage.jsx 이메일 [인증 코드 받기] → authApi.sendEmailCode
    // 이미 가입된 이메일 409, 60초 안 재요청 · 10분 5번 초과 429
    @PostMapping("/email-verification")
    public ApiResponse<EmailVerificationResponse> sendEmailVerification(@Valid @RequestBody EmailVerificationRequest request) {
        return ApiResponse.ok(authService.sendEmailVerification(request.getEmail()));
    }

    // POST /api/v1/auth/email-verification/confirm — 보완 7: 코드 확인. 본문 { email, code }
    // 호출: SignupPage.jsx 인증 코드 [확인] → authApi.confirmEmailCode
    @PostMapping("/email-verification/confirm")
    // 보완 7 추가(10-22): 성공하면 { verificationToken } — 회원가입 요청에 같이 보낸다
    public ApiResponse<EmailVerificationProof> confirmEmailVerification(@Valid @RequestBody EmailVerificationRequest request) {
        return ApiResponse.ok(new EmailVerificationProof(
                authService.confirmEmailVerification(request.getEmail(), request.getCode())));
    }

    // POST /api/v1/auth/password-reset/code — 보완 7 추가: 비밀번호 찾기 인증 코드 받기. 본문 { email }
    // 호출: PasswordResetModal.jsx [인증 코드 받기] → authApi.sendPasswordResetCode
    @PostMapping("/password-reset/code")
    public ApiResponse<EmailVerificationResponse> sendPasswordResetCode(@Valid @RequestBody EmailVerificationRequest request) {
        return ApiResponse.ok(authService.sendPasswordResetCode(request.getEmail()));
    }

    // POST /api/v1/auth/password-reset/confirm — 코드 확인. 본문 { email, code }
    @PostMapping("/password-reset/confirm")
    // 보완 7 추가(10-22): 성공하면 { verificationToken } — 새 비밀번호 요청에 같이 보낸다
    public ApiResponse<EmailVerificationProof> confirmPasswordResetCode(@Valid @RequestBody EmailVerificationRequest request) {
        return ApiResponse.ok(new EmailVerificationProof(
                authService.confirmPasswordResetCode(request.getEmail(), request.getCode())));
    }

    // POST /api/v1/auth/password-reset — 새 비밀번호로 바꾸기. 본문 { email, newPassword }
    // 성공하면 모든 기기 로그인이 끊긴다 → 새 비밀번호로 다시 로그인
    @PostMapping("/password-reset")
    public ApiResponse<Void> resetPassword(@Valid @RequestBody PasswordResetRequest request) {
        authService.resetPassword(request);
        return ApiResponse.ok(null);
    }

    // POST /api/v1/auth/password — 보완 2 추가: 마이페이지 비밀번호 변경. 본문 { currentPassword, newPassword }
    // 호출: MyPage.jsx 계정 및 데이터 [변경] → PasswordChangeModal → authApi.changePassword
    // 로그인 필요(토큰의 회원 번호만 사용). 성공하면 다른 기기는 로그아웃, 지금 기기는 새 토큰 + 새 refresh 쿠키
    // (/auth 아래에 둔 이유: refresh 쿠키 경로(/api/v1/auth)와 같아 새 쿠키를 함께 내려줄 수 있다)
    @PostMapping("/password")
    public ResponseEntity<ApiResponse<TokenResponse>> changePassword(@AuthenticationPrincipal Long userId,
                                                                     @Valid @RequestBody PasswordChangeRequest request) {
        return withTokens(authService.changePassword(userId, request));
    }

    // POST /api/v1/auth/google — 보완 8: 구글 로그인. 본문 { idToken, consent }
    // 호출: LoginPage.jsx [Google 계정으로 계속하기] → authApi.googleLogin
    // 연결된(또는 같은 이메일) 회원 · 동의한 처음 온 사람 → 로그인과 같은 응답 { accessToken, member } + refresh 쿠키
    // 처음 온 사람인데 동의가 없으면 400 SIGNUP_CONSENT_REQUIRED (10-22: 추가 정보 화면 · /google/signup 삭제)
    @PostMapping("/google")
    public ResponseEntity<ApiResponse<TokenResponse>> googleLogin(@Valid @RequestBody GoogleLoginRequest request) {
        return withTokens(authService.googleLogin(request.getIdToken(), request.isConsent()));
    }

    // POST /api/v1/auth/login — 로그인. 성공하면 200 + 본문 { accessToken, member } + refresh token 쿠키
    // 호출: LoginPage.jsx [로그인] 버튼(handleSubmit) → authApi.login
    @PostMapping("/login")
    public ResponseEntity<ApiResponse<TokenResponse>> login(@Valid @RequestBody LoginRequest request,
                                                           HttpServletRequest httpRequest) {
        // 보완 6: 접속 IP 는 구글 reCAPTCHA 확인에 참고값으로 보낸다 (X-Forwarded-For 는 위조할 수 있어 쓰지 않는다)
        return withTokens(authService.login(request, httpRequest.getRemoteAddr()));
    }

    // POST /api/v1/auth/refresh — access token 재발급. 브라우저가 refresh token 쿠키를 자동으로 실어 보낸다
    // 실패하면 401 REFRESH_INVALID 와 함께 쓸모없어진 쿠키도 지운다
    // 호출: ① App.jsx 앱 시작 시(로그인 복원) ② client.js 토큰 만료(TOKEN_EXPIRED) 시 → 둘 다 tokenRefresh.refreshAccessToken
    @PostMapping("/refresh")
    public ResponseEntity<?> refresh(
            @CookieValue(name = REFRESH_COOKIE, required = false) String refreshToken) {
        try {
            return withTokens(authService.refresh(refreshToken));
        } catch (ApiException e) {
            // 실패해도 쿠키를 지우지 않는다 (보완 1 추가 · 10-20)
            // 탭 두 개가 동시에 재발급하면 늦은 탭은 "이미 바뀐 토큰" 으로 실패하는데, 이때 쿠키를 지우면
            // 먼저 성공한 탭이 막 받은 새 쿠키까지 지워져 로그인이 풀린다. 쓸모없는 쿠키는 다음 로그인 · 로그아웃 때 바뀐다
            return ResponseEntity.status(e.getStatus())
                    .body(ApiResponse.fail(e.getCode(), e.getMessage()));
        }
    }

    // POST /api/v1/auth/logout — DB 의 refresh token 을 지우고 쿠키도 지운다. 이미 로그아웃 상태여도 200
    // 호출: Header.jsx [로그아웃] 버튼(handleLogout) → authApi.logout
    @PostMapping("/logout")
    public ResponseEntity<ApiResponse<Void>> logout(
            @CookieValue(name = REFRESH_COOKIE, required = false) String refreshToken) {
        authService.logout(refreshToken);
        return ResponseEntity.ok()
                .header(HttpHeaders.SET_COOKIE, deleteCookie().toString())
                .body(ApiResponse.ok(null));
    }

    // 로그인 · 재발급 공통 응답: Set-Cookie 헤더(refresh token) + 본문(access token, 회원 정보)
    private ResponseEntity<ApiResponse<TokenResponse>> withTokens(AuthTokens tokens) {
        ResponseCookie cookie = refreshCookie(tokens.getRefreshToken(), jwtProvider.getRefreshTokenValidity());
        return ResponseEntity.ok()
                .header(HttpHeaders.SET_COOKIE, cookie.toString())
                .body(ApiResponse.ok(new TokenResponse(tokens.getAccessToken(), tokens.getMember())));
    }

    private ResponseCookie refreshCookie(String value, Duration maxAge) {
        return ResponseCookie.from(REFRESH_COOKIE, value)
                .httpOnly(true)            // JavaScript 에서 읽을 수 없다 → XSS 로 훔쳐 갈 수 없다
                .secure(cookieSecure)      // true 면 https 에서만 전송
                .sameSite("Strict")        // 다른 사이트에서 시작된 요청에는 실리지 않는다
                .path("/api/v1/auth")      // 재발급 · 로그아웃 요청에만 실린다 (다른 API 에는 안 실림)
                .maxAge(maxAge)            // 이 기간 동안 브라우저를 껐다 켜도 남아 있다
                .build();
    }

    // 유효 시간 0 인 같은 이름 · 경로의 쿠키 = 브라우저에서 삭제
    private ResponseCookie deleteCookie() {
        return refreshCookie("", Duration.ZERO);
    }
}
