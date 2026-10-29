package com.kh.back.common.security;

import com.kh.back.common.dto.ApiResponse;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;
import java.io.IOException;
import lombok.RequiredArgsConstructor;
import org.springframework.http.HttpStatus;
import org.springframework.http.MediaType;
import org.springframework.security.access.AccessDeniedException;
import org.springframework.security.core.Authentication;
import org.springframework.security.core.context.SecurityContextHolder;
import org.springframework.security.web.access.AccessDeniedHandler;
import org.springframework.stereotype.Component;
import tools.jackson.databind.ObjectMapper;

/**
 * 로그인은 했지만 권한이 없는 주소에 들어왔을 때 Spring Security 가 부르는 곳 → 403 실패 봉투.
 * 보완 11: 관리자 API(/api/v1/admin/**)는 관리자가 아닌 회원에게 403 대신 "없는 주소"와 똑같은 404 를 준다
 *          → 일반 회원은 관리자 기능이 있는지조차 알 수 없다 (비회원은 없는 주소도 원래 401 이라 그대로 둔다)
 */
@Component
@RequiredArgsConstructor
public class JwtAccessDeniedHandler implements AccessDeniedHandler {
    private final ObjectMapper objectMapper;

    @Override
    public void handle(HttpServletRequest request, HttpServletResponse response,
                       AccessDeniedException exception) throws IOException {
        response.setContentType(MediaType.APPLICATION_JSON_VALUE);
        response.setCharacterEncoding("UTF-8");
        if (request.getRequestURI().startsWith("/api/v1/admin/") && !isAdmin()) {
            // GlobalExceptionHandler 의 "없는 주소" 응답과 같은 모양
            response.setStatus(HttpStatus.NOT_FOUND.value());
            objectMapper.writeValue(response.getWriter(), ApiResponse.fail("NOT_FOUND", "요청한 주소가 없습니다."));
            return;
        }
        response.setStatus(HttpStatus.FORBIDDEN.value());
        objectMapper.writeValue(response.getWriter(), ApiResponse.fail("ACCESS_DENIED", "접근 권한이 없습니다."));
    }

    // 관리자 · 총관리자 (JwtAuthenticationFilter 가 DB 의 지금 권한으로 ROLE_… 을 넣어 둔다)
    private static boolean isAdmin() {
        Authentication auth = SecurityContextHolder.getContext().getAuthentication();
        return auth != null && auth.getAuthorities().stream()
                .anyMatch(a -> a.getAuthority().equals("ROLE_ADMIN") || a.getAuthority().equals("ROLE_SUPER_ADMIN"));
    }
}
