package com.kh.back.common.security;

import com.kh.back.common.jwt.JwtProvider;
import lombok.RequiredArgsConstructor;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.http.HttpMethod;
import org.springframework.security.config.annotation.web.builders.HttpSecurity;
import org.springframework.security.config.http.SessionCreationPolicy;
import org.springframework.security.crypto.bcrypt.BCryptPasswordEncoder;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.security.web.SecurityFilterChain;
import org.springframework.security.web.authentication.UsernamePasswordAuthenticationFilter;

/**
 * Spring Security 설정.
 * Security 는 의존성을 넣는 순간 "모든 주소를 잠그고, 로그인 폼 · 세션을 쓰는" 기본 동작을 한다.
 * 여기서 그 기본값을 끄고 "JWT 로 검사, 정해 둔 주소만 공개"로 바꾼다.
 */
@Configuration
@RequiredArgsConstructor
public class SecurityConfig {

    private final JwtProvider jwtProvider;
    private final JwtAuthenticationEntryPoint authenticationEntryPoint;

    @Bean
    public SecurityFilterChain securityFilterChain(HttpSecurity http) throws Exception {
        http
                // ① 쓰지 않는 기본 기능 끄기
                .csrf(csrf -> csrf.disable())             // 세션 · 쿠키 로그인을 노리는 공격 방어. 토큰을 헤더로 보내므로 끈다
                .formLogin(form -> form.disable())        // Security 가 만들어 주는 로그인 페이지
                .httpBasic(basic -> basic.disable())      // 브라우저 팝업 로그인
                .logout(logout -> logout.disable())       // Security 기본 /logout. 우리는 /api/v1/auth/logout 을 쓴다

                // ② 세션을 만들지 않는다 → 요청마다 토큰으로만 판단 (STATELESS)
                .sessionManagement(session -> session.sessionCreationPolicy(SessionCreationPolicy.STATELESS))

                // ③ 주소별 접근 규칙 — 위에서부터 차례로 검사한다
                .authorizeHttpRequests(auth -> auth
                        .requestMatchers("/api/v1/auth/**").permitAll()                    // 회원가입 · 로그인
                        .requestMatchers(HttpMethod.GET, "/api/v1/vehicles/**").permitAll() // 차량 조회는 누구나 (비회원 차량 찾기)
                        .requestMatchers(HttpMethod.GET, "/api/v1/companies/**").permitAll() // 종목 조회 예제
                        .anyRequest().authenticated())                                     // 나머지는 로그인 필요

                // ④ 인증이 필요한데 없을 때의 응답 → 401 실패 봉투
                .exceptionHandling(ex -> ex.authenticationEntryPoint(authenticationEntryPoint))

                // ⑤ 우리 토큰 필터를 Security 필터 체인에 끼워 넣는다
                .addFilterBefore(new JwtAuthenticationFilter(jwtProvider), UsernamePasswordAuthenticationFilter.class);

        return http.build();
    }

    // 비밀번호를 BCrypt 로 암호화하는 객체 → 회원가입 · 로그인 Service 에서 주입받아 쓴다
    @Bean
    public PasswordEncoder passwordEncoder() {
        return new BCryptPasswordEncoder();
    }
}
