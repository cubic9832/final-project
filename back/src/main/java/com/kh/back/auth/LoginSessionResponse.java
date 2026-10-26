package com.kh.back.auth;

import java.time.LocalDateTime;

/**
 * 6단계: 로그인된 기기 1개 (refresh token 1행).
 * refresh token 값 자체는 절대 내려보내지 않는다 — 화면에는 번호(id)로만 구분한다.
 *
 * @param id         기기 번호 (기기별 로그아웃에 사용)
 * @param device     브라우저 · 운영체제 (모르면 null → 화면에서 "알 수 없는 기기")
 * @param loggedInAt 처음 로그인한 시각
 * @param lastUsedAt 마지막으로 로그인을 이어 간 시각 (재발급할 때마다 바뀜)
 * @param current    지금 이 브라우저인지
 */
public record LoginSessionResponse(Long id, String device, LocalDateTime loggedInAt,
                                   LocalDateTime lastUsedAt, boolean current) {

    static LoginSessionResponse from(RefreshTokenDto token, String currentToken) {
        return new LoginSessionResponse(token.getId(), token.getDevice(), token.getLoggedInAt(),
                token.getCreatedAt(), token.getToken().equals(currentToken));
    }
}
