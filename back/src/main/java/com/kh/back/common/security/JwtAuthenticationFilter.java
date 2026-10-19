package com.kh.back.common.security;

import com.kh.back.common.exception.ApiException;
import com.kh.back.common.jwt.JwtProvider;
import com.kh.back.common.jwt.JwtProvider.TokenUser;
import jakarta.servlet.FilterChain;
import jakarta.servlet.ServletException;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;
import java.io.IOException;
import java.util.List;
import lombok.RequiredArgsConstructor;
import org.springframework.security.authentication.UsernamePasswordAuthenticationToken;
import org.springframework.security.core.authority.SimpleGrantedAuthority;
import org.springframework.security.core.context.SecurityContextHolder;
import org.springframework.web.filter.OncePerRequestFilter;

/**
 * 모든 요청 앞에서 access token 을 꺼내 검증하는 필터.
 * 토큰이 맞으면 "이 요청은 N번 회원(역할)"이라는 인증 정보를 SecurityContext 에 넣는다.
 *
 * 이 필터는 막지 않는다. 막을지 말지는 SecurityConfig 의 접근 규칙이 정한다.
 * (로그인이 필요 없는 주소에 만료된 토큰이 실려 와도 그대로 통과해야 하기 때문)
 *
 * @Component 를 붙이지 않는다 → 붙이면 Spring Boot 가 일반 서블릿 필터로도 한 번 더 등록한다.
 * SecurityConfig 에서 new 로 만들어 Security 필터 체인에만 넣는다.
 */
@RequiredArgsConstructor
public class JwtAuthenticationFilter extends OncePerRequestFilter {

    // 토큰 검증에 실패한 이유를 EntryPoint 에 전달할 때 쓰는 이름
    public static final String AUTH_ERROR = "authError";

    private final JwtProvider jwtProvider;

    @Override
    protected void doFilterInternal(HttpServletRequest request, HttpServletResponse response, FilterChain chain)
            throws ServletException, IOException {

        // 요청 헤더 예: Authorization: Bearer eyJhbGciOi...
        String header = request.getHeader("Authorization");

        if (header != null && header.startsWith("Bearer ")) {
            try {
                TokenUser user = jwtProvider.parse(header.substring("Bearer ".length()));

                // 인증 정보 = (누구인지, 비밀번호, 권한 목록)
                // principal 자리에 회원 번호를 넣는다 → Controller 에서 @AuthenticationPrincipal Long userId 로 꺼낸다
                // 권한은 "ROLE_USER" · "ROLE_ADMIN" 형태로 넣어야 hasRole("ADMIN") 규칙이 알아본다
                UsernamePasswordAuthenticationToken authentication = new UsernamePasswordAuthenticationToken(
                        user.userId(), null, List.of(new SimpleGrantedAuthority("ROLE_" + user.role())));
                SecurityContextHolder.getContext().setAuthentication(authentication);

            } catch (ApiException e) {
                // 필터에서 던진 예외는 GlobalExceptionHandler 가 받지 못한다 (Controller 보다 앞이라서).
                // 이유(TOKEN_EXPIRED 등)만 적어 두고, 응답은 JwtAuthenticationEntryPoint 가 만든다
                request.setAttribute(AUTH_ERROR, e);
            }
        }

        chain.doFilter(request, response); // 다음 필터로 넘긴다
    }
}
