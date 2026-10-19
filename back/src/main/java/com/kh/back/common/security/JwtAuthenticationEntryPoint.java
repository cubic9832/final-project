package com.kh.back.common.security;

import com.kh.back.common.dto.ApiResponse;
import com.kh.back.common.exception.ApiException;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;
import java.io.IOException;
import lombok.RequiredArgsConstructor;
import org.springframework.http.HttpStatus;
import org.springframework.http.MediaType;
import org.springframework.security.core.AuthenticationException;
import org.springframework.security.web.AuthenticationEntryPoint;
import org.springframework.stereotype.Component;
import tools.jackson.databind.ObjectMapper;

/**
 * 로그인이 필요한 주소에 인증 없이 들어왔을 때 Spring Security 가 부르는 곳.
 * GlobalExceptionHandler 대신 여기서 401 실패 봉투(ApiResponse)를 직접 만들어 응답한다.
 */
@Component
@RequiredArgsConstructor
public class JwtAuthenticationEntryPoint implements AuthenticationEntryPoint {

    private final ObjectMapper objectMapper; // 객체 → JSON 변환기 (Controller 가 응답할 때 쓰는 것과 같다)

    @Override
    public void commence(HttpServletRequest request, HttpServletResponse response,
                         AuthenticationException authException) throws IOException {

        // JwtAuthenticationFilter 가 남긴 실패 이유. 없으면 토큰 자체를 안 보낸 것
        ApiException error = (ApiException) request.getAttribute(JwtAuthenticationFilter.AUTH_ERROR);
        ApiResponse<Void> body = (error != null)
                ? ApiResponse.fail(error.getCode(), error.getMessage())         // TOKEN_EXPIRED · TOKEN_INVALID
                : ApiResponse.fail("AUTH_REQUIRED", "로그인이 필요합니다.");

        response.setStatus(HttpStatus.UNAUTHORIZED.value());
        response.setContentType(MediaType.APPLICATION_JSON_VALUE);
        response.setCharacterEncoding("UTF-8");
        objectMapper.writeValue(response.getWriter(), body);
    }
}
