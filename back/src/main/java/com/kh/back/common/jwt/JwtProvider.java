package com.kh.back.common.jwt;

import com.kh.back.common.exception.ApiException;
import io.jsonwebtoken.Claims;
import io.jsonwebtoken.ExpiredJwtException;
import io.jsonwebtoken.JwtException;
import io.jsonwebtoken.Jwts;
import io.jsonwebtoken.security.Keys;
import java.nio.charset.StandardCharsets;
import java.time.Duration;
import java.util.Date;
import javax.crypto.SecretKey;
import lombok.Getter;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.http.HttpStatus;
import org.springframework.stereotype.Component;

/**
 * access token(JWT) 을 만들고 검증한다.
 * JWT = 헤더.내용.서명 세 부분을 점으로 이은 문자열. 서명 덕분에 내용이 바뀌면 검증에서 걸러진다.
 *
 * 내용(claims)에는 회원 번호(sub)와 역할(role: USER · ADMIN)만 담는다.
 * 내용은 누구나 읽을 수 있으므로 비밀번호 · 이메일 같은 정보는 넣지 않는다.
 */
@Component
public class JwtProvider {

    private static final String ROLE_CLAIM = "role";

    private final SecretKey key;
    private final Duration accessTokenValidity;
    @Getter
    private final Duration refreshTokenValidity; // refresh token 은 JWT 가 아니지만 유효 시간 설정을 여기서 함께 관리한다

    // application.yml 의 jwt.* 값을 생성자로 받는다 ("30m" 같은 글자가 Duration 으로 바뀐다)
    public JwtProvider(
            @Value("${jwt.secret}") String secret,
            @Value("${jwt.access-token-validity}") Duration accessTokenValidity,
            @Value("${jwt.refresh-token-validity}") Duration refreshTokenValidity) {
        this.key = Keys.hmacShaKeyFor(secret.getBytes(StandardCharsets.UTF_8)); // 32바이트 미만이면 서버 시작 시 오류
        this.accessTokenValidity = accessTokenValidity;
        this.refreshTokenValidity = refreshTokenValidity;
    }

    // 회원 번호와 역할을 담은 access token 을 만든다
    public String createAccessToken(Long userId, String role) {
        Date now = new Date();
        Date expiresAt = new Date(now.getTime() + accessTokenValidity.toMillis());
        return Jwts.builder()
                .subject(String.valueOf(userId)) // 토큰의 주인 (users.id)
                .claim(ROLE_CLAIM, role)         // 권한 (USER · ADMIN) → 관리자 화면 제한에 쓴다
                .issuedAt(now)                   // 발급 시각
                .expiration(expiresAt)           // 만료 시각
                .signWith(key)                   // 서버만 아는 키로 서명
                .compact();
    }

    // 토큰을 검증하고 회원 번호 · 역할을 꺼낸다. 실패하면 401 예외
    public TokenUser parse(String token) {
        try {
            Claims claims = Jwts.parser()
                    .verifyWith(key)
                    .build()
                    .parseSignedClaims(token) // 서명 · 만료 시각을 여기서 검사한다
                    .getPayload();
            return new TokenUser(Long.valueOf(claims.getSubject()), claims.get(ROLE_CLAIM, String.class));
        } catch (ExpiredJwtException e) {
            // 만료 → 프론트가 다시 로그인(또는 재발급)하도록 알린다
            throw new ApiException(HttpStatus.UNAUTHORIZED, "TOKEN_EXPIRED", "로그인 시간이 만료되었습니다.");
        } catch (JwtException | IllegalArgumentException e) {
            // 서명이 틀리거나 형식이 깨짐 → 위조되었거나 잘못된 토큰
            throw new ApiException(HttpStatus.UNAUTHORIZED, "TOKEN_INVALID", "유효하지 않은 토큰입니다.");
        }
    }

    /** 토큰에서 꺼낸 로그인 회원 정보 */
    public record TokenUser(Long userId, String role) {
    }
}
