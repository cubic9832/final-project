package com.kh.back.common.security;

import com.kh.back.common.dto.ApiResponse;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;
import java.io.IOException;
import lombok.RequiredArgsConstructor;
import org.springframework.http.HttpStatus;
import org.springframework.http.MediaType;
import org.springframework.security.access.AccessDeniedException;
import org.springframework.security.web.access.AccessDeniedHandler;
import org.springframework.stereotype.Component;
import tools.jackson.databind.ObjectMapper;

@Component
@RequiredArgsConstructor
public class JwtAccessDeniedHandler implements AccessDeniedHandler {
    private final ObjectMapper objectMapper;

    @Override
    public void handle(HttpServletRequest request, HttpServletResponse response,
                       AccessDeniedException exception) throws IOException {
        response.setStatus(HttpStatus.FORBIDDEN.value());
        if(request.getRequestURI().startsWith("/api/v1/admin/")){
            var problem=org.springframework.http.ProblemDetail.forStatusAndDetail(HttpStatus.FORBIDDEN,"관리자 권한이 필요합니다.");
            problem.setProperty("error", ApiResponse.fail("ACCESS_DENIED", "접근 권한이 없습니다.").getError());
            response.setContentType(MediaType.APPLICATION_PROBLEM_JSON_VALUE);response.setCharacterEncoding("UTF-8");
            objectMapper.writeValue(response.getWriter(),problem);return;
        }
        response.setContentType(MediaType.APPLICATION_JSON_VALUE);
        response.setCharacterEncoding("UTF-8");
        objectMapper.writeValue(response.getWriter(), ApiResponse.fail("ACCESS_DENIED", "접근 권한이 없습니다."));
    }
}
