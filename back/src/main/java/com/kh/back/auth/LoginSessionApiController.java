package com.kh.back.auth;

import com.kh.back.common.dto.ApiResponse;
import java.util.List;
import lombok.RequiredArgsConstructor;
import org.springframework.security.core.annotation.AuthenticationPrincipal;
import org.springframework.web.bind.annotation.CookieValue;
import org.springframework.web.bind.annotation.DeleteMapping;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

/**
 * 6단계: 로그인된 기기 (개인정보 · 계정 관리 화면).
 * /api/v1/auth 아래에 둔 이유: refresh 쿠키가 Path=/api/v1/auth 라서, 여기서만 "지금 기기" 쿠키를 받을 수 있다.
 * 그래서 SecurityConfig 에서 /auth/** 공개 규칙보다 먼저 "로그인 필요" 로 지정했다.
 */
@RestController
@RequestMapping("/api/v1/auth/sessions")
@RequiredArgsConstructor
public class LoginSessionApiController {

    private static final String REFRESH_COOKIE = "refreshToken";

    private final LoginSessionService loginSessionService;

    // GET /api/v1/auth/sessions — 내 로그인된 기기 목록
    // 호출: ProfilePage.jsx 화면이 열릴 때 · MyPage.jsx 프로필 카드 "최근 로그인" → authApi.getSessions
    @GetMapping
    public ApiResponse<List<LoginSessionResponse>> list(@AuthenticationPrincipal Long userId,
            @CookieValue(name = REFRESH_COOKIE, required = false) String refreshToken) {
        return ApiResponse.ok(loginSessionService.list(userId, refreshToken));
    }

    // DELETE /api/v1/auth/sessions/{id} — 기기 하나 로그아웃 (남의 기기면 403)
    // 호출: ProfilePage.jsx 로그인된 기기 [로그아웃] → authApi.logoutSession
    @DeleteMapping("/{id}")
    public ApiResponse<Void> logout(@AuthenticationPrincipal Long userId, @PathVariable Long id,
            @CookieValue(name = REFRESH_COOKIE, required = false) String refreshToken) {
        loginSessionService.logout(userId, id, refreshToken);
        return ApiResponse.ok(null);
    }

    // POST /api/v1/auth/sessions/logout-others — 지금 기기만 남기고 모두 로그아웃. 응답: 로그아웃한 기기 수
    // 호출: ProfilePage.jsx [다른 기기 모두 로그아웃] → authApi.logoutOtherSessions
    @PostMapping("/logout-others")
    public ApiResponse<Integer> logoutOthers(@AuthenticationPrincipal Long userId,
            @CookieValue(name = REFRESH_COOKIE, required = false) String refreshToken) {
        return ApiResponse.ok(loginSessionService.logoutOthers(userId, refreshToken));
    }
}
